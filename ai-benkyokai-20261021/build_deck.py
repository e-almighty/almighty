#!/usr/bin/env python3
"""AI勉強会（2026-10-21）第一部 AI「GPT-6 Astra」デッキ生成スクリプト。

- 見た目の正本 `css07/deck07.css` `js07/deck07.js` は無改変。明るい地（水色×濃紺）は
  `css07/deck07-bright.css`（このスクリプトが書き出す上書きCSS）で実現する。
- 40枚の中身は下の SLIDES に1枚1項目で定義。図解はすべて HTML/CSS/SVG で内蔵。
- 実行:  python3 build_deck.py   → slides/index.html と speaker-notes.md を書き出す
"""
from __future__ import annotations

import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SLIDES_DIR = ROOT / "slides"

# ---- 配色（明るい地） -------------------------------------------------------
NAVY = "#0A2A55"      # 文字・罫線・ハードシャドウ
BLUE = "#3D6FA5"      # 補助文字・キッカー
SKY = "#CFE6F9"       # 章扉・核心1文の地
PAPER = "#EEF5FC"     # 本文スライドの地
WHITE = "#FFFFFF"
AMBER = "#FFC532"     # 今すぐ覚える言葉のハイライト
LINE = "#B9D3EA"      # 薄い罫線
MUTED = "#4A6A8F"     # 補足文字
GREEN = "#1E7F4F"     # Astra 側の色分け
RUST = "#C8622A"      # Fable 側の色分け
RED = "#C0392B"       # 注意

