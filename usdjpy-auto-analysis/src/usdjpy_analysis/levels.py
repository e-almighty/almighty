"""サポート・レジスタンス候補。

手順（docs/ANALYSIS_RULES.md の「サポレジ」と対応）:
  1. 解析範囲のスイング高値・安値を集める
  2. 価格差が ATR × cluster_atr_mult 以内のものを1つにまとめる（クラスタ）
  3. それぞれの価格帯に、ローソク足のヒゲが何回触れたか（反応回数）を数える
  4. 重要度 = 反応回数 + 直近性 + 心理的節目ボーナス
  5. 現在値より下をサポート、上をレジスタンスとして、重要度順に最大 N 本
     （ライン同士が ATR × min_separation_atr より近いものは間引く）
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .swings import Swing


@dataclass
class Level:
    price: float
    kind: str                 # "support" | "resistance"
    touches: int              # ヒゲが触れた回数（連続する足は1回と数える）
    pivots: int               # まとめたスイングの数
    last_touch_index: int     # 最後に触れた足の位置
    score: float
    is_round: bool = False
    members: list[float] = field(default_factory=list)

    def label(self) -> str:
        return f"{self.price:.3f}"


def _is_round(price: float, step: float, tol: float) -> bool:
    r = round(price / step) * step
    return abs(price - r) <= tol


def _cluster(swings: list[Swing], tol: float) -> list[list[Swing]]:
    if not swings:
        return []
    srt = sorted(swings, key=lambda s: s.price)
    clusters: list[list[Swing]] = [[srt[0]]]
    for s in srt[1:]:
        cur = clusters[-1]
        center = float(np.mean([m.price for m in cur]))
        if abs(s.price - center) <= tol:
            cur.append(s)
        else:
            clusters.append([s])
    return clusters


def _count_touches(level: float, high: np.ndarray, low: np.ndarray, tol: float) -> tuple[int, int]:
    """ヒゲが level ± tol に入った回数と、最後に触れた足の位置。連続する足は1回。"""
    touched = (np.abs(high - level) <= tol) | (np.abs(low - level) <= tol) | ((low <= level) & (high >= level))
    count = 0
    last = -1
    prev = False
    for i, t in enumerate(touched):
        if t and not prev:
            count += 1
        if t:
            last = i
        prev = bool(t)
    return count, last


def build_levels(
    highs: list[Swing],
    lows: list[Swing],
    high: np.ndarray,
    low: np.ndarray,
    close_now: float,
    atr_now: float,
    *,
    cluster_atr_mult: float,
    min_separation_atr: float,
    max_support: int,
    max_resistance: int,
    round_number_step: float,
) -> tuple[list[Level], list[Level]]:
    n = len(high)
    tol = atr_now * cluster_atr_mult
    sep = atr_now * min_separation_atr
    candidates: list[Level] = []
    for cl in _cluster(highs + lows, tol):
        price = float(np.median([s.price for s in cl]))
        touches, last = _count_touches(price, high, low, tol * 0.5)
        recency = math.exp(-(n - 1 - max(last, 0)) / max(n / 3, 1))
        is_round = _is_round(price, round_number_step, atr_now * 0.15)
        score = touches + len(cl) * 0.5 + recency * 1.5 + (0.5 if is_round else 0.0)
        kind = "support" if price < close_now else "resistance"
        candidates.append(Level(price, kind, touches, len(cl), last, round(score, 3), is_round, [s.price for s in cl]))

    def pick(kind: str, limit: int) -> list[Level]:
        pool = sorted([c for c in candidates if c.kind == kind], key=lambda c: c.score, reverse=True)
        chosen: list[Level] = []
        for c in pool:
            if len(chosen) >= limit:
                break
            if all(abs(c.price - o.price) >= sep for o in chosen):
                chosen.append(c)
        return sorted(chosen, key=lambda c: c.price, reverse=(kind == "support"))

    return pick("support", max_support), pick("resistance", max_resistance)
