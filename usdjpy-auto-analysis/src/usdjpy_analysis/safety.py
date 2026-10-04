"""表現の安全弁。断定・助言と受け取られる言葉を機械的に置き換える／検出する。"""
from __future__ import annotations

import re

# 置き換え（左 → 右）。順番に適用する
REPLACEMENTS = [
    ("必ず", "多くの場合"),
    ("絶対に", ""),
    ("絶対", "強く"),
    ("確実に", "比較的"),
    ("推奨", "一案"),
    ("〜べき", "〜が考えられ"),
    ("べきです", "が考えられます"),
    ("べき", "のが一案"),
    ("エントリー", "仕掛けの目安"),
    ("買いです", "上方向が意識されます"),
    ("売りです", "下方向が意識されます"),
]
BANNED_PATTERNS = [r"必ず", r"絶対", r"確実", r"推奨", r"べき", r"エントリー", r"買いです", r"売りです"]

DISCLAIMER = "※テクニカル分析の参考情報であり、投資助言ではありません。価格は参考値（15分以上の遅延あり）、判定は確定足の終値に基づきます。"


def sanitize(text: str) -> tuple[str, list[str]]:
    hits = [p for p in BANNED_PATTERNS if re.search(p, text)]
    out = text
    for a, b in REPLACEMENTS:
        out = out.replace(a, b)
    return out, hits
