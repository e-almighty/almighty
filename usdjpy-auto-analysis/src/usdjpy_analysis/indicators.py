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


def rsi(close, n: int = 14) -> np.ndarray:
    """Pine の ta.rsi と同じ（上昇幅・下落幅の rma の比）。"""
    s = np.asarray(close, dtype=float)
    ch = np.empty_like(s)
    ch[0] = np.nan
    ch[1:] = s[1:] - s[:-1]
    up = np.where(np.isnan(ch), np.nan, np.maximum(ch, 0))
    dn = np.where(np.isnan(ch), np.nan, np.maximum(-ch, 0))
    ru, rd = rma(up, n), rma(dn, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(rd == 0, 100.0, np.where(ru == 0, 0.0, 100 - 100 / (1 + ru / rd)))
    return out


def highest(s, n: int) -> np.ndarray:
    return pd.Series(np.asarray(s, dtype=float)).rolling(n).max().to_numpy()


def lowest(s, n: int) -> np.ndarray:
    return pd.Series(np.asarray(s, dtype=float)).rolling(n).min().to_numpy()


def stdev(s, n: int) -> np.ndarray:
    return pd.Series(np.asarray(s, dtype=float)).rolling(n).std(ddof=0).to_numpy()


def linreg(s, n: int, offset: int = 0) -> np.ndarray:
    """Pine の ta.linreg：最小二乗直線の末尾の値。"""
    ser = pd.Series(np.asarray(s, dtype=float))
    x = np.arange(n, dtype=float)
    xm = x.mean()
    xv = ((x - xm) ** 2).sum()

    def f(y):
        ym = y.mean()
        slope = ((x - xm) * (y - ym)).sum() / xv
        return (ym - slope * xm) + slope * (n - 1 - offset)

    return ser.rolling(n).apply(f, raw=True).to_numpy()


def sqzmom(high, low, close, bb_len: int = 20, bb_mult: float = 2.0, kc_len: int = 20, kc_mult: float = 1.5):
    """LazyBear の SQZMOM_LB（FX_PhoenixConfluence/backtest/tvbt.py から移植）。
    返り値: (val, sqz_on, sqz_off)  val=モメンタム, sqz_on=スクイーズ中, sqz_off=解放"""
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    basis = sma(c, bb_len)
    dev = bb_mult * stdev(c, bb_len)
    up_bb, lo_bb = basis + dev, basis - dev
    ma_k = sma(c, kc_len)
    rng = sma(true_range(h, l, c), kc_len)
    up_kc, lo_kc = ma_k + rng * kc_mult, ma_k - rng * kc_mult
    sqz_on = (lo_bb > lo_kc) & (up_bb < up_kc)
    sqz_off = (lo_bb < lo_kc) & (up_bb > up_kc)
    hh, ll = highest(h, kc_len), lowest(l, kc_len)
    val = linreg(c - ((hh + ll) / 2 + sma(c, kc_len)) / 2, kc_len, 0)
    return val, sqz_on, sqz_off
