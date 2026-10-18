#!/usr/bin/env python3
"""script.json → スライド画像（PNG）

使い方:
  python3 ツール/make_slides.py script.json

出力: 出力/slides/slide01.png 〜（1920×858）

※ 動画は 1920×1080 ですが、**下の222pxは字幕帯**です（第15章）。
   スライドはその上の 858px に作ります。字幕と絵が重なりません。

## 考え方：2層で作ります（第13章）

  文字（見出し・箇条書き・数字） → **HTMLで描く**
  絵（図・アイコン・雰囲気）     → **AIに描かせる**（任意）

**文字は絶対に画像に描かせません。**AIに文字を描かせると、日本語が崩れたり、
数字を勝手に作られたりします（「3,000万円」が「6,000万円」になる等）。
数字はHTMLで描くので、台本と必ず一致します。

## 絵を入れるには

script.json の各シーンに `"art"` を足して、何を描くかを1行で書きます。

    {"heading": "…", "art": "書類とパソコンとデータベースが矢印でつながる図", …}

`.env` に `OPENAI_API_KEY` があれば自動で作ります。無ければ文字だけで作ります。

**同じ絵は作り直しません。**台本の文字を直しても、絵の指示が変わらなければ
費用はかかりません。
"""
import json, sys, pathlib, subprocess, html, hashlib, base64, urllib.request
import urllib.error
import os, shutil
from _api_error import die


def _open(req, timeout=60):
    """通信して、失敗したら日本語で説明して止める"""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        die(e, "絵を作るとき")
    except Exception as e:
        die(e, "絵を作るとき")

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Windowsの場合は次の行に置き換えてください
# CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def find_chrome():
    """Google Chrome を探す。無ければ、日本語で理由を伝えて止める"""
    cands = [os.environ.get("CHROME_PATH", ""),   # 環境変数で場所を指定できます
             CHROME,
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             # Linux（Claude Code のクラウド環境など）
             "/opt/pw-browsers/chromium",
             shutil.which("google-chrome") or "",
             shutil.which("chromium") or "",
             shutil.which("chromium-browser") or ""]
    for c in cands:
        if c and pathlib.Path(c).exists():
            return c
    print("\n────────────────────────────────")
    print("  Google Chrome が見つかりませんでした")
    print("────────────────────────────────")
    print("  このツールは、スライドを画像にするために Chrome を使います。")
    print()
    print("  ① https://www.google.com/chrome/ から入れてください（無料）")
    print("  ② 入れたあと、もう一度このコマンドを実行してください")
    print()
    print("  すでに入れているのに出る場合は、Chromeの場所が違います。")
    print("  ツール/make_slides.py の中の「CHROME = 」で始まる行を、")
    print("  ご自身のパソコンでの場所に書き換えてください。")
    print()
    print("  わからないときは、この文章をそのままClaudeに貼ってください。\n")
    sys.exit(1)

# ── 画風の設定（CLAUDE.md と揃えてください）──────────────
STYLE = {
    "bg": "#0f1830",
    "text": "#ffffff",
    "accent": "#ffb02e",
    "font": '"Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif',
    "h_size": 86,          # 見出しの大きさ（文字だけのとき）
    "b_size": 52,          # 箇条書きの大きさ（文字だけのとき）
    # ★絵を入れると文字の幅が狭くなるので、少し小さくします
    "h_size_art": 64,      # 見出し（絵ありのとき）→ 12字までが1行に入ります
    "b_size_art": 44,      # 箇条書き（絵ありのとき）→ 17字までが1行に入ります

    # ★絵の見せ方：
    #   "card" … 濃い背景に、絵を白いカードで置く（落ち着いた印象）
    #   "full" … 白い背景に、絵を大きく置く（明るく、解説動画らしい印象）
    "layout": "card",
    "bg_light": "#ffffff",     # full のときの背景
    "text_light": "#0f1830",   # full のときの文字
}

# ── 絵の設定（第13章）──────────────────────────
ART_MODEL = "gpt-image-2"
ART_QUALITY = "low"        # low ≒ 1円/枚 ／ medium ≒ 9円/枚 ／ high ≒ 26円/枚
ART_SIZE = "1536x1024"

