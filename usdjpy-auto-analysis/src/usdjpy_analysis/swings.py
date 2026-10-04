"""スイング高値・安値（Pivot High / Pivot Low）。

Pine の ta.pivothigh(left, right) と同じ考え方:
  足 i が、左 left 本すべてより高く、右 right 本すべて以上なら Pivot High。
  右 right 本が確定して初めて決まるので、直近 right 本の中には確定ピボットは無い。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Swing:
    index: int      # 足の位置（0 始まり）
    price: float    # 高値または安値
    kind: str       # "high" または "low"


def find_pivots(high, low, left: int, right: int) -> tuple[list[Swing], list[Swing]]:
    """確定したスイング高値・安値を古い順に返す。"""
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    n = len(h)
    highs: list[Swing] = []
    lows: list[Swing] = []
    for i in range(left, n - right):
        hl = h[i - left : i]
        hr = h[i + 1 : i + 1 + right]
        if h[i] > hl.max() and h[i] >= hr.max():
            highs.append(Swing(i, float(h[i]), "high"))
        ll = l[i - left : i]
        lr = l[i + 1 : i + 1 + right]
        if l[i] < ll.min() and l[i] <= lr.min():
            lows.append(Swing(i, float(l[i]), "low"))
    return highs, lows


def alternate(highs: list[Swing], lows: list[Swing], open_=None, close=None) -> list[Swing]:
    """高値と安値を時間順に並べ、同じ種類が続いたら極値の方だけ残す（ZigZag 風）。

    同じ足に高値と安値の両方のピボットがあるとき（アウトサイドバー）は、足の向きで順番を決める：
      陽線（終値 ≥ 始値）→ 安値 → 高値、陰線 → 高値 → 安値。open_/close を渡さないときは高値 → 安値。
    """
    if open_ is not None and close is not None:
        o = np.asarray(open_, dtype=float)
        c = np.asarray(close, dtype=float)

        def order(s: Swing) -> int:
            bullish = c[s.index] >= o[s.index]
            return (1 if s.kind == "high" else 0) if bullish else (0 if s.kind == "high" else 1)
    else:
        def order(s: Swing) -> int:
            return 0 if s.kind == "high" else 1
    allsw = sorted(highs + lows, key=lambda s: (s.index, order(s)))
    out: list[Swing] = []
    for s in allsw:
        if out and out[-1].kind == s.kind:
            prev = out[-1]
            better = (s.kind == "high" and s.price > prev.price) or (s.kind == "low" and s.price < prev.price)
            if better:
                out[-1] = s
            continue
        out.append(s)
    return out
