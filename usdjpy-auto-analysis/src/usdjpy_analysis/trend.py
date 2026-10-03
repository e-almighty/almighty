"""相場環境の判定（5分類）。

スコア方式。各項目を +1 / 0 / -1 で足し合わせ、
  score >= strong_threshold → 強い上昇、 >= weak_threshold → 弱い上昇
  score <= -strong_threshold → 強い下落、 <= -weak_threshold → 弱い下落
  それ以外 → レンジ

項目:
  1. 終値が EMA(slow) の上か下か
  2. EMA(fast) が EMA(slow) の上か下か
  3. EMA(slow) の傾き（直近 N 本の変化が ATR × しきい値を超えるか）
  4. 高値・安値の切り上げ／切り下げ（直近の確定スイング 2 組）
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .swings import Swing

LABELS = {
    2: "強い上昇",
    1: "弱い上昇",
    0: "レンジ",
    -1: "弱い下落",
    -2: "強い下落",
}


@dataclass
class TrendResult:
    label: str          # 5分類の名前
    direction: int      # 2, 1, 0, -1, -2
    score: int
    details: dict       # 各項目の判定（解説文に使う）


def _structure(highs: list[Swing], lows: list[Swing]) -> tuple[int, str]:
    """直近2つの高値・安値から HH/HL（+1）、LH/LL（-1）、混在（0）を返す。"""
    if len(highs) < 2 or len(lows) < 2:
        return 0, "スイングが少なく判定できず"
    hh = highs[-1].price > highs[-2].price
    hl = lows[-1].price > lows[-2].price
    if hh and hl:
        return 1, "高値・安値とも切り上げ（HH/HL）"
    if (not hh) and (not hl):
        return -1, "高値・安値とも切り下げ（LH/LL）"
    if hh and not hl:
        return 0, "高値は切り上げ、安値は切り下げ（拡大）"
    return 0, "高値は切り下げ、安値は切り上げ（収れん）"


def classify(
    close: np.ndarray,
    ema_fast: np.ndarray,
    ema_slow: np.ndarray,
    atr: np.ndarray,
    highs: list[Swing],
    lows: list[Swing],
    *,
    strong_threshold: int,
    weak_threshold: int,
    ema_slope_bars: int,
    ema_slope_atr: float,
) -> TrendResult:
    c = float(close[-1])
    ef, es, a = float(ema_fast[-1]), float(ema_slow[-1]), float(atr[-1])
    s1 = 1 if c > es else -1
    s2 = 1 if ef > es else -1
    slope = float(ema_slow[-1] - ema_slow[-1 - ema_slope_bars])
    s3 = 1 if slope > ema_slope_atr * a else (-1 if slope < -ema_slope_atr * a else 0)
    s4, s4_text = _structure(highs, lows)
    score = s1 + s2 + s3 + s4
    if score >= strong_threshold:
        d = 2
    elif score >= weak_threshold:
        d = 1
    elif score <= -strong_threshold:
        d = -2
    elif score <= -weak_threshold:
        d = -1
    else:
        d = 0
    details = {
        "close_vs_ema_slow": "上" if s1 > 0 else "下",
        "ema_fast_vs_slow": "上" if s2 > 0 else "下",
        "ema_slow_slope": "上向き" if s3 > 0 else ("下向き" if s3 < 0 else "横ばい"),
        "structure": s4_text,
        "ema_fast": round(ef, 3),
        "ema_slow": round(es, 3),
        "atr": round(a, 3),
    }
    return TrendResult(LABELS[d], d, score, details)
