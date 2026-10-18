#!/usr/bin/env python3
"""音声の読み間違いを、機械で確認する

使い方:
  python3 ツール/check_voice.py script.json

作った音声を文字起こしして、台本と突き合わせます。
**耳で聞く代わりではありません。**通しで聞く前の、一次スクリーニングです。

なぜ必要か:
  読み間違いは、数字・固有名詞・専門用語で起きます。
  10分の動画を毎回すべて集中して聞くのは大変なので、
  「怪しい行」を先に機械で絞り込みます。

必要なもの:
  .env に OPENAI_API_KEY=（キー）
  ※ 文字起こしに使います。1本あたり数円です。
"""
import json, sys, pathlib, uuid, urllib.request, re
import urllib.error
from _api_error import die


def _open(req, timeout=60):
    """通信して、失敗したら日本語で説明して止める"""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except Exception as e:
        die(e, "読み間違いを確認するとき")


def load_key(name):
    for f in (pathlib.Path(".env"), pathlib.Path("../.env")):
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith(name + "="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and not v.startswith("ここに"):
                        return v
    # ★キーが無くても、動画は作れます。ここは任意の工程です。
    print("この確認は、OpenAIのキーがある場合だけ動きます。")
    print("  .env に OPENAI_API_KEY=（キー）を書くと使えます（1本あたり10円ほど）。")
    print()
    print("キーを入れない場合は、この工程を飛ばして構いません。")
    print("★そのかわり、音声は必ずご自身で通しで聞いてください（第14章 14-6）。")
    sys.exit(0)


def transcribe(path, key):
    b = pathlib.Path(path).read_bytes()
    bd = "----" + uuid.uuid4().hex
    parts = []
    for n, v in (("model", "whisper-1"), ("response_format", "json"), ("language", "ja")):
        parts.append(f"--{bd}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    parts.append((f"--{bd}\r\nContent-Disposition: form-data; name=\"file\"; "
                  f"filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode() + b + b"\r\n")
    parts.append(f"--{bd}--\r\n".encode())
    req = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions",
                                 data=b"".join(parts),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": f"multipart/form-data; boundary={bd}"})
    return json.load(_open(req, timeout=180)).get("text", "")


def norm(s):
    """比較用に整える（記号・空白を落とす）"""
    return re.sub(r"[、。,.\s　「」『』（）()！？!?・]", "", s)


# ── 数字の読み合わせ ────────────────────────────────
#  台本「三千万円」と、聞こえた「3000万円」は同じものです。
#  表記が違うだけで別物と判定しないよう、数として比べます。
_D = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9}
_S = {"十": 10, "百": 100, "千": 1000}
_B = {"万": 10**4, "億": 10**8, "兆": 10**12}
_NUM = "0-9０-９〇零一二三四五六七八九十百千万億兆"


def to_int(s):
    """「三千万」も「3000万」も 30000000 にそろえる"""
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    total = section = num = 0
    digits = ""
    for ch in s:
        if ch.isdigit():
            digits += ch
            continue
        if digits:
            num, digits = int(digits), ""
        if ch in _D:
            num = _D[ch]
        elif ch in _S:
            section += (num or 1) * _S[ch]
            num = 0
        elif ch in _B:
            total += (section + num) * _B[ch]
            section = num = 0
    if digits:
        num = int(digits)
    return total + section + num


def numbers(text):
    """文中の数の表現を、すべて数値にして返す"""
    text = text.replace(",", "").replace("，", "")   # 「3,000万」で桁が割れないように
    # ★助数詞が付いた一桁は、数の指定ではなく言い回しなので数えません
    #   （「もう一つ」「一人で」「一度だけ」→ 文字起こしが「ひとつ」と書くと誤検知になる）
    text = re.sub(r"[一二三四五六七八九][つ人度回本つ度言瞬]", "", text)
    vals = set()
    for m in re.findall(f"[{_NUM}]+", text):
        v = to_int(m)
        if v:
            vals.add(v)
    return vals


def words(text):
    """読み間違いやすい語（カタカナ・漢字の連なり）を抜き出す。
       数の部分は numbers() が別に見るので、ここでは取り除く。"""
    out = []
    for w in re.findall(r"[ァ-ヴー]{3,}|[一-龥]{2,}", text):
        for part in re.split(f"[{_NUM}]+", w):    # 「二十四時間」→「時間」
            if len(part) >= 2:
                out.append(part)
    return out


def main(path):
    key = load_key("OPENAI_API_KEY")
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    voice = pathlib.Path("出力/voice")
    if not voice.exists():
        sys.exit("出力/voice がありません。先に make_voice.py を実行してください。")

    print("音声を文字起こしして、台本と突き合わせます\n")
    ng = []
    for si, sc in enumerate(data["scenes"], 1):
        for li, line in enumerate(sc["lines"], 1):
            f = voice / f"s{si:02d}_l{li:02d}.mp3"
            if not f.exists():
                continue
            spoken = line.get("read") or line["text"]
            heard = transcribe(f, key)

            # ① 数字が合っているか（表記の違いは無視して、数として比べる）
            want, got = numbers(spoken), numbers(heard)
            bad_num = sorted(want - got)
            # ② 語が入れ替わっていないか
            bad_word = [w for w in words(spoken) if norm(w) not in norm(heard)]

            if bad_num or bad_word:
                ng.append((si, li, bool(bad_num)))
                mark = "⚠" if bad_num else "・"
                print(f"{mark} シーン{si} {li}行目")
                print(f"   台本 : {spoken}")
                print(f"   聞こえ: {heard.strip()}")
                if bad_num:
                    print(f"   ★数字が違います: {' / '.join(f'{v:,}' for v in bad_num)}")
                if bad_word:
                    print(f"   ・語の確認: {' / '.join(bad_word)}")
                print()

    if not ng:
        print("✓ 数字・語の読み間違いは見つかりませんでした。")
    else:
        n = sum(1 for x in ng if x[2])
        print(f"── ⚠ 数字の誤り {n}行 ／ ・語の確認 {len(ng)-n}行 ──")
        print("※「・」は、文字起こし側の表記ゆれのことがあります。聞いて判断してください。")
        print("※ 文字起こしは毎回わずかに揺れます。**同じ音声でも、実行のたびに")
        print("   出たり出なかったりします。**出たものだけを聞いて確かめてください。")
        print("直し方（第14章）:")
        print("  誤読（別の言葉として読まれた）→ script.json のその行に read を足す")
        print("  抑揚が変（読みは合っている） → read の表記を言い換える")
        print("  直したら make_voice.py を実行するだけです（mp3を消す必要はありません）")

    print("\n★これは一次スクリーニングです。")
    print("  必ず、最初から最後まで通しで聞いてください（第14章 14-6）。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "script.json")