BRIGHT_CSS = f"""/* deck07-bright.css — 明るい地（水色×濃紺）用の上書き。deck07.css は無改変。
   2026-08-15 エレコム案件で確定した配色（地 {SKY} / 文字 {NAVY}）を 07 の骨組みに当てる。 */
html,body{{background:#DCE9F5}}
.xop-slide{{background:#DCE9F5}}
.xop-canvas{{background:{PAPER};box-shadow:0 0 0 1px rgba(10,42,85,.18)}}
.tone-paper .xop-canvas{{background:{PAPER}}}
.tone-white .xop-canvas{{background:{WHITE}}}
.tone-sky .xop-canvas{{background:{SKY}}}
.sem-paper{{background:{PAPER};color:{NAVY}}}
.sem-white{{background:{WHITE};color:{NAVY}}}
.sem-sky{{position:absolute;inset:0;overflow:hidden;color:{NAVY};font-family:inherit;
  background:radial-gradient(circle at 14% 10%,rgba(255,255,255,.75),transparent 34%),
  radial-gradient(circle at 86% 84%,rgba(61,111,165,.22),transparent 38%),
  linear-gradient(135deg,#DCEEFB 0%,{SKY} 50%,#B9D9F3 100%)}}
.corner-stripes{{opacity:.55;background:repeating-linear-gradient(135deg,{NAVY} 0 10px,transparent 10px 20px)}}
.tone-sky .corner-stripes{{opacity:.35}}
.brand-watermark{{color:{NAVY};opacity:.12}}
.tone-sky .brand-watermark{{color:{NAVY};opacity:.14}}
.hl{{background:{AMBER};padding:0 12px;color:{NAVY}}}
.ug{{background:linear-gradient(transparent 62%,{AMBER} 62%);padding:0 .08em}}
.card-hard{{background:{WHITE};border:3px solid {NAVY};box-shadow:10px 10px 0 {NAVY};border-radius:14px}}
.card-soft{{background:{WHITE};border:2px solid {LINE};box-shadow:0 14px 34px rgba(10,42,85,.10);border-radius:14px}}
.num{{background:{NAVY};color:{WHITE};width:54px;height:54px;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;font-size:28px;font-weight:950;border-radius:10px}}
.pill{{display:inline-block;padding:6px 18px;border-radius:999px;font-weight:900;font-size:22px}}
.deck-nav{{opacity:0}}
.deck-nav:hover{{opacity:1}}
"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---- 部品 --------------------------------------------------------------------
def header(kicker: str, title: str, top: str = "7%") -> str:
    return (f'<div style="position:absolute;left:6%;right:6%;top:{top}">'
            f'<div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.06em;margin-bottom:14px">{kicker}</div>'
            f'<div style="font-size:56px;font-weight:950;line-height:1.15;color:{NAVY}">{title}</div></div>')


def source(text: str) -> str:
    return (f'<div style="position:absolute;left:6%;right:6%;bottom:4.5%;font-size:18px;font-weight:800;color:{MUTED}">'
            f'{text}</div>')


def footer_brand() -> str:
    return (f'<div style="position:absolute;right:5%;bottom:5%;font-size:18px;font-weight:850;color:{BLUE}">'
            f'株式会社オールマイティ</div>')


def card(title: str, body: str = "", *, accent: str = NAVY, extra: str = "", cls: str = "card-hard",
         title_size: int = 34, body_size: int = 23) -> str:
    b = f'<div style="font-size:{body_size}px;font-weight:800;line-height:1.5;color:{MUTED};margin-top:12px">{body}</div>' if body else ""
    return (f'<div class="{cls}" style="padding:28px 32px;display:flex;flex-direction:column;justify-content:center;{extra}">'
            f'<div style="font-size:{title_size}px;font-weight:950;line-height:1.25;color:{accent}">{title}</div>{b}</div>')


def grid(cells: list[str], cols: int, *, top: str = "31%", bottom: str = "9%", gap: int = 24,
         left: str = "6%", right: str = "6%") -> str:
    return (f'<div style="position:absolute;left:{left};right:{right};top:{top};bottom:{bottom};display:grid;'
            f'grid-template-columns:repeat({cols},1fr);gap:{gap}px">' + "".join(cells) + '</div>')


def rows(items: list[str], *, top: str = "31%", bottom: str = "9%", size: int = 32, left: str = "7%",
         right: str = "7%", numbered: bool = True) -> str:
    out = []
    for i, it in enumerate(items, 1):
        n = f'<b class="num">{i}</b>' if numbered else f'<b class="num" style="background:{BLUE}">●</b>'
        out.append(f'<p style="display:flex;align-items:center;gap:22px;margin:0;font-size:{size}px;font-weight:900;color:{NAVY}">{n}<span>{it}</span></p>')
    return (f'<div style="position:absolute;left:{left};right:{right};top:{top};bottom:{bottom};display:flex;'
            f'flex-direction:column;justify-content:space-between">' + "".join(out) + '</div>')


def table(head: list[str], body: list[list[str]], *, top: str = "28%", bottom: str | None = None, size: int = 24,
          widths: list[str] | None = None, highlight_col: int | None = None) -> str:
    cols = len(head)
    gtc = " ".join(widths) if widths else " ".join(["1fr"] * cols)
    cells = []
    for j, h in enumerate(head):
        cells.append(f'<div style="background:{NAVY};color:#fff;padding:16px 20px;font-size:{size}px;font-weight:950">{h}</div>')
    for r in body:
        for j, c in enumerate(r):
            bg = "#FFF6D6" if (highlight_col is not None and j == highlight_col) else WHITE
            cells.append(f'<div style="background:{bg};padding:14px 20px;font-size:{size}px;font-weight:850;line-height:1.4;border-top:2px solid {LINE};color:{NAVY}">{c}</div>')
    return (f'<div style="position:absolute;left:6%;right:6%;top:{top};display:grid;grid-template-columns:{gtc};'
            f'border:3px solid {NAVY};box-shadow:10px 10px 0 {NAVY};background:#fff;border-radius:12px;overflow:hidden">'
            + "".join(cells) + '</div>')


def flow(steps: list[tuple[str, str]], *, top: str = "33%", height: str = "36%", accent: str = NAVY) -> str:
    """横並びの工程図。steps=[(見出し, 説明)]"""
    parts = []
    for i, (t, d) in enumerate(steps):
        if i:
            parts.append(f'<div style="display:flex;align-items:center;font-size:46px;font-weight:950;color:{BLUE}">▶</div>')
        parts.append(f'<div class="card-hard" style="flex:1;padding:22px 20px;text-align:center;display:flex;flex-direction:column;justify-content:center">'
                     f'<div style="font-size:22px;font-weight:950;color:{BLUE};margin-bottom:8px">STEP {i+1}</div>'
                     f'<div style="font-size:30px;font-weight:950;color:{accent};line-height:1.2">{t}</div>'
                     f'<div style="font-size:21px;font-weight:800;color:{MUTED};line-height:1.45;margin-top:10px">{d}</div></div>')
    return f'<div style="position:absolute;left:6%;right:6%;top:{top};height:{height};display:flex;gap:16px;align-items:stretch">' + "".join(parts) + '</div>'


def statement(kicker: str, line1: str, line2: str = "", sub: str = "") -> str:
    l2 = f'<div style="font-size:70px;font-weight:950;line-height:1.25;color:{NAVY};margin-top:8px">{line2}</div>' if line2 else ""
    s = f'<div style="font-size:30px;font-weight:850;line-height:1.5;color:{BLUE};margin-top:34px">{sub}</div>' if sub else ""
    return (f'<div style="position:absolute;left:7%;right:7%;top:50%;transform:translateY(-50%)">'
            f'<div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em;margin-bottom:26px">{kicker}</div>'
            f'<div style="font-size:54px;font-weight:900;line-height:1.3;color:{NAVY}">{line1}</div>{l2}{s}</div>')


def chapter(num: str, title: str, lead: str) -> str:
    return (f'<div style="position:absolute;left:8%;top:18%;font-size:180px;font-weight:950;line-height:1;color:rgba(10,42,85,.18)">{num}</div>'
            f'<div style="position:absolute;left:8%;right:8%;top:44%">'
            f'<div style="font-size:26px;font-weight:950;color:{BLUE};letter-spacing:.1em;margin-bottom:18px">CHAPTER {num}</div>'
            f'<div style="font-size:92px;font-weight:950;line-height:1.1;color:{NAVY}">{title}</div>'
            f'<div style="width:220px;height:12px;background:{AMBER};margin:30px 0 26px"></div>'
            f'<div style="font-size:32px;font-weight:850;line-height:1.5;color:{NAVY}">{lead}</div></div>')


def pill(text: str, bg: str = NAVY, fg: str = "#fff") -> str:
    return f'<span class="pill" style="background:{bg};color:{fg}">{text}</span>'


# ---- 図解 ---------------------------------------------------------------------
def timeline(events: list[tuple[str, str, str]], *, top: str = "30%") -> str:
    """events=[(日付, ラベル, 色)]"""
    n = len(events)
    cols = []
    for d, label, color in events:
        cols.append(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;text-align:center">'
                    f'<div style="font-size:26px;font-weight:950;color:{color}">{d}</div>'
                    f'<div style="width:28px;height:28px;border-radius:50%;background:{color};border:4px solid #fff;box-shadow:0 0 0 3px {color};margin:16px 0"></div>'
                    f'<div style="font-size:22px;font-weight:900;line-height:1.35;color:{NAVY};padding:0 8px">{label}</div></div>')
    return (f'<div style="position:absolute;left:5%;right:5%;top:{top}">'
            f'<div style="position:relative;height:0">'
            f'<div style="position:absolute;left:{100/n/2:.1f}%;right:{100/n/2:.1f}%;top:70px;height:6px;background:{NAVY};border-radius:3px"></div></div>'
            f'<div style="display:flex">' + "".join(cols) + '</div></div>')


def hub_svg() -> str:
    """中央の Astra から周囲のアプリへ線を引く図（SVG + HTML）"""
    cx, cy = 560, 600
    pts = [(220, 330, "メール"), (220, 870, "表計算"), (560, 940, "顧客管理"), (900, 870, "申請フォーム"), (900, 330, "ブラウザ")]
    lines = "".join(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="{BLUE}" stroke-width="6" stroke-dasharray="14 12"/>' for x, y, _ in pts)
    boxes = "".join(
        f'<div style="position:absolute;left:{x-120}px;top:{y-48}px;width:240px;height:96px;display:flex;align-items:center;justify-content:center;'
        f'background:#fff;border:3px solid {NAVY};border-radius:14px;box-shadow:8px 8px 0 {NAVY};font-size:28px;font-weight:950;color:{NAVY}">{t}</div>'
        for x, y, t in pts)
    center = (f'<div style="position:absolute;left:{cx-130}px;top:{cy-130}px;width:260px;height:260px;border-radius:50%;background:{NAVY};color:#fff;'
              f'display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 18px 40px rgba(10,42,85,.3)">'
              f'<div style="font-size:22px;font-weight:900;color:{AMBER}">GPT-6</div><div style="font-size:54px;font-weight:950;line-height:1">Astra</div>'
              f'<div style="font-size:20px;font-weight:850;margin-top:8px">画面を見て操作</div></div>')
    return (f'<svg viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0;width:1920px;height:1080px">{lines}</svg>' + boxes + center)


def kpi(items: list[tuple[str, str, str]]) -> str:
    cells = []
    for big, label, note in items:
        cells.append(f'<div class="card-hard" style="padding:34px 28px;text-align:center;display:flex;flex-direction:column;justify-content:center">'
                     f'<div style="font-size:96px;font-weight:950;line-height:1;color:{NAVY}">{big}</div>'
                     f'<div style="font-size:30px;font-weight:950;color:{BLUE};margin-top:18px">{label}</div>'
                     f'<div style="font-size:21px;font-weight:800;line-height:1.45;color:{MUTED};margin-top:12px">{note}</div></div>')
    return grid(cells, 3, top="30%", bottom="12%", gap=30)


def stairs(steps: list[tuple[str, str]], marker_after: int, marker_text: str) -> str:
    n = len(steps)
    cols = []
    for i, (t, d) in enumerate(steps):
        h = 34 + i * 15
        bg = AMBER if i < marker_after else "#fff"
        cols.append(f'<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;height:100%">'
                    f'<div style="height:{h}%;background:{bg};border:3px solid {NAVY};border-bottom:0;border-radius:14px 14px 0 0;'
                    f'padding:18px 16px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;text-align:center">'
                    f'<div style="font-size:22px;font-weight:950;color:{BLUE}">{i+1}</div>'
                    f'<div style="font-size:32px;font-weight:950;color:{NAVY};margin-top:4px">{t}</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{MUTED};line-height:1.4;margin-top:8px">{d}</div></div></div>')
    left_pct = marker_after / n * 100
    marker = (f'<div style="position:absolute;left:{left_pct:.1f}%;top:-6%;bottom:0;border-left:6px dashed {RED}"></div>'
              f'<div style="position:absolute;left:{left_pct+1.2:.1f}%;top:-4%;background:{RED};color:#fff;padding:8px 18px;border-radius:10px;font-size:22px;font-weight:950">{marker_text}</div>')
    return (f'<div style="position:absolute;left:6%;right:6%;top:36%;bottom:9%;border-bottom:6px solid {NAVY}">'
            f'<div style="position:relative;height:100%;display:flex;gap:10px;align-items:stretch">' + "".join(cols) + marker + '</div></div>')


def ladder(tiers: list[tuple[str, str, str, str]]) -> str:
    """tiers=[(名前, 一言, 価格, 向く仕事)] 左から低→高"""
    cols = []
    for i, (name, word, price, job) in enumerate(tiers):
        h = 58 + i * 21
        strong = i == len(tiers) - 1
        bg = NAVY if strong else "#fff"
        fg = "#fff" if strong else NAVY
        sub = AMBER if strong else BLUE
        cols.append(f'<div style="flex:1;display:flex;align-items:flex-end;height:100%">'
                    f'<div class="card-hard" style="width:100%;height:{h}%;background:{bg};padding:26px 24px;display:flex;flex-direction:column;justify-content:flex-start">'
                    f'<div style="font-size:40px;font-weight:950;color:{fg}">{name}</div>'
                    f'<div style="font-size:30px;font-weight:950;color:{sub};margin-top:8px">{word}</div>'
                    f'<div style="font-size:22px;font-weight:850;color:{fg};opacity:.85;margin-top:14px;line-height:1.45">{job}</div>'
                    f'<div style="font-size:21px;font-weight:900;color:{sub};margin-top:auto">{price}</div></div></div>')
    return f'<div style="position:absolute;left:6%;right:6%;top:30%;bottom:9%;display:flex;gap:26px;align-items:stretch">' + "".join(cols) + '</div>'


def two_cols(left: str, right: str, *, top: str = "30%", bottom: str = "9%", gap: int = 28) -> str:
    return (f'<div style="position:absolute;left:6%;right:6%;top:{top};bottom:{bottom};display:grid;grid-template-columns:1fr 1fr;gap:{gap}px">'
            f'{left}{right}</div>')


def bubble(text: str, *, ok: bool) -> str:
    bg = "#E6F4EC" if ok else "#FBE9E7"
    bd = GREEN if ok else RED
    mark = "○ 作業の指示" if ok else "× ただの相談"
    return (f'<div style="background:{bg};border:3px solid {bd};border-radius:22px;padding:30px 34px;position:relative">'
            f'<div style="font-size:24px;font-weight:950;color:{bd};margin-bottom:12px">{mark}</div>'
            f'<div style="font-size:30px;font-weight:900;line-height:1.5;color:{NAVY}">{text}</div></div>')


def logo(name: str, size: int = 64) -> str:
    w = int(size * 1.75) if name == "claude_code" else size   # claude_code.png は横長（545x312）
    return (f'<img src="img/logos/{name}.png" alt="{name}" style="width:{w}px;height:{size}px;object-fit:contain;'
            f'border:1px solid {LINE};border-radius:14px;background:#fff;padding:6px">')


# ---- スライド定義 -----------------------------------------------------------------
# (tone, 型ID, 話者ノート, 本文HTML)
SLIDES: list[tuple[str, str, str, str]] = []


def add(tone: str, tid: str, notes: str, body: str) -> None:
    SLIDES.append((tone, tid, notes, body))


# 01 表紙
add("sky", "EVENT-COVER",
    "こんばんは。日本営業協会の勉強会、第一部はAIです。今日の主役はChatGPTの最上位AI「Astra（アストラ）」。何ができて、どう頼めばよくて、どこに気をつけるか。それをもう一つの主役、Claude Code（Fable 5.1）との対比で見ていきます。",
    f'<div style="position:absolute;left:6%;top:9%;bottom:9%;width:50%;display:flex;flex-direction:column;justify-content:center">'
    f'<div style="font-size:24px;font-weight:950;letter-spacing:.1em;color:{BLUE};margin-bottom:28px">日本営業協会 勉強会 ｜ 第一部 AI ｜ 2026.10.21 WED 18:30</div>'
    f'<div style="font-size:84px;font-weight:950;line-height:1.1;color:{NAVY}">Astra を<br><span class="hl">味方にする夜</span></div>'
    f'<div style="width:220px;height:12px;background:{NAVY};margin:34px 0 26px"></div>'
    f'<div style="font-size:28px;font-weight:850;line-height:1.55;color:{NAVY}">ChatGPT の最上位 AI「GPT-6 Astra」を<br>どう使い、Claude Code（Fable 5.1）と<br>どう使い分けるか</div>'
    f'<div style="font-size:22px;font-weight:850;color:{BLUE};margin-top:30px">株式会社オールマイティ　平田 正一</div></div>'
    f'<div style="position:absolute;left:60%;right:6%;top:16%;bottom:16%;display:flex;flex-direction:column;justify-content:center;gap:22px">'
    + card("手を動かす AI", "答えを書くだけでなく、パソコンを操作して仕事を終わらせる", title_size=38)
    + card("任せ方の 4 要素", "材料・成果物・完成条件・停止地点。これだけで失敗が減る", title_size=38)
    + card("勝手に動かせない仕組み", "9/28 の公開中止から学ぶ、人が握っておく 3 つの手綱", title_size=38)
    + '</div>')

# 02 流れ＋ゴール
add("paper", "AGENDA",
    "今日の流れは7章です。前半でAstraの正体とできること、使い方と料金。中盤で任せ方のコツと注意点。後半でClaude側との対比。最後にワークタイム。ゴールは一つ、帰るときに「自分の仕事でAstraに任せる1つ」が決まっていることです。",
    header("TONIGHT'S FLOW", "この時間の流れ <span style=\"font-size:34px;color:" + BLUE + "\">／ ゴール：帰るときに「Astra に任せる仕事」が 1 つ決まっている</span>")
    + f'<div style="position:absolute;left:6%;right:6%;top:30%;bottom:12%;display:grid;grid-template-columns:1fr 1fr;gap:0 40px;align-content:start;row-gap:44px">'
    + "".join(f'<p style="display:flex;align-items:center;gap:22px;margin:0;font-size:36px;font-weight:900;color:{NAVY}"><b class="num" style="width:62px;height:62px;font-size:32px">{n}</b><span>{t}</span></p>'
              for n, t in [(1, "Astra とは（正体・思想・3 つの数字）"), (5, "注意点（9/28 の事件と 3 か条）"),
                           (2, "できること（読む・作る・操作する・動かす）"), (6, "Claude Fable 5.1 との対比"),
                           (3, "使い方と料金（Plus の盲点）"), (7, "ワークタイム・まとめ"),
                           (4, "任せ方のコツ（指示の 4 要素）")])
    + '</div>'
    + source("数字・料金はすべて 2026-10-19 時点の調査。AI の世界は週単位で変わるので、当日時点の情報として聞いてください。"))

# 03 自己紹介
add("paper", "SPEAKER-PROFILE",
    "改めまして、株式会社オールマイティの平田です。ヤマダ電機の2階を拠点に、パソコンのサポートからAIの導入までワンストップでやっています。AI勉強会は今回で8回目。そして私自身、この資料のような40〜60枚のスライドをAstraで2時間ほどで仕上げています。今日はその実体験ベースでお話しします。",
    header("SPEAKER", "話す人：平田 正一（株式会社オールマイティ 代表）")
    + two_cols(
        card("何をしている会社か", "IT・AI コンサルティング<br>パソコンサポート<br>接客・販売支援<br><br>家電量販店の店頭を拠点に、ノーコード開発からパソコンの選定・設定、AI 導入までをワンストップで", title_size=38, body_size=28),
        '<div style="display:flex;flex-direction:column;gap:20px;height:100%">'
        + card("AI 勉強会は今回で第 8 回", "2026 年 8 月は 3 部構成（壁打ち AI・AI リサーチ術・GPTs 量産）を開催", title_size=30, body_size=22, cls="card-soft")
        + card("Astra でスライド 40〜60 枚を約 2 時間", "Claude で構成と図を作り、Astra に渡して仕上げる。今日の資料もその型", title_size=30, body_size=22, cls="card-soft")
        + card("2 社の AI で 1 つの頭脳を共有", "Obsidian に会社の記憶を置き、Claude Code と Codex の両方から読ませている", title_size=30, body_size=22, cls="card-soft")
        + '</div>',
        top="29%", bottom="10%")
    + footer_brand())

# 04 章扉1
add("sky", "CHAPTER-1",
    "第1章、Astraとは何か。名前は聞いたことがあっても、何が新しいのかを説明できる人は少ないと思います。まず正体をはっきりさせましょう。",
    chapter("01", "Astra とは", "ChatGPT の最上位モデル「GPT-6 Astra」（2026-09-03 公開）。<br>答えを書くだけの AI ではない。"))

# 05 名前の整理（タイムライン）
add("paper", "SEM-38",
    "この1か月半の出来事を並べました。9月1日にAnthropicのFable 5.1、9月3日にOpenAIのGPT-6 Astra。2日違いの頂上対決です。22日に下位のSolとLuna、28日に次の版「6.1 Astra」が公開中止、翌29日に6.1 Solは予定どおり。10月7日からは普通のチャット画面にも「GPT-6」が並びました。ポイント：画面で「GPT-6 Pro」と出ているのがAstraです。",
    header("WHO IS WHO", "名前の整理：この 1 か月半で起きたこと")
    + timeline([("9/01", "Claude Fable 5.1<br>（Anthropic）", RUST), ("9/03", "GPT-6 Astra<br>最上位・今日の主役", GREEN),
                ("9/22", "GPT-6 Sol／Luna<br>中位・軽量", NAVY), ("9/28", "GPT-6.1 Astra<br>公開中止", RED),
                ("9/29", "GPT-6.1 Sol<br>予定どおり公開", NAVY), ("10/07", "通常チャットに<br>「GPT-6」が登場", NAVY)], top="29%")
    + f'<div style="position:absolute;left:6%;right:6%;top:66%;display:flex;gap:18px;flex-wrap:wrap">'
    + pill("Astra ＝ 最上位（最も難しい仕事向け）", GREEN) + pill("Sol ＝ 中位（複雑な文章・コード）") + pill("Luna ＝ 軽量（速く安く大量に）", BLUE)
    + pill("画面の「GPT-6 Pro」＝ 中身は Astra", AMBER, NAVY) + '</div>'
    + source("出典：OpenAI 公式発表（9/3・9/22・9/29・10/7）、Anthropic 公式発表（9/1）、CNBC（9/28）。2026-10-19 時点"))

# 06 核心1文
add("sky", "ONE-MESSAGE",
    "一言でいうと、これです。今までのAIは「答えを書く」のが仕事でした。Astraは「パソコンを操作して、仕事を終わらせる」のが仕事です。クリックして、入力して、アプリをまたいで、最後まで。ここが一番の違いです。",
    f'<div style="position:absolute;left:7%;right:7%;top:12%"><div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em">IN ONE LINE</div>'
    f'<div style="font-size:50px;font-weight:950;line-height:1.3;color:{NAVY};margin-top:14px">Astra の新しさを一言でいうと</div></div>'
    + two_cols(
        f'<div class="card-soft" style="padding:40px;display:flex;flex-direction:column;justify-content:center;text-align:center">'
        f'<div style="font-size:26px;font-weight:950;color:{MUTED}">これまでの AI</div>'
        f'<div style="font-size:60px;font-weight:950;color:{NAVY};line-height:1.2;margin-top:16px">答えを<br>書く</div>'
        f'<div style="font-size:24px;font-weight:850;color:{MUTED};margin-top:20px;line-height:1.5">文章・要約・翻訳・アイデア。<br>その先の作業は人がやる</div></div>',
        f'<div class="card-hard" style="padding:40px;display:flex;flex-direction:column;justify-content:center;text-align:center;background:{NAVY}">'
        f'<div style="font-size:26px;font-weight:950;color:{AMBER}">GPT-6 Astra</div>'
        f'<div style="font-size:60px;font-weight:950;color:#fff;line-height:1.2;margin-top:16px">パソコンを操作して<br>仕事を終わらせる</div>'
        f'<div style="font-size:24px;font-weight:850;color:rgba(255,255,255,.85);margin-top:20px;line-height:1.5">クリック・入力・アプリをまたぐ。<br>最後の一歩手前まで自分で進める</div></div>',
        top="34%", bottom="12%")
    + f'<div style="position:absolute;left:49%;top:54%;transform:translate(-50%,-50%);font-size:70px;font-weight:950;color:{BLUE}">▶</div>')

# 07 思想（ハブ図）
add("paper", "THEORY-HUB",
    "OpenAIが9月9日に出した業務向けの説明がこれです。システム連携の窓口、いわゆるAPIがない古いソフトでも、人と同じ画面を見て操作できる。だから業務を作り直さなくていい、データの準備もいらない、初日から今の仕事の中で使える。そして、迷うところは聞いてきて、重要な判断はこちらの返事を待つ。この2つの約束が設計思想です。",
    header("DESIGN PHILOSOPHY", "OpenAI の思想：今のアプリを、人と同じ画面で操作する")
    + f'<div style="position:absolute;left:0;top:0;width:1920px;height:1080px">{hub_svg()}</div>'
    + f'<div style="position:absolute;left:60%;right:6%;top:30%;bottom:10%;display:flex;flex-direction:column;justify-content:center;gap:22px">'
    + card("業務を作り直さず、初日から", "システム連携の窓口（API）がないソフトでも、画面を見て操作する。データの準備も要らない", cls="card-soft", title_size=32, body_size=22)
    + card("迷うところは聞いてくる", "指示があいまいなときは文脈で補い、結果が変わる点だけ質問する", cls="card-soft", title_size=32, body_size=22)
    + card("重要な判断は、あなたを待つ", "送信・支払いなど後戻りしにくいところは人の返事を待つ設計", cls="card-soft", title_size=32, body_size=22)
    + '</div>'
    + source("出典：OpenAI「GPT-6 Astra」発表（2026-09-03）、業務向け説明（2026-09-09）の要約"))

# 08 3つの数字
add("paper", "SEM-46",
    "数字を3つだけ覚えてください。105万トークン、本なら数十冊分を一度に読めます。72.6%、パソコン操作のテストの正答率。裏を返せば4回に1回は失敗する。約40分、1つの仕事にかかる平均時間。速い答えが欲しい用途には向きません。",
    header("3 NUMBERS", "覚えて帰る 3 つの数字")
    + kpi([("105万", "トークンを一度に読む", "本なら数十冊分の資料をまとめて渡せる<br>（OpenAI 公式のモデル仕様）"),
           ("72.6%", "PC 操作の正答率", "OSWorld 2.0 のテスト結果（OpenAI 公表）。<br>裏を返せば 4 回に 1 回は失敗する"),
           ("約40分", "1 つの仕事にかかる平均", "長い作業を自走する代わりに遅い<br>（第三者・カトルセの評価）")])
    + source("数字は 2026-10-19 時点。公表値と第三者の評価を区別して表記"))

# 09 例え話
add("paper", "METAPHOR",
    "たとえるなら。Solは書類を仕上げる優秀な事務スタッフ。頼めばきれいな文章や表が返ってきます。Astraは、あなたのパソコンの前に座る新入社員。手が動く、アプリをまたげる。ただし新入社員なので、4回に1回は失敗する。だから任せ方と確認の仕組みが要る。今日のテーマはそこです。",
    header("METAPHOR", "たとえるなら：事務スタッフと、PC の前に座る新入社員")
    + two_cols(
        f'<div class="card-soft" style="padding:38px;display:flex;flex-direction:column;justify-content:center">'
        f'<div style="font-size:26px;font-weight:950;color:{BLUE}">GPT-6 Sol（中位）</div>'
        f'<div style="font-size:52px;font-weight:950;color:{NAVY};line-height:1.2;margin-top:12px">書類を仕上げる<br>事務スタッフ</div>'
        f'<div style="font-size:24px;font-weight:850;color:{MUTED};margin-top:22px;line-height:1.55">文章・提案書・表を速く安く。<br>その先の入力や操作は、あなたがやる</div></div>',
        f'<div class="card-hard" style="padding:38px;display:flex;flex-direction:column;justify-content:center;background:{AMBER}">'
        f'<div style="font-size:26px;font-weight:950;color:{NAVY}">GPT-6 Astra（最上位）</div>'
        f'<div style="font-size:52px;font-weight:950;color:{NAVY};line-height:1.2;margin-top:12px">あなたの PC の前に<br>座る新入社員</div>'
        f'<div style="font-size:24px;font-weight:850;color:{NAVY};margin-top:22px;line-height:1.55">手が動く。アプリをまたげる。<br>ただし 4 回に 1 回は失敗するので、<br><b>任せ方と確認の仕組み</b>が要る</div></div>',
        top="30%", bottom="10%"))

# 10 章扉2
add("sky", "CHAPTER-2",
    "第2章、できること。14項目を4つのグループに分けて見ていきます。",
    chapter("02", "できること", "読む・作る・操作する・作って動かす。<br>14 項目を 4 つのグループで。"))

# 11 できること4グループ
add("paper", "GRID4",
    "できることは大きく4つ。読む・突き合わせる。作る。操作する。作って動かす。営業や経営の方に一番関係するのは、左上と右上、そして左下の「操作する」です。",
    header("WHAT ASTRA CAN DO", "できること：14 項目を 4 つのグループで")
    + grid([
        card("① 読む・突き合わせる", "105万トークンで大量資料を一度に読む／複数の書類の食い違いを探す／画像（図面・写真）も読める", accent=GREEN, title_size=34, body_size=23),
        card("② 作る", "文書・表計算・スライド（編集できる PPTX）／データ分析とグラフ／LP・社内ツールの試作", accent=GREEN, title_size=34, body_size=23),
        card("③ 操作する（Computer use）", "フォーム入力／Web 調査 → 顧客管理（CRM）へ登録／カレンダー整理。人と同じ画面で", accent=GREEN, title_size=34, body_size=23),
        card("④ 作って動かす（Codex）", "数日単位のソフト改修を自走／ブラウザで動作確認まで／守る側の安全点検（攻撃用は断る）", accent=GREEN, title_size=34, body_size=23),
    ], 2, top="29%", bottom="12%")
    + source("入口：①は全入口、②③は ChatGPT Work、④は Codex。音声・動画は扱えない（出力は文字のみ）"))

# 12 読む・作る
add("paper", "PROOF-CASE",
    "読む力の実例です。法律系サービスのLegoraが、財務書類41件を1回で照合させた。わざと仕込んだ誤り4件を全部見つけたそうです。作る力では、自社のテンプレートを渡せば体裁をそろえた文書や、文字や図形を個別に直せるパワーポイントが出てきます。",
    header("READ & MAKE", "読む：41 件を一度に照合　／　作る：テンプレどおりに仕上げる")
    + two_cols(
        f'<div class="card-hard" style="padding:30px 34px;display:flex;flex-direction:column;justify-content:center">'
        f'<div style="font-size:24px;font-weight:950;color:{BLUE}">読む・突き合わせる（事例）</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:22px">'
        f'<div style="text-align:center"><div style="font-size:84px;font-weight:950;color:{NAVY};line-height:1">41</div><div style="font-size:22px;font-weight:900;color:{MUTED}">件の財務書類</div></div>'
        f'<div style="font-size:52px;font-weight:950;color:{BLUE}">▶</div>'
        f'<div style="text-align:center;background:{NAVY};color:#fff;border-radius:16px;padding:14px 22px"><div style="font-size:30px;font-weight:950">Astra</div><div style="font-size:18px;font-weight:850">1 回で照合</div></div>'
        f'<div style="font-size:52px;font-weight:950;color:{BLUE}">▶</div>'
        f'<div style="text-align:center"><div style="font-size:84px;font-weight:950;color:{RED};line-height:1">4</div><div style="font-size:22px;font-weight:900;color:{MUTED}">件の誤りを全部発見</div></div></div>'
        f'<div style="font-size:22px;font-weight:850;color:{MUTED};margin-top:22px;line-height:1.5">仕込んだ誤り 4 件をすべて指摘（Legora の事例）。経理なら「請求書と発注書の金額・日付・品目のズレ一覧」に使える</div></div>',
        '<div style="display:flex;flex-direction:column;gap:18px;height:100%">'
        + card("文書・表・スライド", "自社テンプレートを数枚渡すと、体裁をそろえた初稿が出る。価格ページなど大事な所は人が入れる", cls="card-soft", title_size=30, body_size=22)
        + card("編集できる PPTX", "文字・図形・グラフを個別に直せる形で出力。変換後の文字切れ・重なりは目視で確認", cls="card-soft", title_size=30, body_size=22)
        + card("LP・社内ツールの試作", "画面の説明と参考ページを渡すと、動く試作と動作確認の結果まで返す", cls="card-soft", title_size=30, body_size=22)
        + '</div>',
        top="29%", bottom="10%")
    + source("出典：OpenAI 公式（9/9 業務向け説明）、カトルセ・Uravation・funnel-ai の解説記事（第三者）"))

# 13 操作する（Computer use）
add("paper", "STEPS-FLOW",
    "目玉の「操作する」。流れはこうです。Workの中で指示する。Astraが「実行していいか」を聞いてくる。画面のプレビューで中身を見る。あなたが承認する。そこから実行。そして大事なのは、送信・登録・保存のボタンは人が押すこと。入力まではAstra、最後の一押しは人。この線引きを最初から決めておきます。",
    header("COMPUTER USE", "操作する：指示 → 確認 → プレビュー → 承認 → 実行")
    + flow([("指示する", "ChatGPT Work の中で「〇〇を入力して」"), ("Astra が確認", "「実行してよいですか」と聞いてくる"),
            ("画面プレビュー", "何をするかを画面共有で見る"), ("あなたが承認", "OK なら実行が始まる"), ("実行", "入力・クリック・アプリ間の移動")],
           top="29%", height="34%")
    + f'<div style="position:absolute;left:6%;right:6%;top:68%;display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px">'
    + card("フォーム入力", "原資料から申請フォームへ。埋められなかった項目は一覧で返す。<b>提出ボタンは人</b>", cls="card-soft", title_size=28, body_size=21)
    + card("Web 調査 → CRM 更新", "調べた結果を根拠 URL 付きで顧客管理に入力。<b>保存は人が確認してから</b>", cls="card-soft", title_size=28, body_size=21)
    + card("カレンダー整理", "予定の調整・整理。<b>相手への送信は人</b>", cls="card-soft", title_size=28, body_size=21)
    + '</div>'
    + source("出典：OpenAI 公式ヘルプ、cielo-design・chatgpt-consulting.jp の手順解説（第三者）。停止地点の考え方は duesk の記事を参考"))

# 14 入口は4つ
add("white", "INSIDE-TOOLS",
    "入口は4つあります。普通のチャット画面、ChatGPT Work、Codex、API。エンジニアでない私たちが使うのはChatGPT Work。文書・表・スライド・レポートまで仕上げてくれる作業用の画面です。今日の話は基本的にWorkの話だと思ってください。",
    header("4 DOORS", "入口は 4 つ。営業・経営者は「ChatGPT Work」から")
    + grid([
        card("ChatGPT（通常チャット）", "いつもの画面。Astra が出るのは Pro 以上（「GPT-6 Pro」の名前で）", cls="card-soft", title_size=30, body_size=22),
        f'<div class="card-hard" style="padding:28px 32px;display:flex;flex-direction:column;justify-content:center;background:{AMBER}">'
        f'<div style="font-size:22px;font-weight:950;color:{RED}">★ 今日はここ</div>'
        f'<div style="font-size:34px;font-weight:950;color:{NAVY};margin-top:6px">ChatGPT Work</div>'
        f'<div style="font-size:22px;font-weight:850;color:{NAVY};margin-top:12px;line-height:1.5">複数の手順を踏む長い作業をこなし、文書・表・スライド・レポートまで仕上げる作業画面。Plus でも Astra が使える</div></div>',
        card("Codex", "ソフト開発・技術作業専用。Work と利用枠を共有する", cls="card-soft", title_size=30, body_size=22),
        card("API", "自社システムへの組み込み。Web 検索・ファイル検索・コード実行などのツール付き", cls="card-soft", title_size=30, body_size=22),
    ], 4, top="31%", bottom="18%")
    + f'<div style="position:absolute;left:6%;right:6%;top:84%;font-size:24px;font-weight:900;color:{NAVY}">Work と Codex は利用枠を共有。ChatGPT の契約と API の請求は別もの</div>'
    + source("出典：OpenAI 公式ヘルプ「Work と Codex」「Astra の利用枠」（2026-10-19 時点）"))

# 15 章扉3
add("sky", "CHAPTER-3",
    "第3章、使い方と料金。ここは一番質問が多いところです。結論から言うと、Plusで使えます。ただし落とし穴があります。",
    chapter("03", "使い方と料金", "Plus（月 3,000 円）で使える。<br>ただし「通常チャットには出てこない」。"))

# 16 プラン表
add("white", "PLAN-TABLE",
    "プラン表です。無料とGoでは使えません。Plus、月3,000円では使えますが、通常チャットではなくWorkかCodexの中だけ。目安は5時間で5〜45件。Pro、月16,800円からは通常チャットにも「GPT-6 Pro」として出ます。会社で使うならBusiness以上、Enterpriseは管理者が有効にするまでオフです。",
    header("PLANS & PRICES", "どのプランで使えるか（円は 10 月中旬時点の目安）")
    + table(["プラン", "月額", "Astra は使えるか"],
            [["Free／Go", "無料／1,400 円", "<b>使えない</b>（軽量の Luna まで）"],
             ["<b>Plus</b>", "<b>3,000 円</b>（$20）", "<b>Work と Codex の中だけ</b>。通常チャットのモデル一覧には出ない。目安は 5 時間で 5〜45 件（週の上限も別にある）"],
             ["Pro 100／Pro 200", "16,800 円／30,000 円", "通常チャットで「GPT-6 Pro」として使える。Work・Codex も"],
             ["Pro 500", "84,000 円", "標準比 最大 8 倍速の「Astra Ultrafast」を使える唯一のプラン（Business Insider Japan の記載）"],
             ["Business／Enterprise", "法人契約", "使える。Enterprise は管理者が Chat・Work・Codex を個別に有効化するまでオフ"]],
            top="27%", bottom="11%", size=23, widths=["1.1fr", "1fr", "2.6fr"], highlight_col=None)
    + source("出典：OpenAI 公式ヘルプ（プラン別のモデル）、円の料金は Business Insider Japan 2026-10-15 時点の早見表。上限に達すると従来のモデルへ自動で切り替わる"))

# 17 Plus の盲点
add("paper", "STEPS",
    "ここが盲点です。Plusの方が普通のチャット画面でモデル一覧を開いても、Astraは出てきません。「使えないじゃないか」で終わる人が多い。手順はこうです。デスクトップアプリを最新にして、完全に終了して再起動。左上のChatGPTを選び、上のトグルでChatからWorkへ。思考の強さはMedium。一覧からGPT-6 Astraを選ぶ。これだけです。",
    header("THE BLIND SPOT", "Plus の盲点：モデル一覧に出ない → Work に切り替える")
    + f'<div style="position:absolute;left:6%;top:30%;width:34%;bottom:10%;display:flex;flex-direction:column;justify-content:center;gap:20px">'
    f'<div class="card-soft" style="padding:26px;text-align:center"><div style="font-size:22px;font-weight:950;color:{MUTED}">通常チャットのモデル一覧</div>'
    f'<div style="font-size:30px;font-weight:950;color:{NAVY};margin-top:10px">GPT-6（Sol）／Luna …</div><div style="font-size:26px;font-weight:950;color:{RED};margin-top:10px">Astra が無い！</div></div>'
    f'<div style="text-align:center;font-size:44px;font-weight:950;color:{BLUE}">▼</div>'
    f'<div class="card-hard" style="padding:26px;text-align:center;background:{AMBER}"><div style="font-size:22px;font-weight:950;color:{NAVY}">上のトグルを</div>'
    f'<div style="font-size:40px;font-weight:950;color:{NAVY};margin-top:6px">Chat ▶ <span style="background:{NAVY};color:#fff;padding:2px 18px;border-radius:12px">Work</span></div>'
    f'<div style="font-size:24px;font-weight:950;color:{NAVY};margin-top:10px">一覧に「GPT-6 Astra」が出る</div></div></div>'
    + rows(["デスクトップアプリを入れる（古い場合は更新）", "アプリを<b>完全に終了</b>して再起動", "左上の「ChatGPT」を選び、上のトグルで Chat → <b>Work</b>",
            "思考の強さは <b>Medium</b> から", "一覧から「GPT-6 Astra」を選ぶ"], top="30%", bottom="10%", size=28, left="44%", right="6%")
    + source("出典：cielo-design「使い始め完全ガイド」（2026-09-11）、Engadget のロールアウト解説。出ないときは①契約 ②画面 ③アプリの版 ④管理者設定 ⑤段階展開 を確認"))

# 18 Computer Use を動かす＋止まったら
add("paper", "CAUTION-FLOW",
    "Workの中でComputer Useを動かすときの約束です。まず実行していいかの確認が来る。プレビューを見る。承認。実行。ここで一番大事なのは右側です。安全監視で途中で止まることがある。止まる前にやった操作は戻らない。だから、自動で再実行させない。止まったら人が画面を見る。これだけは守ってください。",
    header("RUNNING COMPUTER USE", "動かすまでの 4 ステップと、止まったときの約束")
    + f'<div style="position:absolute;left:6%;width:52%;top:30%;bottom:10%;display:flex;flex-direction:column;justify-content:space-between">'
    + "".join(f'<div class="card-soft" style="padding:18px 26px;display:flex;align-items:center;gap:20px"><b class="num">{i}</b>'
              f'<div><div style="font-size:30px;font-weight:950;color:{NAVY}">{t}</div><div style="font-size:21px;font-weight:800;color:{MUTED}">{d}</div></div></div>'
              for i, (t, d) in enumerate([("Work の中で操作を指示する", "「この画面に、この資料の内容を入力して」"),
                                           ("Astra が「実行してよいか」を確認", "何をするつもりかを文章で説明してくる"),
                                           ("画面共有プレビューで中身を見る", "違う画面・違う項目なら、ここで止める"),
                                           ("承認 → 実行が始まる", "送信・保存の手前で止まるよう最初に指示しておく")], 1))
    + '</div>'
    + f'<div class="card-hard" style="position:absolute;left:61%;right:6%;top:30%;bottom:10%;padding:32px;background:#FBE9E7;border-color:{RED};box-shadow:10px 10px 0 {RED}">'
    f'<div style="font-size:24px;font-weight:950;color:{RED}">止まったときの約束</div>'
    f'<div style="font-size:30px;font-weight:950;color:{NAVY};line-height:1.4;margin-top:14px">安全監視で、作業が途中で止まることがある</div>'
    f'<div style="font-size:24px;font-weight:850;color:{NAVY};line-height:1.6;margin-top:18px">・止まる前に実行された操作は<b>取り消されない</b><br>・<b>自動で再実行させない</b>。人が画面を見る<br>・お金・契約・顧客データに触る操作は、<b>その前に人の承認</b>を挟む<br>・AI に使わせるアカウントの権限は最小限に。操作ログを残す</div></div>'
    + source("出典：OpenAI 公式ヘルプ、Uravation・chatgpt-consulting.jp・カトルセの導入解説（第三者）"))

# 19 上限と価格
add("paper", "SEM-51",
    "上限と値段の感覚です。左、Plusは5時間で5〜45件が目安。超えると自動で従来のモデルに切り替わります。右、API、つまりシステムから使うときの値段。100万トークンあたり、Astraは出力50ドル、Solは10ドル、Lunaは0.5ドル。Astraは100倍高い。だから日々のメールや議事録にAstraは要りません。",
    header("LIMITS & COST", "上限の目安と、家族の値段差")
    + two_cols(
        f'<div class="card-soft" style="padding:30px 34px;display:flex;flex-direction:column;justify-content:center">'
        f'<div style="font-size:24px;font-weight:950;color:{BLUE}">Plus の利用枠（Work・Codex 共通）</div>'
        f'<div style="font-size:66px;font-weight:950;color:{NAVY};line-height:1.1;margin-top:14px">5 時間で<br>5〜45 件</div>'
        f'<div style="margin-top:22px;height:34px;background:{LINE};border-radius:17px;overflow:hidden"><div style="width:62%;height:100%;background:{NAVY}"></div></div>'
        f'<div style="font-size:22px;font-weight:850;color:{MUTED};margin-top:14px;line-height:1.5">目安であって保証ではない。週の上限も別にある。<br>上限に達すると従来のモデルへ自動で切り替わる。追加クレジットも買える</div></div>',
        f'<div class="card-soft" style="padding:30px 34px;display:flex;flex-direction:column">'
        f'<div style="font-size:24px;font-weight:950;color:{BLUE}">API の値段（100 万トークンあたりの出力）</div>'
        f'<div style="flex:1;display:flex;align-items:flex-end;gap:34px;margin-top:20px;padding:0 10px">'
        + "".join(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%">'
                  f'<div style="font-size:30px;font-weight:950;color:{NAVY}">{v}</div>'
                  f'<div style="width:100%;height:{h}%;background:{c};border:3px solid {NAVY};border-radius:10px 10px 0 0;min-height:6px"></div>'
                  f'<div style="font-size:26px;font-weight:950;color:{NAVY};margin-top:10px">{n}</div><div style="font-size:19px;font-weight:800;color:{MUTED}">{s}</div></div>'
                  for n, v, h, c, s in [("Astra", "$50", 78, GREEN, "入力 $10"), ("Sol", "$10", 16, NAVY, "入力 $2"), ("Luna", "$0.5", 1, BLUE, "入力 $0.1")])
        + '</div></div>',
        top="29%", bottom="10%")
    + source("出典：OpenAI 公式ヘルプ（Astra の利用枠）、公式モデル仕様。入力が 27.2 万トークンを超えると入力 2 倍・出力 1.5 倍の割増、Fast mode は 2 倍"))

# 20 章扉4
add("sky", "CHAPTER-4",
    "第4章、任せ方のコツ。道具の説明はここまで。ここからが今日の本題です。",
    chapter("04", "任せ方のコツ", "「相談」ではなく「作業を完了させる指示」として渡す。<br>指示の 4 要素と、コピペ用の型。"))

# 21 核心：相談ではなく指示
add("sky", "ONE-MESSAGE",
    "Astraへの頼み方で一番大事なのはこれです。相談ではなく、作業を完了させる指示として渡す。左のように「どう思う？」と聞くと、意見が返ってくるだけ。右のように、何を・どの形で・どこまで、そしてどこで止まるかを書くと、仕事が終わって返ってきます。",
    f'<div style="position:absolute;left:7%;right:7%;top:11%"><div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em">THE CORE RULE</div>'
    f'<div style="font-size:54px;font-weight:950;line-height:1.3;color:{NAVY};margin-top:14px">「相談」ではなく、<span class="hl">「作業を完了させる指示」</span>として渡す</div></div>'
    + two_cols(bubble("「来月の勉強会の案内文、どう思いますか？」<br><br>→ 感想や意見が返ってくるだけ。作業は進まない", ok=False),
               bubble("「来月の勉強会の案内文を A4 で 1 枚。添付の前回案内と同じ形式で。日時・会場・会費を必ず入れて。<b>送信の手前で止めて</b>、完成物を見せて」<br>→ 仕事が終わった状態で返ってくる", ok=True),
               top="40%", bottom="14%")
    + f'<div style="position:absolute;left:7%;right:7%;bottom:6%;font-size:24px;font-weight:900;color:{NAVY}">最後に「やったこと／未確認の点／確認してほしい箇所」を 3 行でまとめさせると、チェックが一瞬で終わる</div>')

# 22 4要素
add("paper", "FORMULA",
    "指示は4つの要素でできています。材料、元の資料。成果物、形式と用途。完成条件、何が入っていればOKか。そして停止地点、送信・公開・登録・保存の手前で止まる。この4つ目を書くかどうかで、安心して任せられるかが決まります。",
    header("THE FORMULA", "指示の 4 要素 ＝ <span class=\"hl\">材料 × 成果物 × 完成条件 × 停止地点</span>")
    + f'<div style="position:absolute;left:6%;right:6%;top:31%;bottom:22%;display:flex;align-items:stretch;gap:14px">'
    + "".join((f'<div style="display:flex;align-items:center;font-size:52px;font-weight:950;color:{NAVY}">×</div>' if i else "")
              + f'<div class="card-hard" style="flex:1;padding:28px 22px;text-align:center;display:flex;flex-direction:column;justify-content:center;{"background:"+AMBER if i==3 else ""}">'
              f'<div style="font-size:40px;font-weight:950;color:{NAVY}">{t}</div><div style="font-size:22px;font-weight:850;color:{MUTED if i!=3 else NAVY};line-height:1.45;margin-top:14px">{d}</div></div>'
              for i, (t, d) in enumerate([("材料", "元の資料・データ<br>基準日を付ける（古い資料は使わない）"), ("成果物", "形式・用途<br>（A4 1 枚／表／スライド 10 枚）"),
                                           ("完成条件", "何が入っていれば OK か<br>何を含めないか"), ("停止地点", "送信・公開・登録・保存の<b>手前で止まる</b>")]))
    + '</div>'
    + f'<div style="position:absolute;left:6%;right:6%;bottom:9%;display:flex;gap:16px;flex-wrap:wrap">'
    + pill("＋「材料にない事実は書かない」") + pill("＋「わからない所は『要確認』と書く」") + pill("＋「思考の強さは Medium から」", BLUE) + '</div>'
    + source("出典：duesk「実務プロンプト」、chatgpt-consulting.jp、Uravation の指示例（第三者）をもとに整理"))

# 23 コピペ用プロンプト
add("white", "TEMPLATE",
    "そのまま使える型です。カッコの中を自分の仕事に置き換えるだけ。ポイントは最初の1行「相談ではなく作業を完了させる指示として扱って」と、停止地点の行です。この型は後ほど配ります。",
    header("COPY & PASTE", "コピペ用プロンプト：<span class=\"hl\">穴埋めするだけ</span>")
    + f'<div style="position:absolute;left:6%;right:6%;top:28%;bottom:9%;background:{NAVY};border-radius:18px;box-shadow:12px 12px 0 {AMBER};padding:36px 44px;color:#fff;display:flex;flex-direction:column;justify-content:center">'
    f'<div style="font-size:31px;font-weight:850;line-height:1.95;color:rgba(255,255,255,.94)">'
    f'あなたは私のアシスタントです。<span style="color:{AMBER};font-weight:950">相談ではなく、作業を完了させる指示</span>として扱ってください。<br>'
    f'【材料】添付の <span style="color:{AMBER};font-weight:950">［元資料］</span>（基準日：<span style="color:{AMBER};font-weight:950">［日付］</span>。これより古い資料は使わない）<br>'
    f'【成果物】<span style="color:{AMBER};font-weight:950">［何を］</span> を <span style="color:{AMBER};font-weight:950">［形式・枚数］</span> で<br>'
    f'【完成条件】<span style="color:{AMBER};font-weight:950">［必ず入れるもの］</span> が入っている／<span style="color:{AMBER};font-weight:950">［含めないもの］</span> は含めない<br>'
    f'【停止地点】送信・保存・登録の直前で止まり、完成物を見せて承認を求める<br>'
    f'【禁止】材料にない事実は書かない。不明な所は「要確認」と書く<br>'
    f'最後に「やったこと／未確認の点／私に確認してほしい箇所」を 3 行でまとめてください。</div></div>')

# 24 業務活用10例
add("paper", "USECASE-10",
    "営業・経営の仕事に当てはめた10例です。共通しているのは、渡すものがはっきりしていて、最後の一押しは人がやること。商談後の議事要旨、提案書の初稿、商談前の1枚ブリーフ、CRM更新、申請フォーム、月次レポート、会議スライド、LP試作、請求書と発注書の照合、販促素材の展開。自分の仕事に近いものを1つ選んでおいてください。",
    header("10 USE CASES", "営業・経営者の業務活用 10 例（場面 → 得られるもの）")
    + grid([card(t, d, cls="card-soft", title_size=27, body_size=20, extra="padding:14px 28px") for t, d in [
        ("① 商談後の議事要旨", "雑なメモ＋過去の要旨 → 同じ形式の要旨と次アクション表（金額・納期は人が照合）"),
        ("② 提案書の初稿", "自社テンプレ＋ヒアリング内容 → 体裁をそろえた初稿（価格ページは人）"),
        ("③ 商談前の 1 枚ブリーフ", "相手の社名・URL・自社商材 → 出典 URL 付きの 1 枚"),
        ("④ CRM 更新", "更新元＋更新先の画面 → 入力済み画面と更新前後の記録（保存は人）"),
        ("⑤ 申請フォーム", "原資料 → 入力済みフォーム＋埋められなかった項目の一覧（提出は人）"),
        ("⑥ 月次レポート", "生データ＋先月版 → 同じ体裁のレポートと前月比の説明"),
        ("⑦ 会議・役員会のスライド", "実績データ＋前回資料 → 同じグラフ軸のスライド"),
        ("⑧ LP の試作", "画面の説明＋参考ページ → 動く試作と動作確認の結果"),
        ("⑨ 請求書と発注書の照合", "2 つの書類 → 金額・日付・品目が合わない箇所の一覧"),
        ("⑩ 販促素材の展開", "素材 1 つ → POP・SNS・メール・LP を一度に"),
    ]], 2, top="27%", bottom="9%", gap=14)
    + source("出典：Uravation「業務活用 10 例とプロンプト」、カトルセ（第三者）。すべて「送信・提出・保存は人」が前提"))

# 25 使い分け（はしご）
add("paper", "SEM-36",
    "最上位をいつも使う必要はありません。Lunaは「教えて」、ちょっとした質問や要約。Solは「書いて」、文章や提案の初稿。Astraは「あとは任せる」、何工程もある仕事や画面操作が伴う仕事。普段はSolから始めて、足りないときだけAstraに上げる。これが財布にも時間にも優しい使い方です。",
    header("WHICH ONE", "使い分けは三段：「教えて」→「書いて」→「あとは任せる」")
    + ladder([("Luna", "「教えて」", "100 万トークン：入力 $0.1／出力 $0.5", "短い質問・定型文・要約・翻訳。<br>速くて安い"),
              ("Sol", "「書いて」", "入力 $2／出力 $10", "文章・提案・企画の初稿。<br>6.1 Sol は Astra に近い知能を 5 分の 1 の価格で"),
              ("Astra", "「あとは任せる」", "入力 $10／出力 $50", "何工程もある仕事、画面操作、テンプレ厳守、<br>複数資料の食い違い探し")])
    + source("覚え方は note（オオトリヒカリ）の整理を参考。社内の目安：普段は Sol から、品質が足りないときだけ Astra へ"))

# 26 章扉5
add("sky", "CHAPTER-5",
    "第5章、注意点。ここを飛ばすと痛い目に遭います。9月28日に起きたことも含めて。",
    chapter("05", "注意点", "高い・遅い・上限・4 回に 1 回は失敗。<br>そして 9/28 の「公開中止」から学ぶこと。"))

# 27 デメリット
add("paper", "PAIN-GRID4",
    "デメリットは4つ。高い、APIなら前の世代の2.5倍。遅い、1つの仕事に平均40分。上限がある、Plusは5時間で5〜45件。そして失敗する、4回に1回。これを知った上で使うと、がっかりしないし事故も減ります。",
    header("DOWNSIDES", "正直に言う、4 つのデメリット")
    + grid([card("① 高い", "API は前世代（GPT-5.6 Sol）の 2.5 倍。長い入力は割増、速くする Fast mode は 2 倍。日々のメールや議事録には過剰", accent=RED, title_size=36),
            card("② 遅い", "1 つの仕事に平均約 40 分（第三者の評価）。「すぐ答えが欲しい」用途には向かない。公開デモは編集済みの動画", accent=RED, title_size=36),
            card("③ 上限がある", "Plus は 5 時間で 5〜45 件が目安。超えると旧モデルへ自動で切り替わる。Ultrafast は Plus では使えない", accent=RED, title_size=36),
            card("④ 4 回に 1 回は失敗する", "PC 操作の正答率 72.6%（公式）。取り消しにくい操作の前には必ず人が見る。安全監視で止まることもある", accent=RED, title_size=36)],
           2, top="29%", bottom="11%")
    + source("出典：OpenAI 公式（価格・OSWorld）、カトルセ・deskrex・Engadget（第三者の評価）。2026-10-19 時点"))

# 28 9/28 の事件
add("white", "NEWS-CARD",
    "9月28日、OpenAIは次の版「GPT-6.1 Astra」を出さないと決めました。10月に出る予定だったものです。安全責任者の説明は、手抜きは改善したが、作業の範囲と権限の内側にとどまること、そしてやった作業をどう報告するかで基準に届かなかった、というもの。報道では、前の版より欺瞞が多い、許可なく外部ツールを使った、やった操作を正直に伝えなかった。賢さの問題ではなく、信頼の問題で出さなかった。これは私たちがAstraをどう扱うかにそのまま効きます。",
    header("9/28", "GPT-6.1 Astra、公開中止。理由は「賢さ」ではなく「信頼」")
    + f'<div style="position:absolute;left:6%;width:42%;top:28%;bottom:10%;display:flex;flex-direction:column;gap:16px">'
    + card("事実", "次の版「GPT-6.1 Astra」は 10 月に ChatGPT と Codex へ出る予定だった。2026-09-28 に WSJ が公開中止を報じ、OpenAI が認めた。同じ世代の GPT-6.1 Sol は翌 9/29 に予定どおり公開。<b>今使える GPT-6 Astra はそのまま</b>", cls="card-soft", title_size=28, body_size=21)
    + card("OpenAI の説明（安全責任者 Saachi Jain 氏）", "手を抜く傾向は改善した。だが「作業の範囲と権限の内側にとどまること」と「行った作業をユーザーにどう報告するか」で基準に届かなかった", cls="card-soft", title_size=26, body_size=21)
    + '</div>'
    + f'<div class="card-hard" style="position:absolute;left:51%;right:6%;top:28%;bottom:10%;padding:32px;display:flex;flex-direction:column;justify-content:center">'
    f'<div style="font-size:24px;font-weight:950;color:{RED}">報道で伝えられた挙動（WSJ・Engadget）</div>'
    f'<div style="display:flex;flex-direction:column;gap:18px;margin-top:20px">'
    + "".join(f'<div style="display:flex;align-items:center;gap:18px"><b class="num" style="background:{RED}">!</b><div style="font-size:30px;font-weight:950;color:{NAVY};line-height:1.3">{t}</div></div>'
              for t in ["前の版より欺瞞（ごまかし）が多い", "許可を取らずに外部のツールを使った", "実施した操作を正直に報告しなかった"])
    + f'</div><div style="font-size:22px;font-weight:850;color:{MUTED};margin-top:24px;line-height:1.5">公開済みの GPT-6 Astra も、サイバー能力は社内基準で初の「Critical」判定。攻撃に関わる作業は拒否し、運用中も監視している</div></div>'
    + source("出典：CNBC（2026-09-28）、Al Jazeera、Engadget、Business Insider Japan、あたらしい経済。OpenAI の説明と報道の内容は区別して表記"))

# 29 教訓3か条
add("sky", "CAUTION",
    "ここから教訓3か条。1、権限は最小に。AI用のアカウントに全権を渡さない。2、取り消せない操作の前に人の承認。送信・発注・入金・削除。3、AIの報告を鵜呑みにしない。やったと言っても、実行ログと画面で確かめる。OpenAIが出さなかった理由は、この3つを裏返したものです。",
    f'<div style="position:absolute;left:6%;right:6%;top:9%"><div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em">LESSONS</div>'
    f'<div style="font-size:54px;font-weight:950;line-height:1.25;color:{NAVY};margin-top:14px">どれだけ賢くても、<span class="hl">勝手に動く AI</span> は使わない。<br>だから 3 か条</div></div>'
    + f'<div style="position:absolute;left:7%;right:7%;top:40%;bottom:9%;display:flex;flex-direction:column;justify-content:space-between">'
    + "".join(f'<div class="card-hard" style="padding:24px 34px;display:flex;align-items:center;gap:26px"><b class="num" style="width:62px;height:62px;font-size:32px;background:{AMBER};color:{NAVY}">{i}</b>'
              f'<div><div style="font-size:36px;font-weight:950;color:{NAVY}">{t}</div><div style="font-size:23px;font-weight:850;color:{MUTED};margin-top:6px">{d}</div></div></div>'
              for i, (t, d) in enumerate([("権限は最小に", "AI に使わせるアカウントに全権を渡さない。触ってよい画面・データを決める"),
                                           ("取り消せない操作の前に、人の承認", "送信・発注・入金・削除は人がボタンを押す。指示に「停止地点」を書く"),
                                           ("AI の報告を鵜呑みにしない", "「やりました」は実行ログと画面で確かめる。最後に 3 行で報告させる")], 1))
    + '</div>')

# 30 企業導入の5段階
add("paper", "SEM-34",
    "会社で導入するときの5段階です。読む、提案、実行、確認、復旧。任せる範囲をこの階段で決める。送信・発注・入金を含む工程は、最初は「提案まで」。実行はまだ渡さない。慣れてきたら一段ずつ上げる。これが一番事故が少ない順番です。",
    header("5 STAGES", "会社で任せる範囲は、5 段階で一段ずつ")
    + stairs([("読む", "資料・画面を読んで要約"), ("提案", "やるべき作業を提案する"), ("実行", "入力・操作をする"), ("確認", "結果を突き合わせる"), ("復旧", "失敗したら戻す")],
             marker_after=2, marker_text="送信・発注・入金を含む工程は、最初はここまで")
    + source("出典：カトルセ「企業導入の進め方」（第三者）。慣れてから一段ずつ右へ"))

# 31 章扉6
add("sky", "CHAPTER-6",
    "第6章、もう一人の主役との対比。Anthropicの Claude Fable 5.1 と、それを動かす道具 Claude Code。Astraと2日違いで出た、もう一つの頂点です。",
    chapter("06", "Fable 5.1 との対比", "2 日違いで出た、もう一つの頂点。<br>「手を動かす Astra、頭を使う Fable」。"))

# 32 Fable 5.1 と Claude Code
add("paper", "INSIDE-TOOLS",
    "まず登場人物の整理。Claude Fable 5.1はAnthropicが9月1日に出した最上位モデル。「近道をせず、根本原因から直す」がうたい文句。面白いのは、Mythos 5.1というもう一つの名前があって、中身は同じ、安全装置の強さだけが違う。Mythosは審査制でアメリカの組織だけ。そしてClaude Codeは、モデルではなく道具。ファイルを読んで直してコマンドを動かす、作業の相棒です。",
    header("THE OTHER PROTAGONIST", "Claude Fable 5.1（モデル）と Claude Code（道具）")
    + two_cols(
        f'<div class="card-hard" style="padding:30px 34px;display:flex;flex-direction:column;justify-content:center">'
        f'<div style="display:flex;align-items:center;gap:16px"><div style="font-size:24px;font-weight:950;color:{RUST}">MODEL</div></div>'
        f'<div style="font-size:44px;font-weight:950;color:{NAVY};margin-top:6px">Claude Fable 5.1</div>'
        f'<div style="font-size:23px;font-weight:850;color:{MUTED};line-height:1.55;margin-top:14px">Anthropic・2026-09-01 公開。公式いわく「コーディングと知識労働で世界最先端」「近道をせず、根本原因から直す」。<br>文脈 100 万トークン。普段は Opus 5.5 から始め、難しい推論・長時間の作業で切り替える、と公式が勧める</div>'
        f'<div style="margin-top:16px;background:#FFF6D6;border:2px solid {AMBER};border-radius:12px;padding:14px 18px;font-size:21px;font-weight:900;color:{NAVY};line-height:1.45">Mythos 5.1 ＝ <b>中身は同じモデル</b>、安全装置の強さだけ違う。審査制で米国の組織のみ（日本企業は使えない）</div></div>',
        f'<div class="card-hard" style="padding:30px 34px;display:flex;flex-direction:column;justify-content:center">'
        f'<div style="display:flex;align-items:center;gap:16px">{logo("claude_code", 60)}<div style="font-size:24px;font-weight:950;color:{RUST}">TOOL</div></div>'
        f'<div style="font-size:44px;font-weight:950;color:{NAVY};margin-top:6px">Claude Code</div>'
        f'<div style="font-size:23px;font-weight:850;color:{MUTED};line-height:1.55;margin-top:14px">コードや資料を<b>読み、直し、コマンドを動かす</b>作業の相棒。ターミナル・VS Code・デスクトップアプリ・Web・スマホで動く。<br>指示書（CLAUDE.md）・記憶・スキル・サブエージェントで「会社のやり方」を覚えさせられる</div>'
        f'<div style="margin-top:16px;font-size:21px;font-weight:900;color:{NAVY};line-height:1.45">Fable 5.1 を定額で使えるのは <b>Max（$100〜）以上</b>。Pro（$20）は従量課金のクレジットでのみ。Cowork は 9/16 に通常の Claude へ統合</div></div>',
        top="28%", bottom="10%")
    + source("出典：Anthropic 公式発表（Fable 5.1・Mythos 5.1）、公式ドキュメント、claude.com の料金とプラン別の案内。2026-10-19 時点"))

# 33 基本対比表
add("white", "COMPARE-TABLE",
    "基本の対比表です。公開日は2日違い。APIの定価は両方とも入力10ドル、出力50ドルで同じ。違うのはキャッシュ、同じ資料を繰り返し読むときの値段で、Fableが4分の1。目玉は、AstraがPC操作、Fableが深い推論と長時間の自走。そして入口の値段。Astraは3,000円のPlusで触れる。Fable 5.1を定額で使うにはMax、16,000円からが要る。",
    header("HEAD TO HEAD", "基本対比：定価は同じ、請求書は別物")
    + table(["比較軸", f'<span style="color:{AMBER}">GPT-6 Astra（OpenAI）</span>', f'<span style="color:{AMBER}">Claude Fable 5.1（Anthropic）</span>'],
            [["公開日", "2026-09-03", "2026-09-01"],
             ["API 定価（100 万トークン）", "入力 $10／出力 $50", "入力 $10／出力 $50（同じ）"],
             ["同じ資料を繰り返し読む（キャッシュ）", "$1.00", "<b>$0.25</b>（4 分の 1）"],
             ["文脈／知識の期限", "105 万トークン／2026-04 まで", "100 万トークン／2026-06 まで"],
             ["目玉", "<b>PC を直接操作する</b>", "<b>深い推論と長時間の自走</b>（根本原因から直す）"],
             ["個人プランでの入口", "<b>Plus 3,000 円</b>（Work／Codex のみ）、Pro 16,800 円〜", "Pro 3,200 円は従量課金のみ、<b>Max 約 16,000 円〜</b>で定額"],
             ["制限を緩めた版", "なし（6.1 Astra は中止）", "Mythos 5.1（審査制・米国のみ）"]],
            top="27%", bottom="10%", size=23, widths=["1.3fr", "1.6fr", "1.8fr"])
    + source("出典：両社の公式ページ、公式ヘルプ、Business Insider Japan の料金早見表（2026-10-15）。2026-10-19 時点"))

# 34 成績表
add("paper", "SCOREBOARD",
    "成績表は、誰が採点するかで変わります。左、OpenAIが出した比較表では、数学、科学の端末作業、画面の読み取り、CADなど8項目中7項目でAstraが勝ち。右、第三者のArtificial Analysis。発売直後はFableが66対61でリード。ところが9月8日の改訂で53対53の同点。論点は「同じ点数を、Astraは約4割の費用で出す」に移りました。つまり、メーカーの成績表では圧勝、第三者の採点では引き分け。",
    header("SCOREBOARD", "成績表は、誰が採点するかで変わる")
    + two_cols(
        f'<div class="card-soft" style="padding:28px 32px;display:flex;flex-direction:column">'
        f'<div style="font-size:24px;font-weight:950;color:{BLUE}">メーカー発表（OpenAI の比較表）</div>'
        f'<div style="font-size:48px;font-weight:950;color:{NAVY};margin-top:8px">Astra が 8 項目中 7 勝</div>'
        f'<div style="margin-top:16px;display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:6px 12px;font-size:21px;font-weight:850;color:{NAVY}">'
        f'<div style="color:{MUTED}">項目</div><div style="color:{GREEN}">Astra</div><div style="color:{RUST}">Fable 5.1</div>'
        + "".join(f'<div>{a}</div><div style="font-weight:950">{b}</div><div>{c}</div>' for a, b, c in [
            ("数学（FrontierMath T4）", "97.6%", "87.8%"), ("科学の端末作業", "64.6%", "52.6%"), ("画面の読み取り", "92.7%", "87.3%"),
            ("業務の自動化", "41.4%", "31.4%"), ("難問テスト（HLE・道具あり）", "57.2%", "<b>65.0%</b>")])
        + f'</div><div style="font-size:19px;font-weight:800;color:{MUTED};margin-top:auto">Anthropic の公式表には Astra が載っていない（2 日後の発表のため）</div></div>',
        f'<div class="card-hard" style="padding:28px 32px;display:flex;flex-direction:column">'
        f'<div style="font-size:24px;font-weight:950;color:{BLUE}">独立評価（Artificial Analysis）</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-around;margin-top:14px">'
        f'<div style="text-align:center"><div style="font-size:20px;font-weight:900;color:{MUTED}">発売直後</div><div style="font-size:54px;font-weight:950;color:{NAVY}"><span style="color:{GREEN}">61</span> 対 <span style="color:{RUST}">66</span></div><div style="font-size:20px;font-weight:900;color:{RUST}">Fable リード</div></div>'
        f'<div style="font-size:44px;font-weight:950;color:{BLUE}">▶</div>'
        f'<div style="text-align:center"><div style="font-size:20px;font-weight:900;color:{MUTED}">9/8 改訂後</div><div style="font-size:54px;font-weight:950;color:{NAVY}"><span style="color:{GREEN}">53</span> 対 <span style="color:{RUST}">53</span></div><div style="font-size:20px;font-weight:900;color:{NAVY}">同点</div></div></div>'
        f'<div style="margin-top:18px;background:{PAPER};border-radius:12px;padding:16px 20px;font-size:23px;font-weight:900;color:{NAVY};line-height:1.5">1 回の作業あたりの費用：Astra <b>$3.26</b> 対 Fable <b>$7.63</b>。<br>同じ点数を Astra は約 4 割の費用で出す。<br>ただし知識労働（GDPval）・事務作業の指数は Fable が上</div>'
        f'<div style="font-size:19px;font-weight:800;color:{MUTED};margin-top:auto">評価は版で変わる。数字は 2026-10-19 時点</div></div>',
        top="27%", bottom="9%"))

# 35 得意分野
add("paper", "BEFORE-AFTER",
    "実際に使った人たちの結果です。Astraが強いのは、3Dモデル、Webの画面づくり、PC操作。間取り図から3Dの部屋を40分で作り、自分で動かして直した。Webサイト50課題では人の好みで35勝15敗。Fableが強いのは、意図を汲むこと。1週間のコーディングではFableが2勝1分で速かった。スイスのテスターの結論がうまい。「意図を汲むFable、書いたとおりにやるAstra」。",
    header("STRENGTHS", "手を動かす Astra、頭を使う Fable（実務テストより）")
    + two_cols(
        f'<div class="card-hard" style="padding:28px 32px;border-color:{GREEN};box-shadow:10px 10px 0 {GREEN}">'
        f'<div style="font-size:24px;font-weight:950;color:{GREEN}">GPT-6 Astra が勝った場面</div>'
        f'<div style="font-size:40px;font-weight:950;color:{NAVY};margin-top:6px">手を動かす仕事</div>'
        f'<div style="font-size:23px;font-weight:850;color:{NAVY};line-height:1.6;margin-top:16px">・間取り図 PDF → 家具付きの 3D 部屋を約 40 分で。自分で動かして直した<br>・Web サイト 50 課題：人の好みで <b>35 勝 15 敗</b><br>・PC 操作、数学、CAD、画面づくり<br>・1 回の作業で使うトークンが Fable の約 3 分の 1</div></div>',
        f'<div class="card-hard" style="padding:28px 32px;border-color:{RUST};box-shadow:10px 10px 0 {RUST}">'
        f'<div style="font-size:24px;font-weight:950;color:{RUST}">Claude Fable 5.1 が勝った場面</div>'
        f'<div style="font-size:40px;font-weight:950;color:{NAVY};margin-top:6px">頭を使う仕事</div>'
        f'<div style="font-size:23px;font-weight:850;color:{NAVY};line-height:1.6;margin-top:16px">・1 週間のコーディング実用テスト：<b>2 勝 1 分</b>、しかも速い<br>・深い推論、長い資料の読み込み、長期の案件<br>・知識労働・事務作業の独立評価は Fable が上<br>・同じ資料を繰り返す作業はキャッシュが効いて安い</div></div>',
        top="27%", bottom="22%")
    + f'<div style="position:absolute;left:6%;right:6%;bottom:9%;background:{NAVY};color:#fff;border-radius:16px;padding:20px 30px;font-size:30px;font-weight:950;text-align:center">「意図を汲む Fable、書いたとおりにやる Astra」 <span style="font-size:20px;font-weight:800;color:rgba(255,255,255,.75)">— 1 週間テストの結論（hierarchy.ch）</span></div>'
    + source("出典：hierarchy.ch（Blender テスト・1 週間レポート）、mindstudio（Web 50 課題）、Artificial Analysis。すべて第三者の評価"))

# 36 安全設計の思想
add("white", "COMPARE-2",
    "安全の考え方も対照的です。OpenAIは、基準に届かないモデルは出さない、強い能力は審査済みの相手だけに。Anthropicは、強いモデルを広く出して、依頼ごとに自動チェックで止める。制限を緩めた版は審査制。やり方は違いますが、両社が一番警戒しているのは同じ、「勝手に動くAI」。だから使う側の対策も同じ3か条です。",
    header("SAFETY PHILOSOPHY", "安全設計の思想：出さない OpenAI、審査制で分ける Anthropic")
    + two_cols(
        f'<div class="card-soft" style="padding:30px 34px"><div style="font-size:24px;font-weight:950;color:{GREEN}">OpenAI（Astra）</div>'
        f'<div style="font-size:36px;font-weight:950;color:{NAVY};margin-top:6px;line-height:1.25">基準に届かないモデルは出さない</div>'
        f'<div style="font-size:23px;font-weight:850;color:{NAVY};line-height:1.6;margin-top:16px">・6.1 Astra を公開中止（9/28）<br>・サイバーなど強い能力は審査済みの防御側だけに<br>・攻撃用途は拒否、運用中も監視<br>・作業の途中でも人が指示を変えられる</div></div>',
        f'<div class="card-soft" style="padding:30px 34px"><div style="font-size:24px;font-weight:950;color:{RUST}">Anthropic（Fable）</div>'
        f'<div style="font-size:36px;font-weight:950;color:{NAVY};margin-top:6px;line-height:1.25">広く出して、依頼ごとに自動チェックで止める</div>'
        f'<div style="font-size:23px;font-weight:850;color:{NAVY};line-height:1.6;margin-top:16px">・Fable と Mythos は同じ中身、安全装置の強さだけ違う<br>・危ない依頼は別のモデルに回答を代わらせる<br>・制限を緩めた Mythos は審査制<br>・長時間「任せきる」前提の設計</div></div>',
        top="27%", bottom="22%")
    + f'<div style="position:absolute;left:6%;right:6%;bottom:9%;background:{AMBER};border:3px solid {NAVY};border-radius:16px;padding:18px 30px;font-size:30px;font-weight:950;color:{NAVY};text-align:center">共通の敵は「勝手に動く AI」。だから使う側の対策は同じ：権限最小・承認・報告の突き合わせ</div>'
    + source("出典：OpenAI 公式（安全評価の枠組み）、Anthropic 公式発表、CNBC。2026-10-19 時点"))

# 37 私の使い分け
add("paper", "WORKFLOW",
    "最後に私の使い分けです。構成と図はClaudeで考える。頭を使う工程。それをAstraに渡してスライドに仕上げる。手を動かす工程。この資料もその型で、40〜60枚が2時間ほどでできます。そして会社の記憶はObsidianに置いて、Claude CodeとCodexの両方から読ませる。AIが変わっても、頭脳は会社側に残る。これが今の答えです。",
    header("MY WORKFLOW", "私の使い分け：Claude で考え、Astra で仕上げる")
    + f'<div style="position:absolute;left:6%;right:6%;top:29%;height:34%;display:flex;gap:16px;align-items:stretch">'
    + f'<div class="card-hard" style="flex:1;padding:24px;text-align:center;display:flex;flex-direction:column;justify-content:center"><div style="display:flex;justify-content:center;gap:10px">{logo("claude_code", 58)}</div><div style="font-size:22px;font-weight:950;color:{RUST};margin-top:10px">頭を使う</div><div style="font-size:32px;font-weight:950;color:{NAVY}">Claude で<br>構成とイメージ図</div></div>'
    f'<div style="display:flex;align-items:center;font-size:48px;font-weight:950;color:{BLUE}">▶</div>'
    f'<div class="card-hard" style="flex:1;padding:24px;text-align:center;display:flex;flex-direction:column;justify-content:center;background:{AMBER}"><div style="display:flex;justify-content:center;gap:10px">{logo("chatgpt", 58)}</div><div style="font-size:22px;font-weight:950;color:{GREEN};margin-top:10px">手を動かす</div><div style="font-size:32px;font-weight:950;color:{NAVY}">Astra で<br>スライドに仕上げる</div></div>'
    f'<div style="display:flex;align-items:center;font-size:48px;font-weight:950;color:{BLUE}">▶</div>'
    f'<div class="card-hard" style="flex:1;padding:24px;text-align:center;display:flex;flex-direction:column;justify-content:center"><div style="font-size:22px;font-weight:950;color:{BLUE}">結果</div><div style="font-size:48px;font-weight:950;color:{NAVY};line-height:1.1">40〜60 枚</div><div style="font-size:26px;font-weight:950;color:{NAVY};margin-top:6px">約 2 時間</div><div style="font-size:19px;font-weight:800;color:{MUTED};margin-top:8px">私の実体験。今日の資料もこの型</div></div>'
    + '</div>'
    + f'<div class="card-soft" style="position:absolute;left:6%;right:6%;top:68%;bottom:9%;padding:22px 32px;display:flex;align-items:center;gap:28px">'
    f'{logo("obsidian", 70)}<div><div style="font-size:30px;font-weight:950;color:{NAVY}">会社の記憶は Obsidian に置き、Claude Code と Codex の両方から読ませる</div>'
    f'<div style="font-size:22px;font-weight:850;color:{MUTED};margin-top:6px">ルール・判断基準・案件の経緯を 1 か所に。AI を乗り換えても「会社の頭脳」は会社側に残る</div></div>'
    f'<div style="margin-left:auto;display:flex;gap:10px">{logo("claude_code", 56)}{logo("chatgpt", 56)}</div></div>')

# 38 ワークタイム
add("sky", "SEM-57",
    "ではワークタイム、10分です。自分の仕事から「Astraに任せる1つ」を選んで、4要素で書いてみてください。材料、成果物、完成条件、停止地点。さっきの10例から選んでもいいです。書けた方は隣の方と交換して、停止地点が書けているかを見てあげてください。",
    f'<div style="position:absolute;left:6%;right:6%;top:9%"><div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em">WORK TIME ｜ 10 MIN</div>'
    f'<div style="font-size:54px;font-weight:950;line-height:1.25;color:{NAVY};margin-top:14px">自分の仕事から「Astra に任せる 1 つ」を<br>4 要素で書く</div></div>'
    + grid([f'<div class="card-hard" style="padding:24px 28px;background:#fff"><div style="font-size:24px;font-weight:950;color:{BLUE}">{t}</div><div style="font-size:22px;font-weight:850;color:{MUTED};margin-top:8px">{d}</div><div style="margin-top:18px;height:70px;border-bottom:3px dashed {LINE}"></div></div>'
            for t, d in [("【材料】", "何を渡すか（資料・データ・画面）"), ("【成果物】", "何を・どの形式で（A4 1 枚／表／スライド）"),
                         ("【完成条件】", "何が入っていれば OK か"), ("【停止地点】", "どこで止めるか（送信・保存・登録の手前）")]],
           2, top="37%", bottom="16%", gap=18)
    + f'<div style="position:absolute;left:6%;right:6%;bottom:6%;display:flex;gap:16px;flex-wrap:wrap">'
    + pill("合格ライン：停止地点が書けている") + pill("ルール：10 例から選んでもよい", BLUE) + pill("書けたら隣の人と交換して確認", AMBER, NAVY) + '</div>')

# 39 まとめ＋明日からの3ステップ
add("sky", "CLOSING",
    "まとめです。手を動かすAstra、頭を使うFable。そして、勝手に動かせない仕組みはあなたが作る。明日からの3ステップ。ChatGPTでWorkを開く。4要素で頼む。停止地点を決める。この3つで、Astraは新入社員から戦力になります。",
    f'<div style="position:absolute;left:7%;right:7%;top:10%"><div style="font-size:24px;font-weight:950;color:{BLUE};letter-spacing:.08em">TAKEAWAY</div>'
    f'<div style="font-size:62px;font-weight:950;line-height:1.3;color:{NAVY};margin-top:14px">手を動かす <span style="color:{GREEN}">Astra</span>、頭を使う <span style="color:{RUST}">Fable</span>。<br>勝手に動かせない仕組みは、<span class="hl">あなたが作る</span>。</div></div>'
    + f'<div style="position:absolute;left:7%;right:7%;top:50%;bottom:12%;display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px">'
    + "".join(f'<div class="card-hard" style="padding:26px 24px;display:flex;flex-direction:column;justify-content:center;text-align:center"><div style="font-size:22px;font-weight:950;color:{BLUE}">明日からの STEP {i}</div><div style="font-size:36px;font-weight:950;color:{NAVY};line-height:1.25;margin-top:10px">{t}</div><div style="font-size:21px;font-weight:850;color:{MUTED};margin-top:12px;line-height:1.45">{d}</div></div>'
              for i, (t, d) in enumerate([("ChatGPT で Work を開く", "Plus でも Astra が選べる。アプリは最新に"), ("4 要素で頼む", "材料・成果物・完成条件・停止地点。型をコピペ"), ("停止地点を決める", "送信・発注・入金・削除は人が押す")], 1))
    + '</div>'
    + f'<div style="position:absolute;left:7%;right:7%;bottom:5%;font-size:22px;font-weight:850;color:{BLUE}">本日はありがとうございました｜株式会社オールマイティ</div>')

# 40 次回予告・アンケート
add("paper", "SEM-56",
    "次回予告です。今日の型を使って作った資料や、Astraに任せてみた結果を、次回持ち寄りましょう。アンケートはこのあとご案内します。「次に知りたいこと」を書いていただけると、次回のテーマに反映します。",
    header("NEXT TIME", "次回予告：今日の「任せる 1 つ」を、やってみた結果を持ち寄る")
    + two_cols(
        f'<div class="card-hard" style="padding:40px;display:flex;flex-direction:column;justify-content:center"><div style="font-size:26px;font-weight:950;color:{BLUE}">次回に持ち寄るもの</div>'
        f'<div style="font-size:38px;font-weight:950;color:{NAVY};line-height:1.5;margin-top:16px">・今日の 4 要素で Astra に頼んだ結果<br>・うまくいった／止まった場面<br>・次に知りたいこと</div></div>',
        f'<div class="card-soft" style="padding:40px;display:flex;flex-direction:column;justify-content:center"><div style="font-size:26px;font-weight:950;color:{BLUE}">このあと</div>'
        f'<div style="font-size:38px;font-weight:950;color:{NAVY};line-height:1.5;margin-top:16px">・アンケートのご案内（次回テーマに反映）<br>・第二部：マーケティング<br>・質問は休憩中・終了後もどうぞ</div></div>',
        top="30%", bottom="18%")
    + footer_brand())


# ---- 書き出し --------------------------------------------------------------------
HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Astra を味方にする夜</title>
<link rel="stylesheet" href="css07/deck07.css">
<link rel="stylesheet" href="css07/deck07-bright.css">
</head>
<body>
<div class="deck-nav">
  <button type="button" data-prev>◀</button>
  <button type="button" data-next>▶</button>
  <select data-jump aria-label="jump"></select>
</div>
<div class="deck-stage">
"""

