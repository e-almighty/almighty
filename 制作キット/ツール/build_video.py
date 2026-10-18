#!/usr/bin/env python3
"""スライド＋音声（＋BGM） → 1本の動画（mp4）

使い方:
  python3 ツール/build_video.py script.json

前提: 先に make_slides.py と make_voice.py を実行しておくこと
出力: 出力/完成.mp4

考え方（第15章）:
  音声の長さを測る → その長さだけスライドを出す → 同じタイミングで字幕を出す
  画を音声に合わせます。逆ではありません。

BGMについて（第19章）:
  bgm/ フォルダに曲を入れておくと、自動で使います。
  script.json の各シーンに "section" を書いておくと、その区切りで曲が変わります。
  bgm/ が無ければBGMなしで作ります（BGMなしという選択も第19章のとおり有効です）。
"""
import json, sys, pathlib, subprocess, re, hashlib
from subtitle_split import split_caption, share_time

OUT = pathlib.Path("出力")
BGM_DIR = pathlib.Path("bgm")
FONT = "Hiragino Sans"      # Windowsは "Yu Gothic" や "Meiryo" に変えてください
# ── 字幕 ──────────────────────────────────
#   ★字幕は「帯」の中に置きます（第15章・第17章）
#     スライドは上の858px、下の222pxが字幕帯。こうすると
#     **スライドの絵と字幕が絶対に重なりません。**
#     背景が明るくても暗くても関係なくなるので、文字色は白で固定できます。
BAND_H = 222                # 帯の高さ
#   ★実測して決めました：2行だと文字の高さが140px。上下に41pxずつ余白を取って222px。
BAND_COLOR = "black"        # 帯の色（チャンネルに合わせて変えて構いません）
SLIDE_H = 1080 - BAND_H     # スライドの高さ = 858

SUB_SIZE = 83               # 字幕の大きさ
#   ★この数字は「実測で」決めています。
#     字幕の指定値は、フォントの上下の余白を含むため、**見た目の文字より大きい数字**になります。
#     このフォント（Hiragino Sans）では、実測で約1.53倍でした。
#       指定83 → 実際の文字の高さ54px = 画面の高さの5.0%（第17章の基準どおり）
#     ★フォントを変えたら、この比率も変わります。必ずご自身で測り直してください。
#       測り方：1文字だけ表示した画像を書き出して、文字の高さをピクセルで数えます。
SUB_FILL = "&H00FFFFFF"     # 文字：白で固定（帯の中なので変える必要がありません）
SUB_LINE = "&H00000000"     # 縁取り：黒
SUB_OUTLINE = 4             # 縁取りの太さ
TAIL = 0.8                  # 最後のスライドを、この秒数だけ残す（ぶつ切り防止）

# ── 行と行のあいだの「間（ま）」───────────────────
#   ★これを入れないと、文が終わった直後に次の文が始まって、早口に聞こえます。
#     人は句点でしっかり息をつぎ、読点では軽く止まります。それを再現します。
GAP_PERIOD = 0.40           # 「。」で終わる行のあと
GAP_COMMA  = 0.25           # 「、」「・」で終わる行のあと
GAP_EXCLAM = 0.45           # 「！」で終わる行のあと
GAP_QUEST  = 0.40           # 「？」で終わる行のあと
GAP_OTHER  = 0.30           # 句読点なし（体言止めなど）
GAP_SCENE  = 0.70           # シーンの最後の行のあと（画が切り替わるので、ひと呼吸）
GAP_JITTER = 0.12           # ±12％だけ揺らす（機械的に等間隔だと不自然なため）

# ── 音量の設定 ─────────────────────────────
#   動画ごとに音量がバラつかないよう、決まった大きさに揃えます。
#   これをやらないと、チャンネルに並べたとき「この回だけ小さい」が起きます。
LOUDNESS = -16.0            # 目標の音量（LUFS）。YouTubeの基準に近い値です
PEAK = -1.5                 # 音が割れないための上限（dBTP）

# ── BGMの設定（第19章 19-3／19-4 の数値）──────────────
BGM_VOL = 0.08              # ふだんの音量：全体の8％
BGM_DUCK = 0.03             # ナレーション中の目安（実測では約1〜2％まで下がります）
#   ★sidechaincompress の ratio に使う値です。3％ちょうどにはなりません。
#     もっと下げたくない場合は、下の ratio を 1.5 前後にしてください。
BGM_XFADE = 1.5             # 曲の切り替わりを、この秒数だけ重ねる


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def sec_of(p):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)])
    return float(r.stdout.strip())


