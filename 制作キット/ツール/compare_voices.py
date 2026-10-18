#!/usr/bin/env python3
"""声の候補を聞き比べる（第14章 14-1）

使い方:
  python3 ツール/compare_voices.py --おすすめ   # まずはこれ（推奨6声を比較）
  python3 ツール/compare_voices.py            # 共有ライブラリの日本語の声を一覧
  python3 ツール/compare_voices.py ID1 ID2 …  # 指定した声で比較

出力: 出力/声比較/1_（名前）.mp3 …

★声は、あとから変えると全編を作り直すことになります。
★必ず「1分以上」を「通しで」聞いて選んでください。5秒で決めないでください。
"""
import json, sys, pathlib, subprocess, urllib.request, time
import urllib.error
from _api_error import die


def _open(req, timeout=60):
    """通信して、失敗したら日本語で説明して止める"""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        die(e, "声を聞き比べるとき")
    except Exception as e:
        die(e, "声を聞き比べるとき")

# ── まず試すとよい候補（ElevenLabs共有ライブラリ・日本語）──────
#    引数なしで `--おすすめ` を付けると、この6つを一度に比較します
#    数字や専門語を正しく読めるか、実際に読ませて確かめた6声です（2026年10月）。
#    「速さ」は実測。**同じ台本でも、声によって尺が4割変わります。**
OSUSUME = [
    #  voice_id                名前      系統            速さ      読みの確認
    ("gARvXPexe5VF3cKZBian", "Mitsuki 女性・若・明るめ   229字/分  数字すべて正確"),
    ("JTlYtJrcTzPC71hMLOxo", "Yuki    女性・若          264字/分  ★十か月を誤読"),
    ("a0MsDWokG5Xsuji8g8er", "Haru    女性・穏やか       290字/分  数字すべて正確"),
    ("dhGvgIx0X6G3xzSWqOye", "Kana    女性・落ち着き     327字/分  数字すべて正確"),
    ("LjaWbdfZxis9YRrL8L87", "Ryu     男性・中年・落ち着き 280字/分  数字すべて正確"),
    ("KJje3wzepLiSIQjVGCB6", "Riku    男性・中年・深め   292字/分  数字すべて正確"),
]

# ── 比較に使う原稿（自分のチャンネルの台本に差し替えてください）──
SAMPLE = (
    "ここでひとつ、注意点があります。"
    "この申請には、期限があるんです。"
    "原則として、十四日以内。"
    "過ぎてしまうと、さかのぼって申請できない場合があります。"
    "郵送で出す方は、もう一つ気をつけてください。"
    "期限の判定は、消印ではなく到着日です。"
)


def load_key():
    for name in (".env", "../.env"):
        f = pathlib.Path(name)
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ELEVENLABS_API_KEY が見つかりません。.env に書いてください。")


def list_voices(key):
    """ElevenLabsの共有ライブラリから、日本語の声を一覧する。
       ここに出る声は、どのアカウントでも使えます。"""
    import urllib.parse
    q = urllib.parse.urlencode({"language": "ja", "page_size": "40", "sort": "trending"})
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/shared-voices?{q}",
                                 headers={"xi-api-key": key})
    vs = json.load(_open(req, timeout=30)).get("voices", [])
    print(f"共有ライブラリの日本語の声：{len(vs)}件（使われている数の多い順）\n")
    print(f"{'voice_id':24s} {'名前':26s} {'性別/年代':18s} {'使用数':>8s}")
    print("-" * 82)
    for v in vs:
        print(f"{v.get('voice_id') or '':24s}  {(v.get('name') or '')[:24]:26s} "
              f"{(v.get('gender') or '') + '/' + (v.get('age') or ''):18s} "
              f"{v.get('cloned_by_count') or 0:>8,}")
    print("\n比較するには：python3 ツール/compare_voices.py ID1 ID2 ID3")
    print("※ 使用数が多い声ほど、多くの人が実際に使っている声です")


def synth(text, vid, key, dest):
    body = json.dumps({"text": text, "model_id": "eleven_v3", "language_code": "ja",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                                          "speed": 1.0}}).encode()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=body,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    dest.write_bytes(_open(req, timeout=120).read())


def main(ids):
    key = load_key()
    if ids and ids[0] in ("--おすすめ", "--osusume"):
        ids = [v for v, _ in OSUSUME]
        print("おすすめ6声で比較します\n")
    if not ids:
        return list_voices(key)

    # 名前の対応表を作る（おすすめ → 共有ライブラリ → 自分のアカウント の順に探す）
    names = {v: n for v, n in OSUSUME}
    try:
        import urllib.parse
        q = urllib.parse.urlencode({"language": "ja", "page_size": "40", "sort": "trending"})
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/shared-voices?{q}",
                                     headers={"xi-api-key": key})
        for v in json.load(_open(req, timeout=30)).get("voices", []):
            names.setdefault(v.get("voice_id"), (v.get("name") or "").split(" - ")[0])
    except Exception:
        pass
    try:
        req = urllib.request.Request("https://api.elevenlabs.io/v2/voices?page_size=100",
                                     headers={"xi-api-key": key})
        for v in json.load(_open(req, timeout=30))["voices"]:
            names.setdefault(v["voice_id"], v.get("name", ""))
    except Exception:
        pass

    out = pathlib.Path("出力/声比較"); out.mkdir(parents=True, exist_ok=True)
    print(f"原稿 {len(SAMPLE)}字 を {len(ids)}声で読ませます\n")
    for i, vid in enumerate(ids, 1):
        # ★速さはファイル名に入れません（切れて「26」などになるため。画面に出します）
        nm = (names.get(vid, vid) or vid).split("　")[0].replace("/", "_")[:24]
        f = out / f"{i}_{nm}.mp3"
        try:
            synth(SAMPLE, vid, key, f)
            d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1", str(f)],
                               capture_output=True, text=True).stdout.strip()
            print(f"  ○ {f.name}  {float(d):.1f}秒")
        except Exception as e:
            print(f"  × {vid}  {str(e)[:60]}")
        time.sleep(0.3)

    print(f"\n→ {out} に出力しました\n")
    print("【選び方】")
    print("  0. ★まず「誰に向けたチャンネルか」を思い浮かべてください")
    print("     年配の方向けなら、落ち着いた中年の声のほうが届きます")
    print("  1. 全部を通しで聞く（途中で止めない）")
    print("  2. できればスマートフォンのスピーカーで聞く")
    print("  3. 5秒ではなく、最後まで聞いてから決める")
    print("  4. 決めたら、その voice_id を CLAUDE.md と script.json に書く")


if __name__ == "__main__":
    main(sys.argv[1:])
