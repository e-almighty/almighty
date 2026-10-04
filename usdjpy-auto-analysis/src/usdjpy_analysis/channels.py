"""平行チャネル（SHO の指定・2026-10-04：トレンドライン単体ではなくチャネルで持つ。中央線も描く）。

作り方（docs/ANALYSIS_RULES.md「チャネル」）:
  1. 基準線 = trendlines.find_trendline() で見つけた線（上昇なら安値を結ぶ線、下降なら高値を結ぶ線）
  2. 反対側の線 = 基準線と平行で、基準線の起点から現在までの「最も離れた反対側の値」を通る線
       上昇チャネルなら、期間内で基準線から最も上に離れた高値（ヒゲ含む）を通す
       → チャネルの中に期間内の値動きがすべて収まる
  3. 中央線 = 上限と下限のちょうど真ん中
  4. 現在の終値がチャネルの中のどこにいるか（0 = 下限、1 = 上限）を出す
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .trendlines import TrendLine


@dataclass
class Channel:
    kind: str                 # "up" | "down"
    base: TrendLine           # 基準線（上昇なら下限、下降なら上限）
    offset: float             # 平行線までの距離（価格）。常に正
    far_index: int            # 平行線を決めた足の位置
    far_price: float          # その足の高値（上昇）または安値（下降）
    touches_base: int         # 基準線に触れた回数
    touches_far: int          # 平行線に触れた回数
    lower_now: float
    center_now: float
    upper_now: float
    position: float           # 現在の終値の位置（0 = 下限、1 = 上限。範囲外もあり得る）
    broken: bool              # 基準線が終値で割られたか

    def slope(self) -> float:
        return self.base.slope()

    def lower_at(self, i: int) -> float:
        v = self.base.value_at(i)
        return v if self.kind == "up" else v - self.offset

    def upper_at(self, i: int) -> float:
        v = self.base.value_at(i)
        return v + self.offset if self.kind == "up" else v

    def center_at(self, i: int) -> float:
        return (self.lower_at(i) + self.upper_at(i)) / 2.0


def _count_runs(mask: np.ndarray) -> int:
    count = 0
    prev = False
    for t in mask:
        if t and not prev:
            count += 1
        prev = bool(t)
    return count


def build_channel(base: TrendLine, high, low, close, tol: float,
                  far_point: str = "extreme", pivot_indices: list[int] | None = None) -> Channel | None:
    """基準線から平行チャネルを作る。far_point="pivot" なら確定スイングだけを平行線の候補にする。"""
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    n = len(c)
    idx = np.arange(base.i1, n)
    line = base.p1 + base.slope() * (idx - base.i1)
    if base.kind == "up":
        diffs = h[base.i1:n] - line
    else:
        diffs = line - l[base.i1:n]
    cand = np.arange(len(diffs))
    if far_point == "pivot" and pivot_indices:
        piv = [p - base.i1 for p in pivot_indices if base.i1 <= p < n]
        if piv:
            cand = np.asarray(piv)
    k = int(cand[np.argmax(diffs[cand])])
    offset = float(diffs[k])
    if offset <= tol:            # 平行線が基準線とほぼ重なる＝チャネルとして意味がない
        return None
    far_index = base.i1 + k
    if base.kind == "up":
        far_price = float(h[far_index])
        upper = line + offset
        touches_far = _count_runs(np.abs(h[base.i1:n] - upper) <= tol)
        lower_now, upper_now = float(line[-1]), float(upper[-1])
    else:
        far_price = float(l[far_index])
        lower = line - offset
        touches_far = _count_runs(np.abs(l[base.i1:n] - lower) <= tol)
        lower_now, upper_now = float(lower[-1]), float(line[-1])
    width = upper_now - lower_now
    position = float((c[-1] - lower_now) / width) if width > 0 else 0.5
    return Channel(base.kind, base, offset, far_index, far_price, base.touches, touches_far,
                   lower_now, (lower_now + upper_now) / 2.0, upper_now, position, base.broken)


def position_text(pos: float) -> str:
    if pos > 1.0:
        return "上限を上抜けている"
    if pos >= 0.75:
        return "上限寄り"
    if pos >= 0.5:
        return "中央より上"
    if pos >= 0.25:
        return "中央より下"
    if pos >= 0.0:
        return "下限寄り"
    return "下限を割り込んでいる"
