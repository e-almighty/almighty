"""根拠の重なり（コンフルエンス）ゾーン。

サポレジ・フィボ・EMA・チャネル・前日/前週高安・押し安値（戻り高値）・心理的節目を 1 つの候補表に集め、
価格差 ATR × merge_atr 以内のものを束ねて、重みの合計で格付けする。
現在値より上を「上の注目価格帯」、下を「下の注目価格帯」とし、それぞれ上位 max_each_side 件。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Candidate:
    price: float
    source: str      # 種類（サポレジ／フィボ／EMA50 …）
    label: str       # 根拠の説明（短文）
    weight: float


@dataclass
class Zone:
    low: float
    high: float
    center: float
    side: str                 # "above" | "below"
    score: float
    members: list[Candidate] = field(default_factory=list)
    distance_pips: float = 0.0
    distance_atr: float = 0.0

    def reasons(self) -> list[str]:
        return [f"{m.source}：{m.label}" for m in sorted(self.members, key=lambda m: -m.weight)]

    def kinds(self) -> list[str]:
        seen = []
        for m in self.members:
            if m.source not in seen:
                seen.append(m.source)
        return seen


def build(cands: list[Candidate], close_now: float, atr_now: float, *, merge_atr: float,
          max_each_side: int, pip: float, min_kinds: int = 1) -> tuple[list[Zone], list[Zone]]:
    if not cands:
        return [], []
    tol = atr_now * merge_atr
    srt = sorted(cands, key=lambda c: c.price)
    groups: list[list[Candidate]] = [[srt[0]]]
    for c in srt[1:]:
        g = groups[-1]
        center = float(np.mean([m.price for m in g]))
        if abs(c.price - center) <= tol:
            g.append(c)
        else:
            groups.append([c])
    zones: list[Zone] = []
    for g in groups:
        prices = [m.price for m in g]
        center = float(np.median(prices))
        side = "above" if center > close_now else "below"
        score = sum(m.weight for m in g)
        dist = abs(center - close_now)
        z = Zone(min(prices), max(prices), center, side, round(score, 2), g, round(dist / pip, 1),
                 round(dist / atr_now, 2) if atr_now > 0 else 0.0)
        if len(z.kinds()) >= min_kinds:
            zones.append(z)

    def pick(side: str) -> list[Zone]:
        pool = [z for z in zones if z.side == side]
        # 得点が高く、近いものを優先（得点 − 距離(ATR)×0.3）
        pool.sort(key=lambda z: -(z.score - z.distance_atr * 0.3))
        chosen = pool[:max_each_side]
        return sorted(chosen, key=lambda z: z.center, reverse=(side == "below"))

    return pick("above"), pick("below")


def distance_text(d_atr: float) -> str:
    if d_atr <= 0.5:
        return "目前"
    if d_atr <= 1.5:
        return "数本以内の射程"
    if d_atr <= 4.0:
        return "数日の射程"
    return "中期の目安"