# ★この1文が、全スライドの絵柄を揃えます。変えるならチャンネル単位で変えてください
ART_STYLE = (
    "フラットなベクターイラスト。白の背景。青・緑・オレンジ・黄色の"
    "落ち着いた配色。太めの線画。影は最小限。"
    "★要素を大きく描き、画面いっぱいに配置してください。余白は最小限に。"
    "アイコンや図解として読み取れる、シンプルで明快な絵。"
)
# ★文字を描かせない指示（数字の捏造を根本から防ぎます）
ART_GUARD = (
    "画像の中に文字・数字・記号・ラベルを一切描かないでください。"
    "ロゴ・透かし・署名も入れないでください。絵だけにしてください。"
)


# ── 絵をカードで置く（既定）──────────────────────
TPL = """<!doctype html><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1920px;height:858px;background:{bg};color:{text};font-family:{font};
 padding:60px 130px;display:flex;align-items:center;gap:70px}}
.col{{flex:1;min-width:0}}
h1{{font-size:{h}px;font-weight:800;line-height:1.3;margin-bottom:64px;
 padding-left:36px;border-left:16px solid {accent}}}
ul{{list-style:none}}
li{{font-size:{b}px;line-height:1.9;margin-bottom:26px}}
li::before{{content:"▸ ";color:{accent}}}
.art{{flex:0 0 760px;height:507px;border-radius:36px;overflow:hidden;
 background:#fff;box-shadow:0 24px 60px rgba(0,0,0,.35)}}
.art img{{width:100%;height:100%;object-fit:cover}}
</style><div class="col"><h1>{heading}</h1><ul>{items}</ul></div>{art}"""


# ── 絵を大きく置く（白背景・full）────────────────────
TPL_FULL = """<!doctype html><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1920px;height:858px;background:{bg};color:{text};font-family:{font};
 display:flex;align-items:center}}
.col{{flex:1;padding:0 0 0 130px;max-width:980px;min-width:0;z-index:2}}
h1{{font-size:{h}px;font-weight:800;line-height:1.3;margin-bottom:60px;
 padding-left:34px;border-left:16px solid {accent}}}
ul{{list-style:none}}
li{{font-size:{b}px;line-height:1.85;margin-bottom:24px;font-weight:600}}
li::before{{content:"▸ ";color:{accent}}}
.art{{position:absolute;right:30px;top:50%;transform:translateY(-50%);
 width:830px;height:553px}}
.art img{{width:100%;height:100%;object-fit:contain}}
</style><div class="col"><h1>{heading}</h1><ul>{items}</ul></div>{art}"""


