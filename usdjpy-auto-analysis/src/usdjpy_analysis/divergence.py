"""RSI ダイバージェンスの検出（通常＝レギュラー、隠れ＝ヒドゥン）。

確定ピボット（左右 pivot 本）の直近 2 組を使う。
  弱気（通常）  ：価格が高値を切り上げ、RSI は切り下げ  → 上昇の勢いが落ちている兆し
  強気（通常）  ：価格が安値を切り下げ、RSI は切り上げ  → 下落の勢いが落ちている兆し
  強気（隠れ）  ：価格が安値を切り上げ、RSI は切り下げ  → 上昇トレンドの押し目で出やすい（継続示唆）
  弱気（隠れ）  ：価格が高値を切り下げ、RSI は切り上げ  → 下降トレンドの戻りで出やすい（継続示唆）
条件：価格差 ≥ ATR × min_price_atr、RSI 差 ≥ min_rsi_diff、2 つ目のピボットが直近 max_age_bars 本以内。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .swings import Swing


@dataclass
class Divergence:
    kind: str          # "bearish" | "bullish" | "hidden_bearish" | "hidden_bullish"
    label: str         # 日本語
    i1: int
    p1: float
    r1: float
    i2: int
    p2: float
    r2: float
    meaning: str


LABELS = {
    "bearish": "弱気ダイバージェンス（通常）",
    "bullish": "強気ダイバージェンス（通常）",
    "hidden_bearish": "弱気ダイバージェンス（隠れ）",
    "hidden_bullish": "強気ダイバージェンス（隠れ）",
}
MEANING = {
    "bearish": "価格は高値を更新した一方で RSI は切り下がっており、上昇の勢いが落ちている兆し",
    "bullish": "価格は安値を更新した一方で RSI は切り上がっており、下落の勢いが落ちている兆し",
    "hidden_bearish": "価格の戻り高値は切り下がる一方で RSI は切り上がっており、下降トレンドの戻りで出やすい形（継続示唆）",
    "hidden_bullish": "価格の押し安値は切り上がる一方で RSI は切り下がっており、上昇トレンドの押し目で出やすい形（継続示唆）",
}


def detect(highs: list[Swing], lows: list[Swing], rsi: np.ndarray, n_bars: int, atr_now: float, *,
           min_price_atr: float, min_rsi_diff: float, max_age_bars: int, hidden: bool) -> list[Divergence]:
    out: list[Divergence] = []
    min_p = atr_now * min_price_atr

    def recent(s: Swing) -> bool:
        return (n_bars - 1 - s.index) <= max_age_bars

    if len(highs) >= 2 and recent(highs[-1]):
        a, b = highs[-2], highs[-1]
        ra, rb = float(rsi[a.index]), float(rsi[b.index])
        if not (np.isnan(ra) or np.isnan(rb)):
            if b.price - a.price >= min_p and ra - rb >= min_rsi_diff:
                out.append(Divergence("bearish", LABELS["bearish"], a.index, a.price, ra, b.index, b.price, rb, MEANING["bearish"]))
            elif hidden and a.price - b.price >= min_p and rb - ra >= min_rsi_diff:
                out.append(Divergence("hidden_bearish", LABELS["hidden_bearish"], a.index, a.price, ra, b.index, b.price, rb, MEANING["hidden_bearish"]))
    if len(lows) >= 2 and recent(lows[-1]):
        a, b = lows[-2], lows[-1]
        ra, rb = float(rsi[a.index]), float(rsi[b.index])
        if not (np.isnan(ra) or np.isnan(rb)):
            if a.price - b.price >= min_p and rb - ra >= min_rsi_diff:
                out.append(Divergence("bullish", LABELS["bullish"], a.index, a.price, ra, b.index, b.price, rb, MEANING["bullish"]))
            elif hidden and b.price - a.price >= min_p and ra - rb >= min_rsi_diff:
                out.append(Divergence("hidden_bullish", LABELS["hidden_bullish"], a.index, a.price, ra, b.index, b.price, rb, MEANING["hidden_bullish"]))
    return out


def rsi_zone_text(r: float) -> str:
    if r >= 70:
        return "買われすぎ圏（70 以上）"
    if r <= 30:
        return "売られすぎ圏（30 以下）"
    if r >= 55:
        return "中立〜やや強い（50 の上）"
    if r <= 45:
        return "中立〜やや弱い（50 の下）"
    return "中立（50 付近）"
