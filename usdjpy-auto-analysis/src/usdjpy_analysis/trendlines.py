"""トレンドライン候補。

上昇トレンドライン: 直近の確定スイング安値から2点（後の点が高い）を選んで結ぶ。
  その2点の間と、2点目以降の足で「終値がラインを割っていない」ものだけ有効。
  3点目以降の接触（ヒゲが ATR × tolerance 以内）があれば「3点確認あり」。
下降トレンドライン: スイング高値で同じことをする。
レンジ相場では引かない（呼び出し側で判断）。
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from .swings import Swing


@dataclass
class TrendLine:
    kind: str                # "up" | "down"
    i1: int
    p1: float
    i2: int
    p2: float
    touches: int             # 2点を含む接触回数
    value_now: float         # 現在の足での線の値
    broken: bool             # 現在の終値が線を越えて反対側にあるか

    def slope(self) -> float:
        return (self.p2 - self.p1) / (self.i2 - self.i1)

    def value_at(self, i: int) -> float:
        return self.p1 + self.slope() * (i - self.i1)


def _fit(kind: str, swings: list[Swing], low: np.ndarray, high: np.ndarray, close: np.ndarray,
         tol: float, n_candidates: int, min_touches: int, max_broken_age: int, max_distance: float) -> TrendLine | None:
    pts = swings[-n_candidates:]
    n = len(close)
    best: TrendLine | None = None
    for a, b in combinations(pts, 2):
        if b.index <= a.index:
            continue
        rising = b.price > a.price
        if kind == "up" and not rising:
            continue
        if kind == "down" and rising:
            continue
        slope = (b.price - a.price) / (b.index - a.index)
        idx = np.arange(a.index, n)
        line = a.price + slope * (idx - a.index)
        seg_close = close[a.index:n]
        seg_low = low[a.index:n]
        seg_high = high[a.index:n]
        if kind == "up":
            violated = seg_close < line - tol      # 終値が線を割った足
            touched = np.abs(seg_low - line) <= tol
        else:
            violated = seg_close > line + tol
            touched = np.abs(seg_high - line) <= tol
        # 2点目までの間で終値が線を越えていたら無効
        if violated[: b.index - a.index + 1].any():
            continue
        # 2点目より後に線を越えた足があるなら、その最初の足を「ブレイク」とみなす
        after = np.where(violated[b.index - a.index + 1 :])[0]
        if len(after):
            first_break = b.index + 1 + int(after[0])
            if n - 1 - first_break > max_broken_age:
                continue                           # 昔に割られた線は、もうトレンドラインではない
            broken = True
            touched = touched[: first_break - a.index]   # ブレイク後の接触は数えない
        else:
            broken = False
        # 線が今の価格から離れすぎていたら、画像に載せる価値がない
        if abs(float(line[-1]) - float(close[-1])) > max_distance:
            continue
        # 連続する足の接触は1回に数える
        touches = 0
        prev = False
        for t in touched:
            if t and not prev:
                touches += 1
            prev = bool(t)
        touches = max(touches, 2)
        if touches < min_touches:
            continue
        cand = TrendLine(kind, a.index, a.price, b.index, b.price, touches, float(line[-1]), broken)
        # 生きている線 > 接触が多い線 > 新しい線 の順で選ぶ
        key = (not cand.broken, cand.touches, cand.i2)
        if best is None or key > (not best.broken, best.touches, best.i2):
            best = cand
    return best


def find_trendline(kind: str, highs: list[Swing], lows: list[Swing], low, high, close, *,
                   tolerance: float, n_candidates: int, min_touches: int,
                   max_broken_age: int = 10, max_distance: float = float("inf")) -> TrendLine | None:
    """kind="up" はスイング安値、"down" はスイング高値から 1 本選ぶ。見つからなければ None。

    max_broken_age: ブレイクからこの本数より経った線は捨てる（直近のブレイクだけ「割れた」と報告する）
    max_distance:   現在の線の値と現在値の差がこれより大きい線は捨てる（価格単位）
    """
    swings = lows if kind == "up" else highs
    return _fit(kind, swings, np.asarray(low, float), np.asarray(high, float), np.asarray(close, float),
                tolerance, n_candidates, min_touches, max_broken_age, max_distance)
