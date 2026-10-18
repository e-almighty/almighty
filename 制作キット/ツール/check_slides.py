#!/usr/bin/env python3
"""スライドの箇条書きが、ナレーションの言い換えになっていないか確認する

使い方:
  python3 ツール/check_slides.py script.json

## なぜ必要か

ナレーションは**字幕で全文が画面に出ます。**
その状態で、箇条書きにも同じことを書くと、**画面に同じ内容が2回**出ます。

  スライド：「全員にかかるわけではない」
  字幕　　：「ですが、相続税は全員にかかるわけではありません。」

視聴者は同じ文を2回読むことになり、そのぶんナレーションが耳に入りません。

## 箇条書きに書くもの

**あとで思い出したい形**で書いてください。ナレーションの要約ではありません。

  ○ 3,000万円＋600万円×人数    ← 数式。声だけでは覚えられない
  ○ 基礎控除／代襲相続          ← 用語。字面を見せる意味がある
  ○ 期限は10か月                ← 数字。目に残したい
  × 全員にかかるわけではない    ← ナレーションの言い換え

**箇条書きが1つもない画面があっても構いません。**見出しだけで足りる場面はあります。
"""
import json, sys, pathlib, re
import pathlib


def keywords(text):
    """その文の「中身のある語」（漢字・カタカナの2文字以上）を取り出す"""
    return set(re.findall(r"[一-龥]{2,}|[ァ-ヴー]{3,}", text or ""))


# 「文」になっている＝ナレーションの言い換えの疑い
_SENTENCE = re.compile(r"(ない|ません|です|ます|ある|あり|する|して|なる|なり|いる|できる|よい|多い)")
# 数字・数式・記号を含む＝目に残す価値がある（言い換えではない）
_WORTH = re.compile(r"[0-9０-９]|[＋+×÷=＝%％]|[一二三四五六七八九十百千万億]{2,}")


def is_restatement(bullet, narration_keys):
    """その箇条書きが「ナレーションの言い換え」かどうか"""
    bk = keywords(bullet)
    if not bk:
        return False, 0.0
    rate = len(bk & narration_keys) / len(bk)
    # 数字や数式が入っているものは、声だけでは覚えられないので残す価値がある
    if _WORTH.search(bullet):
        return False, rate
    # 文の形になっていなければ（体言止め・用語）、残す価値がある
    if not _SENTENCE.search(bullet):
        return False, rate
    return rate >= 0.6, rate


def check_length(data):
    """見出し・箇条書きが1行に収まるかを、台本の段階で見ます

    絵を全部作ってから「長すぎます」と言われても、待ち時間が無駄になります。
    ここで先に気づけるようにしています（上限は make_slides.py と同じ値です）。
    """
    warn = []
    for i, sc in enumerate(data["scenes"], 1):
        art = bool(sc.get("art"))
        lim_h, lim_b = (12, 17) if art else (18, 25)
        h = sc.get("heading", "")
        if len(h) > lim_h:
            warn.append(f"   シーン{i} 見出し {len(h)}字（上限{lim_h}字）… {h}")
        for b in sc.get("bullets", []):
            if len(b) > lim_b:
                warn.append(f"   シーン{i} 箇条書き {len(b)}字（上限{lim_b}字）… {b}")
    if warn:
        print("⚠ 文字数の上限を超えています（2行に折れて、他のスライドと揃わなくなります）")
        for w in warn:
            print(w)
        print("   → 文字を小さくせず、**台本のほうを短くしてください**")
        print("   ※ 絵ありのシーンは、文字の幅が狭くなるぶん上限が下がります\n")
    else:
        print("✓ 見出し・箇条書きは、すべて1行に収まります\n")


def check_plan():
    """チャンネル設計（CLAUDE.md）が埋まっているかを見ます"""
    f = pathlib.Path("CLAUDE.md")
    if not f.exists():
        return
    body = f.read_text(encoding="utf-8")
    body = body.split("# このチャンネルについて")[-1]
    n = body.count("（　）")
    if n:
        print(f"⚠ CLAUDE.md に、まだ埋めていない項目が {n} か所あります")
        print("   チャンネル名・視聴者・人格・声などが（　）のままだと、")
        print("   **どの動画も似た一般論になります**（第9章・第10章）")
        print("   → `/はじめる` で、先にチャンネル設計を済ませてください\n")


def main(path):
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    total, dup = 0, 0
    print("台本を、動画にする前に確認します\n")
    check_plan()
    check_length(data)
    print("箇条書きが、ナレーションの言い換えになっていないか確認します\n")

    for i, sc in enumerate(data["scenes"], 1):
        nar = "".join(l["text"] for l in sc.get("lines", []))
        nk = keywords(nar)
        bad = []
        for b in sc.get("bullets", []):
            if not keywords(b):
                continue
            total += 1
            ng, rate = is_restatement(b, nk)
            if ng:
                dup += 1
                bad.append((b, rate))
        if bad:
            print(f"⚠ シーン{i}「{sc.get('heading','')}」")
            for b, r in bad:
                print(f"   ・{b}　（ナレーションと {r*100:.0f}% 同じ）")
            print()

    if not total:
        print("箇条書きがありません。")
        return

    print(f"── 箇条書き {total}個のうち、{dup}個（{dup/total*100:.0f}%）が"
          f"ナレーションとほぼ同じ ──\n")

    if dup == 0:
        print("✓ ナレーションの言い換えになっている箇条書きはありません。")
        return

    if dup / total >= 0.25:
        print("★直してください。画面に同じ内容が2回出ています。")
    else:
        print("上に出た行だけ、直してください。")
    print()
    print("箇条書きは、ナレーションの要約ではなく")
    print("**あとで思い出したい形**（数式・用語・数字）にしてください。")
    print()
    print("  ○ 3,000万円＋600万円×人数")
    print("  ○ 期限は10か月")
    print("  × 全員にかかるわけではない")
    print()
    print("書くことがなければ、**箇条書きを減らしてください。**")
    print("見出しだけの画面があっても構いません（第13章 13-1）。")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "script.json")