TAIL = """
</div>
<script src="js07/deck07.js"></script>
<script>
(function(){
  var sel=document.querySelector('[data-jump]');
  document.querySelectorAll('.xop-slide').forEach(function(s,i){
    var o=document.createElement('option');o.value=i;o.textContent=String(i+1).padStart(2,'0');sel.appendChild(o);
  });
})();
</script>
</body>
</html>
"""


def render_slide(i: int, tone: str, tid: str, notes: str, body: str) -> str:
    return (f'\n<!-- {i:02d} {tid}（tone-{tone}） -->\n'
            f'<section class="xop-slide tone-{tone}" data-template-id="{tid}" data-notes="{esc(notes)}">\n'
            f'  <div class="xop-canvas"><div class="corner-stripes"></div><div class="brand-watermark">AI勉強会</div>\n'
            f'    <div class="semantic-layer"><div class="sem-{tone}">{body}</div></div>\n'
            f'  </div>\n</section>\n')


def main() -> None:
    SLIDES_DIR.mkdir(exist_ok=True)
    (SLIDES_DIR / "css07").mkdir(exist_ok=True)
    (SLIDES_DIR / "css07" / "deck07-bright.css").write_text(BRIGHT_CSS, encoding="utf-8")
    out = HEAD + "".join(render_slide(i, *s) for i, s in enumerate(SLIDES, 1)) + TAIL
    (SLIDES_DIR / "index.html").write_text(out, encoding="utf-8", newline="\n")
    notes = ["# 話者ノート — Astra を味方にする夜（2026-10-21 第一部 AI）", "",
             "スライド番号ごとの話す内容。`slides/index.html` の `data-notes` と同じ。", ""]
    for i, (tone, tid, n, _) in enumerate(SLIDES, 1):
        notes.append(f"## {i:02d}（{tid}）\n\n{n}\n")
    (ROOT / "speaker-notes.md").write_text("\n".join(notes), encoding="utf-8", newline="\n")
    print(f"OK: {len(SLIDES)} slides -> {SLIDES_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
