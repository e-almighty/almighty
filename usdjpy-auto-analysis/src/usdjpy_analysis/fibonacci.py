"""フィボナッチ・リトレースメント／エクステンション。

波の決め方：主要スイングのうち、最後の「推進波」。
  上昇構造なら 起点＝直近の主要高値の直前の主要安値 L、終点＝その主要高値 H（L→H）。
  下降構造なら 起点＝直近の主要安値の直前の主要高値 H、終点＝その主要安値 L（H→L）。
  波の大きさが ATR × min_wave_atr 未満なら引かない。

リトレースメント（押し目／戻りの目安）：H − (H−L) × r（上昇）、L + (H−L) × r（下降）
エクステンション（高値更新後の目標）：H + (H−L) × (e−1)（上昇）
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .swings import Swing


@dataclass
class FibResult:
    direction: str                 # "up" | "down"
    start_index: int
    start_price: float
    end_index: int
    end_price: float
    levels: dict = field(default_factory=dict)        # {0.382: price, ...}
    extensions: dict = field(default_factory=dict)    # {1.0: price, 1.618: price}
    current_ratio: float | None = None                # 現在値が波のどこまで戻しているか（0=終点, 1=起点）
    current_band: str = ""                            # 「38.2〜50% の押し目帯」など


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


def compute(major: list[Swing], close_now: float, atr_now: float, *,
            levels: list[float], extensions: list[float], min_wave_atr: float, direction: str) -> FibResult | None:
    highs = [s for s in major if s.kind == "high"]
    lows = [s for s in major if s.kind == "low"]
    if direction == "up":
        if not highs:
            return None
        h = highs[-1]
        prior = [s for s in lows if s.index < h.index]
        if not prior:
            return None
        l = prior[-1]
        size = h.price - l.price
        if size < atr_now * min_wave_atr:
            return None
        lv = {r: h.price - size * r for r in levels}
        ex = {e: h.price + size * (e - 1.0) for e in extensions}
        ratio = (h.price - close_now) / size if size > 0 else None
        return FibResult("up", l.index, l.price, h.index, h.price, lv, ex, ratio, _band_text(ratio, levels))
    if direction == "down":
        if not lows:
            return None
        l = lows[-1]
        prior = [s for s in highs if s.index < l.index]
        if not prior:
            return None
        h = prior[-1]
        size = h.price - l.price
        if size < atr_now * min_wave_atr:
            return None
        lv = {r: l.price + size * r for r in levels}
        ex = {e: l.price - size * (e - 1.0) for e in extensions}
        ratio = (close_now - l.price) / size if size > 0 else None
        return FibResult("down", h.index, h.price, l.index, l.price, lv, ex, ratio, _band_text(ratio, levels))
    return None
