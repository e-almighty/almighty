"""解析 → ライン → 画像 → 解説 をつなぐ。

analyze(df, cfg, tf="4h", df_daily=None) -> dict
run(df, cfg, out_dir, ...)             -> 画像・解説・JSON を保存
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

from . import chart, commentary, indicators, levels, swings, trend, trendlines


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _higher_timeframe(df_daily: pd.DataFrame | None, cfg: dict) -> dict | None:
    if df_daily is None or len(df_daily) < 5:
        return None
    period = int(cfg["higher_timeframe"]["1D"]["ema"])
    e = indicators.ema(df_daily["close"].to_numpy(), period)
    # 直前に確定した日足（最後の行が進行中の可能性があるので [-2] を使う）
    i = -2 if len(df_daily) >= 2 else -1
    c = float(df_daily["close"].iloc[i])
    ev = float(e[i])
    return {"ema_period": period, "close": c, "ema": ev, "above": c > ev,
            "bar_time_utc": df_daily.index[i].isoformat()}


def analyze(df: pd.DataFrame, cfg: dict, tf: str = "4h", df_daily: pd.DataFrame | None = None,
            now: datetime | None = None) -> dict:
    tcfg = cfg["timeframes"][tf]
    df = df.tail(int(tcfg["bars_to_analyze"])).copy()
    o, h, l, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(c)
    if n < max(int(tcfg["ema_slow"]) + 5, 60):
        raise ValueError(f"足が少なすぎます（{n}本）。最低でも {max(int(tcfg['ema_slow']) + 5, 60)} 本必要です")

    atr = indicators.atr(h, l, c, int(tcfg["atr_period"]))
    ema_f = indicators.ema(c, int(tcfg["ema_fast"]))
    ema_s = indicators.ema(c, int(tcfg["ema_slow"]))
    atr_now = float(atr[-1])

    highs, lows = swings.find_pivots(h, l, int(tcfg["pivot_left"]), int(tcfg["pivot_right"]))
    zz = swings.alternate(highs, lows)
    zz_highs = [s for s in zz if s.kind == "high"]
    zz_lows = [s for s in zz if s.kind == "low"]

    sup, res = levels.build_levels(
        highs, lows, h, l, float(c[-1]), atr_now,
        cluster_atr_mult=float(tcfg["cluster_atr_mult"]),
        min_separation_atr=float(tcfg["min_separation_atr"]),
        max_support=int(tcfg["max_support"]),
        max_resistance=int(tcfg["max_resistance"]),
        round_number_step=float(tcfg["round_number_step"]),
    )

    tcfg_trend = cfg["trend"]
    tr = trend.classify(
        c, ema_f, ema_s, atr, zz_highs, zz_lows,
        strong_threshold=int(tcfg_trend["strong_threshold"]),
        weak_threshold=int(tcfg_trend["weak_threshold"]),
        ema_slope_bars=int(tcfg_trend["ema_slope_bars"]),
        ema_slope_atr=float(tcfg_trend["ema_slope_atr"]),
    )

    tol = atr_now * float(tcfg["trendline_tolerance_atr"])
    tl_kw = dict(tolerance=tol, n_candidates=int(tcfg["trendline_candidates"]),
                 min_touches=int(tcfg["trendline_min_touches"]),
                 max_broken_age=int(tcfg.get("trendline_max_broken_age", 2 * int(tcfg["pivot_right"]))),
                 max_distance=atr_now * float(tcfg.get("trendline_max_distance_atr", 6.0)))
    tl_up = tl_dn = None
    if tr.direction >= 0:   # 上昇またはレンジ気味なら上昇ラインを探す（レンジ時は参考扱い）
        tl_up = trendlines.find_trendline("up", zz_highs, zz_lows, l, h, c, **tl_kw)
    if tr.direction <= 0:
        tl_dn = trendlines.find_trendline("down", zz_highs, zz_lows, l, h, c, **tl_kw)
    # レンジ相場では、両方見つかっても「上限・下限（サポレジ）」を優先し、トレンドラインは3点以上のものだけ残す
    if tr.direction == 0:
        if tl_up and tl_up.touches < 3:
            tl_up = None
        if tl_dn and tl_dn.touches < 3:
            tl_dn = None

    tz = ZoneInfo(cfg.get("timezone", "Asia/Tokyo"))
    now = now or datetime.now(tz)
    last_bar_jst = df.index[-1].tz_convert(tz)

    def tl_dict(t):
        if t is None:
            return None
        d = asdict(t)
        d["slope"] = t.slope()
        d["t1_utc"] = df.index[t.i1].isoformat()
        d["t2_utc"] = df.index[t.i2].isoformat()
        return d

    result = {
        "symbol": cfg["symbol"],
        "timeframe": tf,
        "timeframe_label": tcfg["label"],
        "analyzed_at_jst": now.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
        "last_bar_jst": last_bar_jst.strftime("%Y-%m-%d %H:%M"),
        "bars": n,
        "close": float(c[-1]),
        "atr": round(atr_now, 4),
        "ema_fast_period": int(tcfg["ema_fast"]),
        "ema_slow_period": int(tcfg["ema_slow"]),
        "trend": {"label": tr.label, "direction": tr.direction, "score": tr.score, "details": tr.details},
        "supports": [asdict(x) for x in sup],
        "resistances": [asdict(x) for x in res],
        "trendline_up": tl_dict(tl_up),
        "trendline_down": tl_dict(tl_dn),
        "swing_highs": [asdict(s) for s in zz_highs[-6:]],
        "swing_lows": [asdict(s) for s in zz_lows[-6:]],
        "higher_timeframe": _higher_timeframe(df_daily, cfg),
    }
    result["commentary"] = commentary.build(result)
    result["_arrays"] = {"ema_fast": ema_f, "ema_slow": ema_s}
    return result


def run(df: pd.DataFrame, cfg: dict, out_dir: str | Path, tf: str = "4h",
        df_daily: pd.DataFrame | None = None, stem: str | None = None) -> dict:
    result = analyze(df, cfg, tf, df_daily)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = result["analyzed_at_jst"].replace("-", "").replace(" ", "_").replace(":", "")
    stem = stem or f"{cfg['symbol']}_{tf}_{stamp}"
    tcfg = cfg["timeframes"][tf]
    ocfg = cfg.get("output", {})
    arrays = result.pop("_arrays")
    png = chart.render(df.tail(int(tcfg["bars_to_analyze"])), result, out_dir / f"{stem}.png",
                       bars_to_plot=int(tcfg["bars_to_plot"]), tz=cfg.get("timezone", "Asia/Tokyo"),
                       width_px=int(ocfg.get("image_width_px", 1600)), height_px=int(ocfg.get("image_height_px", 900)),
                       dpi=int(ocfg.get("dpi", 100)), ema_fast=arrays["ema_fast"], ema_slow=arrays["ema_slow"])
    md = out_dir / f"{stem}.md"
    md.write_text(
        f"# {result['symbol']} {result['timeframe_label']} 分析（{result['analyzed_at_jst']} JST）\n\n"
        f"![chart]({png.name})\n\n## 解説\n\n{result['commentary']['long']}\n\n"
        f"## X投稿案（DRY RUN・未投稿）\n\n```\n{result['commentary']['post']}\n```\n",
        encoding="utf-8")
    js = out_dir / f"{stem}.json"
    js.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    result["files"] = {"png": str(png), "md": str(md), "json": str(js)}
    return result


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)