def ts(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def line_gap(text, is_scene_last, seed):
    """その行のあとに、どれだけ無音を入れるかを決める"""
    if is_scene_last:
        g = GAP_SCENE
    else:
        last = (text or "").strip()[-1:] or ""
        g = (GAP_EXCLAM if last in "！!" else
             GAP_QUEST if last in "？?" else
             GAP_PERIOD if last in "。" else
             GAP_COMMA if last in "、・" else GAP_OTHER)
    # 同じ台本なら毎回同じ揺れになるように、番号から決めます
    u = int(hashlib.sha256(str(seed).encode()).hexdigest()[:8], 16) / 0x100000000
    return max(0.05, round(g * (1 + GAP_JITTER * (u * 2 - 1)), 3))


def pauses_in(path):
    """その音声の中で、実際に息をついだ時刻を拾う（字幕のめくりを音に合わせるため）"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path),
                        "-af", "silencedetect=noise=-32dB:d=0.16", "-f", "null", "-"],
                       capture_output=True, text=True)
    out = []
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start:\s*([\d.]+)", line)
        if m:
            out.append(float(m.group(1)))
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and out:
            # 無音の真ん中を「めくる場所」とみなす
            out[-1] = (out[-1] + float(m.group(1))) / 2
    return out


ASS_HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,{FONT},{SUB_SIZE},{SUB_FILL},{SUB_LINE},&H80000000,1,1,{SUB_OUTLINE},0,5,80,80,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def build_bgm(sections, total):
    """区切りごとに曲を割り当て、重ねてつなぐ（第19章 19-2／19-3）

    sections: [(区切りの名前, 秒数), …]
    戻り値  : 作ったBGMファイル（bgm/ が無ければ None）
    """
    if not BGM_DIR.is_dir():
        return None
    pool = sorted([p for p in BGM_DIR.iterdir()
                   if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac", ".flac")])
    if not pool:
        return None

    print(f"\nBGM: {len(pool)}曲から {len(sections)}区切りに割り当てます")
    if len(pool) < len(sections):
        print(f"  ※ 曲が足りないので、頭から繰り返して使います"
              f"（第19章では5〜8曲を用意することをおすすめしています）")

    # ① 区切りごとに、その長さぶんの音を作る（足りなければ曲を繰り返す）
    segs = []
    for i, (name, sec) in enumerate(sections):
        track = pool[i % len(pool)]
        seg = OUT / f"bgm_{i:02d}.wav"
        # ★BGMも同じ大きさに揃えてから、8％まで絞ります
        #   （曲ごとの録音レベルの差が、そのまま出てしまわないように）
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(track),
             "-t", f"{sec + BGM_XFADE:.3f}",
             "-af", f"loudnorm=I={LOUDNESS}:TP={PEAK}:LRA=11,volume={BGM_VOL}",
             "-ac", "2", "-ar", "44100", str(seg)])
        segs.append(seg)
        print(f"  {name}：{track.name}（{sec:.1f}秒）")

    # ② 1.5秒重ねながら1本につなぐ
    bgm = OUT / "bgm.wav"
    if len(segs) == 1:
        run(["ffmpeg", "-y", "-i", str(segs[0]), "-t", f"{total:.3f}", str(bgm)])
    else:
        cmd = ["ffmpeg", "-y"]
        for s in segs:
            cmd += ["-i", str(s)]
        fc, prev = [], "[0]"
        for i in range(1, len(segs)):
            tag = f"[x{i}]"
            fc.append(f"{prev}[{i}]acrossfade=d={BGM_XFADE}:c1=tri:c2=tri{tag}")
            prev = tag
        cmd += ["-filter_complex", ";".join(fc), "-map", prev,
                "-t", f"{total:.3f}", str(bgm)]
        run(cmd)

    # ③ 頭と終わりを、そっと出し入れする
    faded = OUT / "bgm_final.wav"
    run(["ffmpeg", "-y", "-i", str(bgm),
         "-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(0, total-2.0):.3f}:d=2.0",
         str(faded)])
    return faded


def main(path):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    durs = json.loads((OUT / "durations.json").read_text(encoding="utf-8"))

    # ① 音声を、ずれない形にそろえる
    #    ★mp3をそのままつなぐと、1ファイルごとに詰め物が入ってわずかに伸びます。
    #      それを積み上げると、終盤で字幕が音声とずれます（第15章のよくある失敗）。
    #      ここでいったん無圧縮に直してから測り、つなぎます。
    wav_dir = OUT / "wav"; wav_dir.mkdir(parents=True, exist_ok=True)
    exact = []
    for d in durs:
        w = wav_dir / (pathlib.Path(d["file"]).stem + ".wav")
        if not w.exists():
            run(["ffmpeg", "-y", "-i", str(OUT / "voice" / d["file"]),
                 "-ac", "2", "-ar", "44100", str(w)])
        exact.append({**d, "wav": w, "sec": sec_of(w)})

    # ★行のあとに「間」を足す（句点のあとはしっかり、読点のあとは軽く）
    last_of_scene = {}
    for i, x in enumerate(exact):
        last_of_scene[x["scene"]] = i
    for i, x in enumerate(exact):
        g = line_gap(x["subtitle"], i == last_of_scene[x["scene"]], i)
        padded = wav_dir / (x["wav"].stem + "_p.wav")
        if not padded.exists():
            run(["ffmpeg", "-y", "-i", str(x["wav"]),
                 "-af", f"apad=pad_dur={g}", str(padded)])
        x["raw"] = x["wav"]          # ★息つぎの検出は「間」を足す前の音声で行います
        x["wav"], x["gap"] = padded, g
        x["sec"] = sec_of(padded)

    drift = sum(x["sec"] for x in exact) - sum(d["sec"] for d in durs)
    if abs(drift) > 0.05:
        print(f"※ 音声の実測が見積もりと {drift:+.2f}秒 違いました。実測に合わせます。")

    # ② シーンごとの合計時間・字幕・区切りを、実測から作る
    scene_sec, events, t, cuts = {}, [], 0.0, 0
    for d in exact:
        scene_sec[d["scene"]] = scene_sec.get(d["scene"], 0) + d["sec"]
        # ★1文をそのまま出すのではなく、めくる単位に割る（第15章）
        spc = d["sec"] / max(1, len(d["subtitle"]))     # この行の1文字あたりの秒数
        parts = split_caption(d["subtitle"], sec_per_char=spc) or [d["subtitle"]]
        # ★末尾に足した「間」は息つぎではないので、検出から外します
        spoken = d["sec"] - d.get("gap", 0)
        ps = ([t + p for p in pauses_in(d["raw"]) if p < spoken - 0.15]
              if len(parts) > 1 else [])
        # 最後の1枚だけ、あとの「間」のあいだも出したままにします（点滅防止）
        times = share_time(parts, t, t + spoken, ps)
        times[-1] = (times[-1][0], t + d["sec"])
        for (a, b), text in zip(times, parts):
            # 帯のまんなかに置く（行数が1でも2でも中央にそろいます）
            events.append(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,"
                          f"{{\\an5\\pos(960,{SLIDE_H + BAND_H // 2})}}{text}")
            cuts += 1
        t += d["sec"]
    total = t

    # 区切り（第19章）：シーンの "section" が同じものをひとまとまりにする
    sections = []
    for i, sc in enumerate(data["scenes"], 1):
        name = sc.get("section") or "本編"
        if sections and sections[-1][0] == name:
            sections[-1][1] += scene_sec.get(i, 0)
        else:
            sections.append([name, scene_sec.get(i, 0)])
    sections = [(n, s) for n, s in sections if s > 0]

    # ③ スライドを、そのシーンの合計時間だけ並べる
    lines = []
    for i in range(1, len(data["scenes"]) + 1):
        png = OUT / "slides" / f"slide{i:02d}.png"
        if not png.exists():
            sys.exit(f"{png} がありません。先に make_slides.py を実行してください。")
        lines += [f"file 'slides/{png.name}'", f"duration {scene_sec.get(i,0):.3f}"]
    # ★最後の1枚は、再掲しないと表示時間が効きません（第15章のよくある失敗）
    lines += [f"file 'slides/slide{len(data['scenes']):02d}.png'", f"duration {TAIL:.3f}"]
    (OUT / "slides.txt").write_text("\n".join(lines), encoding="utf-8")

    # ④ 音声を1本につなぐ（無圧縮なので、ずれません）
    (OUT / "audio.txt").write_text(
        "\n".join(f"file 'wav/{x['wav'].name}'" for x in exact), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio.txt",
         "-c", "copy", "voice_raw.wav"], cwd=OUT)

    # ★音量を揃える（毎回同じ大きさにする）
    run(["ffmpeg", "-y", "-i", "voice_raw.wav",
         "-af", f"loudnorm=I={LOUDNESS}:TP={PEAK}:LRA=11",
         "-ar", "44100", "-ac", "2", "voice.wav"], cwd=OUT)

    # ⑤ BGMを作って、喋っている間だけ下げて混ぜる（第19章 19-4）
    bgm = build_bgm(sections, total + TAIL)
    if bgm:
        # sidechaincompress＝ナレーションが鳴っている間だけBGMを押し下げる仕組み
        ratio = max(1.5, BGM_VOL / BGM_DUCK)
        run(["ffmpeg", "-y", "-i", str(bgm), "-i", str(OUT / "voice.wav"),
             "-filter_complex",
             f"[1]apad=whole_dur={total + TAIL:.3f}[v];"
             f"[v]asplit=2[v1][key];"
             f"[0][key]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:"
             f"attack=20:release=400:makeup=1[duck];"
             f"[duck][v1]amix=inputs=2:normalize=0:duration=longest[out]",
             "-map", "[out]", str(OUT / "mixed.wav")])
        audio = OUT / "mixed.wav"
        print(f"  → ナレーション中は {BGM_VOL*100:.0f}％ から約1〜2％まで自動で下がります")
        print(f"     ★音量の確認は、翌日にスマートフォンのスピーカーで（第19章 19-4）")
    else:
        run(["ffmpeg", "-y", "-i", str(OUT / "voice.wav"),
             "-af", f"apad=whole_dur={total + TAIL:.3f}", str(OUT / "mixed.wav")])
        audio = OUT / "mixed.wav"

    # ⑥ 字幕
    (OUT / "sub.ass").write_text(ASS_HEAD + "\n".join(events) + "\n", encoding="utf-8")

    # ⑦ 合成
    run(["ffmpeg", "-y",
         "-f", "concat", "-safe", "0", "-i", "slides.txt", "-i", audio.name,
         # スライド(858px)の下に帯を足して1080pxにし、その上に字幕を焼く
         #   ★fps を subtitles より前に置くこと。
         #     スライドは1枚につき1フレームしかないので、先に毎秒30枚へ増やしてから
         #     字幕を焼かないと、**そのスライドの間ずっと同じ字幕**が焼き付きます
         #     （＝「字幕が進まない」の原因）。
         "-vf", f"pad=1920:1080:0:0:color={BAND_COLOR},"
                f"fps=30,subtitles=sub.ass,format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{total + TAIL:.3f}", "完成.mp4"], cwd=OUT)

    made = sec_of(OUT / "完成.mp4")
    print(f"  音量を {LOUDNESS:.0f} LUFS に揃えました（毎回同じ大きさになります）")
    print(f"  字幕は下部{BAND_H}pxの帯の中に白文字（スライドは上の{SLIDE_H}px）")
    print(f"\n完成: {OUT/'完成.mp4'}")
    print(f"  尺 {made:.1f}秒 ／ シーン {len(data['scenes'])}枚 ／ 字幕 {len(events)}カット"
          f"（ナレーション {len(exact)}文を分割）")
    gaps = [x["gap"] for x in exact]
    print(f"  行のあいだの間：{min(gaps):.2f}〜{max(gaps):.2f}秒"
          f"（合計 {sum(gaps):.1f}秒）")
    print(f"  ナレーション {total:.2f}秒 ＋ 余韻 {TAIL:.1f}秒 ＝ {total+TAIL:.2f}秒")
    if abs(made - (total + TAIL)) > 0.15:
        print(f"  ⚠ 尺が想定と {made-(total+TAIL):+.2f}秒 ずれています。確認してください。")
    else:
        print(f"  ✓ 音声と映像の長さが一致しています")
    if not bgm:
        print("  ※ BGMなしで作りました（bgm/ フォルダに曲を入れると自動で使います）")
    print(f"  ★必ず末尾まで再生して確認してください（第15章 15-9）")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "script.json")
