#!/usr/bin/env python3
"""script.json → 音声ファイル（1行につき1つ）＋ 長さの計測

使い方:
  python3 ツール/make_voice.py script.json

出力:
  出力/voice/s01_l01.mp3 …   （1行 = 1ファイル）
  出力/durations.json         （各行の秒数。組み立てで使います）

※ 音声には「read」があればそれを、なければ「text」を使います（第14章）。
※ ElevenLabs の API キーを .env に置いてください：
     ELEVENLABS_API_KEY=（キー）
"""
import json, sys, pathlib, subprocess, urllib.request, time, hashlib, re
import urllib.error
from _api_error import die


def _open(req, timeout=60):
    """通信して、失敗したら日本語で説明して止める"""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        die(e, "音声を作るとき")
    except Exception as e:
        die(e, "音声を作るとき")

ROOT = pathlib.Path(".")
# ★モデルと言語の指定は、絶対に省略しないでください
#   古いモデル（multilingual_v2）や言語指定なしだと、漢字を中国語と誤判定します
#   「十四日」→「しいしにち」、「円」→「元（ユアン）」のように読まれます
MODEL = "eleven_v3"          # 第3章でご紹介している最新モデル
LANG = "ja"                  # ★日本語に固定する
FORMAT = "mp3_44100_128"


def load_key():
    for name in (".env", "../.env"):
        f = ROOT / name
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ELEVENLABS_API_KEY が見つかりません。.env に書いてください。")


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)],
                       capture_output=True, text=True, check=True)
    return round(float(r.stdout.strip()), 3)


def tts(text, voice, key, dest):
    body = json.dumps({"text": text, "model_id": MODEL, "language_code": LANG,
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                                          "speed": 1.0}}).encode()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format={FORMAT}"
    req = urllib.request.Request(url, data=body,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    dest.write_bytes(_open(req, timeout=120).read())


def quota(key):
    """いま使える文字数と、残りで何本作れるかを調べる（第3章・第18章）"""
    try:
        req = urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription",
                                     headers={"xi-api-key": key})
        d = json.load(_open(req, timeout=30))
        return d.get("tier", "?"), d.get("character_limit", 0), d.get("character_count", 0)
    except Exception:
        return None, 0, 0


def main(path):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    key = load_key()
    voice = data.get("voice_id")
    if not voice:
        sys.exit("script.json に voice_id がありません。")
    if not re.fullmatch(r"[A-Za-z0-9]{16,}", voice or ""):
        sys.exit("\n  voice_id がまだ設定されていません。\n"
                 f"  いまの値：{voice}\n\n"
                 "  『/00_声を選ぶ』で声を決めて、script.json の voice_id に\n"
                 "  英数字のID（例：gARvXPexe5VF3cKZBian）を書いてください。\n")

    out = pathlib.Path("出力/voice"); out.mkdir(parents=True, exist_ok=True)
    durations, total_chars = [], 0

    # 前回の読み上げ文の署名（台本が変わっていないかの照合に使います）
    prev_sig = {}
    dj = pathlib.Path("出力/durations.json")
    if dj.exists():
        try:
            prev_sig = {x["file"]: x.get("sig") for x in json.loads(dj.read_text())}
        except Exception:
            pass

    for si, sc in enumerate(data["scenes"], 1):
        for li, line in enumerate(sc["lines"], 1):
            spoken = line.get("read") or line["text"]          # ★音声は読み用
            f = out / f"s{si:02d}_l{li:02d}.mp3"
            # ★読み上げ文が変わっていたら、作り直します
            #   （台本を直してmp3を消し忘れると、古い音声が黙って使われるため）
            sig = hashlib.sha256(f"{voice}|{spoken}".encode()).hexdigest()[:16]
            if f.exists() and prev_sig.get(f.name) not in (None, sig):
                print(f"  {f.name}  台本が変わっているので作り直します")
                f.unlink()
            if f.exists():                                     # 作り直しを避ける
                d = duration(f)
            else:
                t0 = time.time()
                tts(spoken, voice, key, f)
                d = duration(f)
                print(f"  {f.name}  {len(spoken)}字 → {d:.2f}秒  ({time.time()-t0:.1f}s)")
            durations.append({"scene": si, "line": li, "file": f.name,
                              "sec": d, "subtitle": line["text"], "sig": sig})  # ★字幕は表示用
            total_chars += len(spoken)

    pathlib.Path("出力/durations.json").write_text(
        json.dumps(durations, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(x["sec"] for x in durations)
    # ★動画では、行と行のあいだに「間」が入ります（build_video.py が入れます）。
    #   その分を足さないと、台本の目安字数が1〜2割ぶん多く出てしまいます。
    GAPS = {"。": 0.40, "、": 0.25, "・": 0.25, "！": 0.45, "？": 0.40}
    gap_total = 0.0
    for i, x in enumerate(durations):
        last_of_scene = (i + 1 == len(durations)
                         or durations[i + 1]["scene"] != x["scene"])
        gap_total += 0.70 if last_of_scene else GAPS.get(x["subtitle"][-1:], 0.30)

    total_with_gap = total + gap_total
    rate_raw = total_chars / total * 60 if total else 0            # 声だけの速さ
    rate = total_chars / total_with_gap * 60 if total_with_gap else 0   # 間を含めた速さ

    print(f"\n完了: {len(durations)}行 / {total_chars:,}字 / {total:.1f}秒（{total/60:.1f}分）")
    print("      出力/durations.json に長さを保存しました")
    print(f"\n  声だけの長さ　　　：{total:.1f}秒（{rate_raw:.0f}字/分）")
    print(f"  ＋行のあいだの間　：{gap_total:.1f}秒")
    print(f"  ＝動画になる長さ　：{total_with_gap:.1f}秒（{total_with_gap/60:.1f}分）")
    print(f"\n★この声の読み上げ速度：{rate:.0f}字/分  ★間を含めた値です")
    print("  この声で作るなら、台本の長さの目安はこうです：")
    for m in (5, 8, 10, 12, 15):
        mark = ("　★8分未満は広告が前後にしか入りません" if m == 5 else
                "　←ここを超えると途中にも広告が入ります" if m == 8 else
                "　←おすすめ" if m in (10, 12) else "")
        print(f"    {m:2d}分 → 約 {int(rate*m):,}字 ／ シーン {int(m*60/40):2d}枚{mark}")
    print("  ※ 上の字数は、動画にしたときの分数です（間を含めて計算しています）。")
    print("    速度は声によって大きく変わります。ご自身の声のこの数字をお使いください。")

    tier, limit, used = quota(key)
    if tier:
        left = max(0, limit - used)
        print(f"\n★ElevenLabsの残り：{left:,}字 / {limit:,}字（{tier}プラン）")
        if total_chars:
            print(f"  → この動画と同じ長さなら、あと約 {left // total_chars} 本つくれます")
        if left < total_chars * 3:
            print("  ⚠ 残りが少なくなっています。プランの見直しをご検討ください（第18章）")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "script.json")
