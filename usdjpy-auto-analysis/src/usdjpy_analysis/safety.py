"""表現の安全弁。断定・助言と受け取られる言葉を機械的に置き換える／検出する。"""
from __future__ import annotations

import re

# 置き換え（正規表現 → 置換）。順番に適用する。文法を壊さない形だけ置き換え、残りは検出（hits）にとどめる
REPLACEMENTS = [
    (r"必ず(?!しも)", "多くの場合"),
    (r"絶対に", ""),
    (r"絶対的な", "はっきりした"),
    (r"確実に", "比較的"),
    (r"(?<!非)推奨します", "一案です"),
    (r"(?<!非)推奨", "一案"),
    (r"べきです", "のが一案です"),
    (r"べきではない", "のは一案ではない"),
    (r"エントリー", "仕掛け"),
    (r"買いです", "上方向が意識されます"),
    (r"売りです", "下方向が意識されます"),
]
# 検出だけする語（置き換え後にも残っていれば hits に入る）
BANNED_PATTERNS = [r"必ず(?!しも)", r"絶対", r"(?<!不)確実", r"(?<!非)推奨", r"べき", r"エントリー", r"買いです", r"売りです"]

DISCLAIMER = "※テクニカル分析の参考情報であり、投資助言ではありません。価格は参考値（15分以上の遅延あり）、判定は確定足の終値に基づきます。"


def sanitize(text: str) -> tuple[str, list[str]]:
    """禁止語を言い換えた本文と、元の本文で見つかった禁止語（検出名）を返す。"""
    hits = [re.search(p, text).group(0) for p in BANNED_PATTERNS if re.search(p, text)]
    out = text
    for a, b in REPLACEMENTS:
        out = re.sub(a, b, out)
    return out, hits
