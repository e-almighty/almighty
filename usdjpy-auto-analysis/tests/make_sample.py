"""動作確認用の架空 4時間足データ（本物の相場ではない）。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_sample(n: int = 400, seed: int = 1, start: str = "2026-07-01", base: float = 155.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    # ゆっくりした上昇 + 波 + ノイズ
    drift = 0.004 * t + 1.2 * np.sin(t / 25.0) + 0.5 * np.sin(t / 7.0)
    noise = rng.normal(0, 0.12, n).cumsum() * 0.3
    close = base + drift + noise
    open_ = np.r_[close[0], close[:-1]] + rng.normal(0, 0.03, n)
    rng_hl = np.abs(rng.normal(0.18, 0.08, n))
    high = np.maximum(open_, close) + rng_hl * rng.uniform(0.3, 1.0, n)
    low = np.minimum(open_, close) - rng_hl * rng.uniform(0.3, 1.0, n)
    idx = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": 0.0}, index=idx)
