#!/usr/bin/env python3
"""デッキの後工程（Windows 向け）。
  python3 deck_tools.py shoot [start end]   全ページを headless Chrome で 1920x1080 撮影 → screenshots/final/
  python3 deck_tools.py sheet               screenshots/final/ を 4列の一覧シートにまとめる → screenshots/overview/
  python3 deck_tools.py standalone          CSS/JS/画像を埋め込んだ 1 ファイル HTML → 納品/
  python3 deck_tools.py pdf                 screenshots/final/ の PNG から PDF（16:9・JPEG 圧縮）→ 納品/
  python3 deck_tools.py all                 shoot → sheet → standalone → pdf
注意（8/26 の記録より）: Windows の Chrome は --screenshot に相対パスを渡すと 0 バイトになる。絶対パスで渡す。
"""
from __future__ import annotations

import base64
import io
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SLIDES = ROOT / "slides"
INDEX = SLIDES / "index.html"
SHOTS = ROOT / "screenshots" / "final"
OVERVIEW = ROOT / "screenshots" / "overview"
DELIVER = ROOT / "納品"
BASENAME = "第一部AI_Astraを味方にする夜_2026-10-21"
CHROME = pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def count_slides() -> int:
    return len(re.findall(r"<section\b", INDEX.read_text(encoding="utf-8")))


def shoot(start: int = 1, end: int | None = None, w: int = 1920, h: int = 1080) -> int:
    n = count_slides()
    end = end or n
    SHOTS.mkdir(parents=True, exist_ok=True)
    url = INDEX.resolve().as_uri()
    profile = tempfile.mkdtemp(prefix="deck_shot_profile_")
    ok = 0
    for i in range(start, end + 1):
        shot = SHOTS / f"slide_{i:03d}.png"
        if shot.exists():
            shot.unlink()
        cmd = [str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--disable-extensions", "--no-sandbox", f"--user-data-dir={profile}",
               "--virtual-time-budget=6000", f"--window-size={w},{h}",
               f"--screenshot={shot}", f"{url}#{i}"]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            print(f"WARN: {i} timeout")
        if shot.exists() and shot.stat().st_size > 1000:
            ok += 1
        else:
            print(f"WARN: {i} ページ目の撮影に失敗")
    print(f"OK: {ok}/{end - start + 1} 枚を {SHOTS} に保存")
    return 0 if ok == end - start + 1 else 1


def sheet(cols: int = 4, per_sheet: int = 20, tw: int = 480) -> None:
    from PIL import Image, ImageDraw
    OVERVIEW.mkdir(parents=True, exist_ok=True)
    files = sorted(SHOTS.glob("slide_*.png"))
    th = int(tw * 9 / 16)
    pad = 14
    for s in range(0, len(files), per_sheet):
        chunk = files[s:s + per_sheet]
        rws = (len(chunk) + cols - 1) // cols
        W = cols * (tw + pad) + pad
        H = rws * (th + pad + 26) + pad
        im = Image.new("RGB", (W, H), "#333")
        d = ImageDraw.Draw(im)
        for k, f in enumerate(chunk):
            r, c = divmod(k, cols)
            x = pad + c * (tw + pad)
            y = pad + r * (th + pad + 26)
            t = Image.open(f).convert("RGB").resize((tw, th))
            im.paste(t, (x, y + 22))
            d.text((x, y + 4), f.stem, fill="#fff")
        out = OVERVIEW / f"sheet_{s // per_sheet + 1}.png"
        im.save(out)
        print(f"OK: {out} ({len(chunk)} 枚)")


def standalone() -> pathlib.Path:
    DELIVER.mkdir(exist_ok=True)
    html = INDEX.read_text(encoding="utf-8")
    for css in ("deck07.css", "deck07-bright.css"):
        c = (SLIDES / "css07" / css).read_text(encoding="utf-8")
        html = html.replace(f'<link rel="stylesheet" href="css07/{css}">', "<style>\n" + c + "\n</style>")
    js = (SLIDES / "js07" / "deck07.js").read_text(encoding="utf-8")
    html = html.replace('<script src="js07/deck07.js"></script>', "<script>\n" + js + "\n</script>")

    def to_data(m: re.Match) -> str:
        rel = m.group(1)
        p = SLIDES / rel
        if not p.exists():
            print(f"WARN: 画像が無い {rel}")
            return m.group(0)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return f'src="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"'

    html, n = re.subn(r'src="(img/[^"]+)"', to_data, html)
    leftovers = re.findall(r'(?:src|href)="(?!data:|#)([^"]+)"', html)
    out = DELIVER / f"{BASENAME}.html"
    out.write_text(html, encoding="utf-8", newline="\n")
    print(f"OK: 埋め込み画像 {n} 枚 / 残った外部参照 {leftovers or 'なし'} / {out} ({out.stat().st_size / 1024 / 1024:.2f} MB)")
    return out


def pdf(quality: int = 90) -> pathlib.Path:
    import img2pdf
    from PIL import Image
    DELIVER.mkdir(exist_ok=True)
    files = sorted(SHOTS.glob("slide_*.png"))
    pages = []
    for f in files:
        im = Image.open(f).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True)
        pages.append(buf.getvalue())
    layout = img2pdf.get_layout_fun((img2pdf.in_to_pt(13.333), img2pdf.in_to_pt(7.5)))
    out = DELIVER / f"{BASENAME}.pdf"
    out.write_bytes(img2pdf.convert(pages, layout_fun=layout))
    print(f"OK: {len(pages)} ページ → {out} ({out.stat().st_size / 1024 / 1024:.2f} MB)")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "shoot":
        a = [int(x) for x in sys.argv[2:4]]
        raise SystemExit(shoot(*a))
    if cmd == "sheet":
        sheet()
    elif cmd == "standalone":
        standalone()
    elif cmd == "pdf":
        pdf()
    elif cmd == "all":
        shoot(); sheet(); standalone(); pdf()
    else:
        print(__doc__)