def load_key():
    for name in (".env", "../.env"):
        f = pathlib.Path(name)
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("OPENAI_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and not v.startswith("ここに"):
                        return v
    return None


def make_art(desc, key, dest):
    """絵を1枚つくる。すでにあれば作りません（＝費用がかかりません）"""
    if dest.exists():
        return dest
    prompt = f"{desc}\n\n{ART_STYLE}\n\n{ART_GUARD}"
    body = json.dumps({"model": ART_MODEL, "prompt": prompt,
                       "size": ART_SIZE, "quality": ART_QUALITY, "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    # ★ここは _open() を使いません。絵は任意の機能なので、
    #   失敗しても「文字だけで作る」に落とせるよう、例外をそのまま返します。
    r = json.load(urllib.request.urlopen(req, timeout=180))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(r["data"][0]["b64_json"]))
    return dest


def main(path):
    chrome = find_chrome()
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    out = pathlib.Path("出力/slides"); out.mkdir(parents=True, exist_ok=True)
    art_dir = pathlib.Path("出力/art")

    no_art = "--絵なし" in sys.argv or "--no-art" in sys.argv
    wants_art = (not no_art) and any(sc.get("art") for sc in data["scenes"])
    if no_art:
        print("※ --絵なし が指定されているので、文字だけで作ります（費用0円）\n")
    key = load_key() if wants_art else None
    if wants_art and not key:
        print("※ 絵の指示（art）はありますが、OPENAI_API_KEY がありません。")
        print("  文字だけのスライドを作ります。絵を入れるには .env にキーを書いてください。\n")

    made = 0
    warn = []
    art_fail = False
    for i, sc in enumerate(data["scenes"], 1):
        art_html = ""
        desc = sc.get("art")
        if desc and key:
            # ★絵の指示と画風から名前を決めます。指示が同じなら作り直しません
            tag = hashlib.sha256(
                f"{desc}|{ART_STYLE}|{ART_QUALITY}".encode()).hexdigest()[:16]
            f = art_dir / f"{tag}.png"
            new = not f.exists()
            try:
                make_art(desc, key, f)
                if new:
                    made += 1
                art_html = f'<div class="art"><img src="{f.resolve().as_uri()}"></div>'
            except Exception as e:
                print(f"  ⚠ シーン{i} の絵を作れませんでした（文字だけで作ります）")
                print(f"     理由：{str(e)[:80]}")
                # ★同じエラーを全シーンで繰り返さないよう、以降は文字だけにします
                key = None
                art_fail = True

        full = art_html and STYLE.get("layout") == "full"
        htm = (TPL_FULL if full else TPL).format(
            bg=STYLE["bg_light"] if full else STYLE["bg"],
            text=STYLE["text_light"] if full else STYLE["text"],
            accent=STYLE["accent"], font=STYLE["font"],
            h=STYLE["h_size_art"] if art_html else STYLE["h_size"],
            b=STYLE["b_size_art"] if art_html else STYLE["b_size"],
            heading=html.escape(sc["heading"]),
            items="".join(f"<li>{html.escape(b)}</li>" for b in sc.get("bullets", [])),
            art=art_html)
        src = out / f"_slide{i:02d}.html"
        src.write_text(htm, encoding="utf-8")
        png = out / f"slide{i:02d}.png"
        # ★Linuxで管理者（root）として動くとき（クラウド環境）は --no-sandbox が必要です
        extra = ["--no-sandbox"] if (sys.platform.startswith("linux")
                                     and getattr(os, "geteuid", lambda: 1)() == 0) else []
        subprocess.run([chrome, "--headless", *extra, "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files",
                        "--window-size=1920,858", "--screenshot=" + str(png),
                        "--default-background-color=00000000",
                        src.resolve().as_uri()],
                       capture_output=True, check=True)
        src.unlink()
        mark = "＋絵" if art_html else "　　"
        print(f"  {png.name} {mark} {sc['heading']}")

        # ★1行に収まるかを、その場で知らせます（2行に折れると揃わなくなるため）
        lim_h = 12 if art_html else 18
        lim_b = 17 if art_html else 25
        if len(sc["heading"]) > lim_h:
            warn.append(f"    シーン{i} 見出し {len(sc['heading'])}字"
                        f"（上限{lim_h}字）… {sc['heading']}")
        for b in sc.get("bullets", []):
            if len(b) > lim_b:
                warn.append(f"    シーン{i} 箇条書き {len(b)}字（上限{lim_b}字）… {b}")

    if art_fail:
        print("\n  ※ 絵は入れられませんでしたが、文字だけのスライドは全部できています。")
        print("     絵を入れたい場合は、.env の OPENAI_API_KEY を確認してから、")
        print("     もう一度このコマンドを実行してください（できている絵は作り直しません）。")

    if warn:
        print("\n  ⚠ 文字数の上限を超えています（2行に折れて、他のスライドと揃わなくなります）")
        for w in warn:
            print(w)
        print("    → 台本の見出し・箇条書きを短くしてください（文字を小さくしないでください）")

    print(f"\n完了: {len(data['scenes'])}枚 → {out}")
    if made:
        yen = {"low": 1, "medium": 9, "high": 26}.get(ART_QUALITY, 9) * made
        print(f"  絵を {made}枚 つくりました（約{yen}円 ／ {ART_QUALITY}）")
        print(f"  → 出力/art に保存しました。**同じ指示なら次回は0円**です")
    elif wants_art and key:
        print("  絵はすべて使い回しました（費用は0円です）")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "script.json")
