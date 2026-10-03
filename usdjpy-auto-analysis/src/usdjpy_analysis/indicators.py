"""Pine Script の ta.* と同じ定義の指標。

FX_PhoenixConfluence/backtest/tvbt.py から必要な分だけ移植した。
  ema  : 初値で初期化（Pine の ta.ema と同じ）
  rma  : SMA(n) で初期化、alpha = 1/n（Pine の ta.rma と同じ）
  atr  : rma(true range)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s, n: int) -> np.ndarray:
    return pd.Series(np.asarray(s, dtype=float)).rolling(n).mean().to_numpy()


def ema(s, n: int) -> np.ndarray:
    return pd.Series(np.asarray(s, dtype=float)).ewm(alpha=2.0 / (n + 1), adjust=False).mean().to_numpy()


def rma(s, n: int) -> np.ndarray:
    s = np.asarray(s, dtype=float)
    out = np.full(len(s), np.nan)
    if len(s) < n:
        return out
    valid = ~np.isnan(s)
    start = None
    for i in range(n - 1, len(s)):
        if valid[i - n + 1 : i + 1].all():
            start = i
            break
    if start is None:
        return out
    out[start] = s[start - n + 1 : start + 1].mean()
    a = 1.0 / n
    for i in range(start + 1, len(s)):
        x = s[i]
        out[i] = out[i - 1] if np.isnan(x) else a * x + (1 - a) * out[i - 1]
    return out


def true_range(high, low, close) -> np.ndarray:
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    c = np.asarray(close, dtype=float)
    pc = np.empty_like(c)
    pc[0] = np.nan
    pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return tr


def atr(high, low, close, n: int = 14) -> np.ndarray:
    return rma(true_range(high, low, close), n)
