"""フィボナッチ・リトレースメント／エクステンション。

2 組を使い分ける（SHO 2026-10-04「フィボナッチをもっと上手に使う」）:
  (1) 主波（リトレースメント用）：チャートに写っている範囲（直近 bars_to_plot 本）で最も大きな波。
      上昇なら「最安値 → その後の最高値」、下降なら「最高値 → その後の最安値」。ヒゲを含む。
      38.2／50／61.8% が押し目（戻り）の候補帯。サポレジ・EMA・前日高安と重なる所が本命。
      config: fibonacci.wave = chart_major（既定）／structure（押し安値→更新対象の高値）／last_impulse（主要スイングの最後の推進波）
  (2) 直近波（目標用）：主要スイングの最後の推進波を 3 点方式で伸ばす。
      上昇：終点 H の後の押しの極値 C を 3 点目にして C + (H−L) × e。e=1.0 が N 計算値、1.618 が 161.8%。
      H の後に足が無ければ出さない。
  波の大きさが ATR × min_wave_atr 未満なら引かない。

リトレースメント：H − (H−L) × r（上昇）、L + (H−L) × r（下降）
主波の 2 点エクステンション（終点を更新した後の中期の目安）：L + (H−L) × e（上昇）
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .swings import Swing


@dataclass
class FibResult:
    direction: str                 # "up" | "down"
    wave: str                      # "chart_major" | "structure" | "last_impulse"
    start_index: int
    start_price: float
    end_index: int
    end_price: float
    levels: dict = field(default_factory=dict)        # {0.382: price, ...}
    extensions: dict = field(default_factory=dict)    # 3 点方式 {1.0: price, 1.618: price}
    ext_base_index: int | None = None                 # 3 点目（押し・戻りの極値）
    ext_base_price: float | None = None
    projections: dict = field(default_factory=dict)   # 2 点方式 {1.272: price, 1.618: price}（主波用・文章のみ）
    current_ratio: float | None = None                # 現在値が波のどこまで戻しているか（0=終点, 1=起点）
    current_band: str = ""                            # 「38.2〜50% の戻し」など

    @property
    def size(self) -> float:
        return abs(self.end_price - self.start_price)


def _band_text(r: float | None, levels: list[float]) -> str:
    if r is None:
        return ""
    if r < 0:
        return "波の終点を超えて伸びている（押し戻しなし）"
    if r > 1:
        return "起点を割っており、この波の押し目・戻りとしては成立していない"
    ls = sorted(levels)
    prev = 0.0
    for l in ls:
        if r <= l:
            return f"{prev * 100:.1f}〜{l * 100:.1f}% の戻し" if prev > 0 else f"{l * 100:.1f}% より浅い戻し"
        prev = l
    return f"{prev * 100:.1f}% より深い戻し"


def last_impulse(major: list[Swing], direction: str) -> tuple[Swing, Swing] | None:
    """主要スイングの最後の推進波 (起点, 終点) を返す。"""
    highs = [s for s in major if s.kind == "high"]
    lows = [s for s in major if s.kind == "low"]
    if direction == "up":
        if not highs:
            return None
        h = highs[-1]
        prior = [s for s in lows if s.index < h.index or (s.index == h.index and major.index(s) < major.index(h))]
        return (prior[-1], h) if prior else None
    if not lows:
        return None
    l = lows[-1]
    prior = [s for s in highs if s.index < l.index or (s.index == l.index and major.index(s) < major.index(l))]
    return (prior[-1], l) if prior else None


def chart_major_wave(high: np.ndarray, low: np.ndarray, start: int, direction: str) -> tuple[tuple[int, float], tuple[int, float]] | None:
    """区間 [start:] で最も大きな波。上昇＝最安値→その後の最高値、下降＝最高値→その後の最安値。"""
    h = np.asarray(high, dtype=float)[start:]
    l = np.asarray(low, dtype=float)[start:]
    if len(h) < 5:
        return None
    if direction == "up":
        li = int(np.argmin(l))
        if li >= len(h) - 1:
            return None
        hi = li + 1 + int(np.argmax(h[li + 1:]))
        return (start + li, float(l[li])), (start + hi, float(h[hi]))
    hi = int(np.argmax(h))
    if hi >= len(l) - 1:
        return None
    li = hi + 1 + int(np.argmin(l[hi + 1:]))
    return (start + hi, float(h[hi])), (start + li, float(l[li]))


def compute_points(start: tuple[int, float], end: tuple[int, float], direction: str, wave: str, close_now: float,
                   atr_now: float, high: np.ndarray, low: np.ndarray, *, levels: list[float], extensions: list[float],
                   min_wave_atr: float, projections: list[float] | None = None) -> FibResult | None:
    si, sp = start
    ei, ep = end
    size = abs(ep - sp)
    if size < atr_now * min_wave_atr or size <= 0:
        return None
    proj = {}
    if direction == "up":
        lv = {r: ep - size * r for r in levels}
        ratio = (ep - close_now) / size
        ext, cb_i, cb_p = {}, None, None
        if ei + 1 < len(low):
            seg = low[ei + 1:]
            cb_i = int(ei + 1 + int(np.argmin(seg)))
            cb_p = float(seg.min())
            if cb_p < ep:
                ext = {e: cb_p + size * e for e in extensions}
        if projections:
            proj = {e: sp + size * e for e in projections}
    else:
        lv = {r: ep + size * r for r in levels}
        ratio = (close_now - ep) / size
        ext, cb_i, cb_p = {}, None, None
        if ei + 1 < len(high):
            seg = high[ei + 1:]
            cb_i = int(ei + 1 + int(np.argmax(seg)))
            cb_p = float(seg.max())
            if cb_p > ep:
                ext = {e: cb_p - size * e for e in extensions}
        if projections:
            proj = {e: sp - size * e for e in projections}
    return FibResult(direction, wave, si, sp, ei, ep, lv, ext, cb_i if ext else None, cb_p if ext else None, proj,
                     ratio, _band_text(ratio, levels))


def compute(major: list[Swing], close_now: float, atr_now: float, *, levels: list[float], extensions: list[float],
            min_wave_atr: float, direction: str, high: np.ndarray, low: np.ndarray, wave: str = "chart_major",
            window_start: int = 0, key_point: tuple[int, float] | None = None, top_point: tuple[int, float] | None = None,
            projections: list[float] | None = None) -> FibResult | None:
    """リトレースメント用の主波。wave の指定で取れないときは次の候補に落ちる（chart_major → structure → last_impulse）。"""
    if direction not in ("up", "down"):
        return None
    order = {"chart_major": ["chart_major", "structure", "last_impulse"],
             "structure": ["structure", "last_impulse"],
             "last_impulse": ["last_impulse"]}.get(wave, ["chart_major", "structure", "last_impulse"])
    for w in order:
        if w == "chart_major":
            pts = chart_major_wave(high, low, window_start, direction)
            if pts is None:
                continue
            r = compute_points(pts[0], pts[1], direction, w, close_now, atr_now, high, low, levels=levels,
                               extensions=extensions, min_wave_atr=min_wave_atr, projections=projections)
        elif w == "structure":
            if key_point is None or top_point is None:
                continue
            r = compute_points(key_point, top_point, direction, w, close_now, atr_now, high, low, levels=levels,
                               extensions=extensions, min_wave_atr=min_wave_atr, projections=projections)
        else:
            pts = last_impulse(major, direction)
            if pts is None:
                continue
            a, b = pts
            r = compute_points((a.index, a.price), (b.index, b.price), direction, w, close_now, atr_now, high, low,
                               levels=levels, extensions=extensions, min_wave_atr=min_wave_atr, projections=projections)
        if r is not None:
            return r
    return None


def compute_target(major: list[Swing], close_now: float, atr_now: float, *, extensions: list[float], min_wave_atr: float,
                   direction: str, high: np.ndarray, low: np.ndarray) -> FibResult | None:
    """目標用の直近波（主要スイングの最後の推進波を 3 点方式で伸ばす）。終点の後に足が無ければ None。"""
    if direction not in ("up", "down"):
        return None
    pts = last_impulse(major, direction)
    if pts is None:
        return None
    a, b = pts
    r = compute_points((a.index, a.price), (b.index, b.price), direction, "last_impulse", close_now, atr_now, high, low,
                       levels=[], extensions=extensions, min_wave_atr=min_wave_atr)
    if r is None or not r.extensions:
        return None
    return r
