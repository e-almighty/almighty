"""確定足の一元管理と、日足から機械的に決まる水準（前日・前週の高安・終値）。

ルール（docs/ANALYSIS_RULES.md「確定足」）:
  足の終了時刻（＝始まり時刻 ＋ 足の長さ）が実行時刻以下なら「確定足」。
  実行時刻より後に終わる足（進行中の足）は解析に使わない。
  足の長さは、時刻の間隔の中央値から求める（4時間足 → 4h、日足 → 24h）。
  TradingView の為替の日足は NY クローズ区切り（夏 21:00 UTC／冬 22:00 UTC 始まり）。

前日 ＝ 確定している最後の日足。前週 ＝ 金曜クローズで区切った、終わっている最後の週。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd


@dataclass
class ConfirmedInfo:
    bar_seconds: int
    n_total: int
    n_confirmed: int
    last_start_utc: str
    last_end_utc: str
    last_start_jst: str          # 表示用「10/03 02:00」
    last_end_jst: str            # 表示用「10/03 06:00」
    dropped_in_progress: bool    # 進行中の足を切り捨てたか


def infer_bar_seconds(index: pd.DatetimeIndex) -> int:
    if len(index) < 2:
        return 0
    d = pd.Series(index[1:]).reset_index(drop=True) - pd.Series(index[:-1]).reset_index(drop=True)
    return int(d.median().total_seconds())


def confirmed(df: pd.DataFrame, now: datetime, tz: str = "Asia/Tokyo") -> tuple[pd.DataFrame, pd.DataFrame, ConfirmedInfo]:
    """(確定足だけの df, 進行中の足の df, 情報) を返す。"""
    sec = infer_bar_seconds(df.index)
    now_utc = pd.Timestamp(now).tz_convert("UTC") if pd.Timestamp(now).tzinfo else pd.Timestamp(now).tz_localize("UTC")
    ends = df.index + pd.Timedelta(seconds=sec)
    mask = ends <= now_utc
    done = df[mask]
    pending = df[~mask]
    if len(done) == 0:
        raise ValueError("確定した足がありません（実行時刻よりデータが新しい、または時刻の単位が違う）")
    last = done.index[-1]
    last_end = last + pd.Timedelta(seconds=sec)
    info = ConfirmedInfo(
        bar_seconds=sec, n_total=len(df), n_confirmed=len(done),
        last_start_utc=last.isoformat(), last_end_utc=last_end.isoformat(),
        last_start_jst=last.tz_convert(tz).strftime("%m/%d %H:%M"),
        last_end_jst=last_end.tz_convert(tz).strftime("%m/%d %H:%M"),
        dropped_in_progress=len(pending) > 0,
    )
    return done, pending, info


@dataclass
class DailyLevels:
    prev_day: dict | None = None        # {"date": "10/02", "open","high","low","close"}
    prev_week: dict | None = None       # {"label": "9/28〜10/02", "high","low","close"}
    this_week: dict | None = None       # 今週ここまで（あれば）
    today: dict | None = None           # 進行中の日足（あれば）＝本日ここまで
    daily_atr: float | None = None      # 日足 ATR(14)
    daily_ema: dict | None = None       # {"period":50,"value":..., "above": bool, "close": 前日終値}
    notes: list[str] = field(default_factory=list)


def _bar_dict(row: pd.Series, label: str) -> dict:
    return {"label": label, "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"])}


def daily_levels(df_daily: pd.DataFrame | None, now: datetime, tz: str, *, ema_period: int,
                 atr_period: int = 14) -> DailyLevels | None:
    """日足（UTC index）から 前日・前週・今週・本日ここまで・日足ATR・日足EMA を出す。"""
    if df_daily is None or len(df_daily) < 5:
        return None
    from . import indicators
    done, pending, _ = confirmed(df_daily, now, tz)
    out = DailyLevels()
    last = done.iloc[-1]
    out.prev_day = _bar_dict(last, done.index[-1].tz_convert(tz).strftime("%m/%d"))
    if len(pending) > 0:
        out.today = _bar_dict(pending.iloc[-1], pending.index[-1].tz_convert(tz).strftime("%m/%d"))
    # 日足 ATR と EMA は確定足で計算
    c = done["close"].to_numpy(dtype=float)
    a = indicators.atr(done["high"].to_numpy(dtype=float), done["low"].to_numpy(dtype=float), c, atr_period)
    if len(a) and not pd.isna(a[-1]):
        out.daily_atr = float(a[-1])
    e = indicators.ema(c, ema_period)
    out.daily_ema = {"period": ema_period, "value": float(e[-1]), "close": float(c[-1]), "above": bool(c[-1] > e[-1]),
                     "date": out.prev_day["label"]}
    # 週：足の始まり（JST）の日付で金曜区切り
    jst = done.copy()
    jst.index = jst.index.tz_convert(tz)
    wk = jst.resample("W-FRI", label="right", closed="right").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    now_jst = pd.Timestamp(now).tz_convert(tz)
    # now が属する週の金曜（W-FRI の右端ラベル）
    days_to_fri = (4 - now_jst.weekday()) % 7
    cur_fri = (now_jst.normalize() + pd.Timedelta(days=days_to_fri)).date()
    finished = [t for t in wk.index if t.date() < cur_fri]
    current = [t for t in wk.index if t.date() == cur_fri]
    if finished:
        t = finished[-1]
        row = wk.loc[t]
        start = (t - pd.Timedelta(days=4)).strftime("%m/%d")
        out.prev_week = {"label": f"{start}〜{t.strftime('%m/%d')}", "open": float(row["open"]),
                         "high": float(row["high"]), "low": float(row["low"]), "close": float(row["close"])}
    if current:
        row = wk.loc[current[-1]]
        out.this_week = {"label": "今週ここまで", "open": float(row["open"]), "high": float(row["high"]),
                         "low": float(row["low"]), "close": float(row["close"])}
    return out
