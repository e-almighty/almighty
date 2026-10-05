"""解析 → ライン → 画像 → 解説 をつなぐ。

analyze(df, cfg, tf="4h", df_daily=None, now=None, slot=None, prev=None) -> dict
run(df, cfg, out_dir, ...)                                               -> 画像・解説・JSON を保存

第2ステージ（2026-10-04）で入ったもの:
  確定足の一元管理（bars）／主要スイングとダウ理論（structure）／フィボナッチ（fibonacci）
  RSI ダイバージェンス（divergence）／SQZMOM・ATR の文脈（momentum）／注目価格帯（zones）
  表現の安全弁（safety）／前回との変化点（ledger）
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

from . import (bars, channels, chart, commentary, divergence, fibonacci, indicators, ledger, levels,
               momentum, safety, structure, swings, trend, trendlines, zones)


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _round_numbers(close: float, span: float, step: float = 1.0) -> list[float]:
    lo = np.floor((close - span) / step) * step
    hi = np.ceil((close + span) / step) * step
    return [float(x) for x in np.arange(lo, hi + step / 2, step)]


def _effective_trend(tr: trend.TrendResult, dow: structure.DowState, n_bars: int, recent_bars: int = 10,
                     flipped_jst: str | None = None) -> tuple[str, int, str]:
    """相場環境の点数と、ダウ理論の構造が食い違うときは「ただし書き」を付け、矢印を一段弱める。"""
    label, d = tr.label, tr.direction
    caveat = ""
    weaken = False
    recent_flip = dow.flipped_index is not None and (n_bars - 1 - dow.flipped_index) <= recent_bars
    when = f"（{flipped_jst}）" if flipped_jst else ""
    if d > 0:
        if dow.direction == "down":
            if recent_flip and dow.flipped_note:
                caveat = f"ただし、{dow.flipped_note}したばかり{when}で、上昇のサインとは食い違っています。"
            else:
                caveat = "ただし、主要な高値・安値は切り下げの形（下降の構造）で、上昇のサインとは食い違っています。"
            weaken = True
        elif dow.direction == "none":
            caveat = "ただし、主要な高値・安値の並びでは方向が定まっておらず、勢いの裏付けは弱めです。"
    elif d < 0:
        if dow.direction == "up":
            if recent_flip and dow.flipped_note:
                caveat = f"ただし、{dow.flipped_note}したばかり{when}で、下落のサインとは食い違っています。"
            else:
                caveat = "ただし、主要な高値・安値は切り上げの形（上昇の構造）で、下落のサインとは食い違っています。"
            weaken = True
        elif dow.direction == "none":
            caveat = "ただし、主要な高値・安値の並びでは方向が定まっておらず、勢いの裏付けは弱めです。"
    if weaken and abs(d) == 2:
        d = 1 if d > 0 else -1
        label = trend.LABELS[d]
    return label, d, caveat


def analyze(df: pd.DataFrame, cfg: dict, tf: str = "4h", df_daily: pd.DataFrame | None = None,
            now: datetime | None = None, slot: str | None = None, prev: dict | None = None,
            source: str | None = None) -> dict:
    tcfg = cfg["timeframes"][tf]
    tz_name = cfg.get("timezone", "Asia/Tokyo")
    tz = ZoneInfo(tz_name)
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    pip = float(cfg.get("pip", 0.01))
    tol_cfg = cfg.get("tolerances", {})

    # ---- 確定足だけを使う（進行中の足は切り捨てる） ----
    df, df_pending, cinfo = bars.confirmed(df, now, tz_name)
    df_conf = df                     # 確定足すべて（前回との比較に使う）

    # 指標は手元にある全データで計算してから、解析範囲（bars_to_analyze）に切る。
    # EMA200 のような長い線は、切った後に計算すると序盤の値が不正確になるため。
    full_c = df["close"].to_numpy(dtype=float)
    full_h = df["high"].to_numpy(dtype=float)
    full_l = df["low"].to_numpy(dtype=float)
    ema_long_period = int(tcfg.get("ema_long", 0) or 0)
    ema_f_full = indicators.ema(full_c, int(tcfg["ema_fast"]))
    ema_s_full = indicators.ema(full_c, int(tcfg["ema_slow"]))
    ema_l_full = indicators.ema(full_c, ema_long_period) if ema_long_period else None
    atr_full = indicators.atr(full_h, full_l, full_c, int(tcfg["atr_period"]))
    rsi_full = indicators.rsi(full_c, int(tcfg.get("rsi_period", 14)))

    df = df.tail(int(tcfg["bars_to_analyze"])).copy()
    o, h, l, c = (df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    n = len(c)
    if n < max(int(tcfg["ema_slow"]) + 5, 60):
        raise ValueError(f"足が少なすぎます（{n}本）。最低でも {max(int(tcfg['ema_slow']) + 5, 60)} 本必要です")

    atr = atr_full[-n:]
    ema_f = ema_f_full[-n:]
    ema_s = ema_s_full[-n:]
    ema_l = ema_l_full[-n:] if ema_l_full is not None else None
    rsi = rsi_full[-n:]
    atr_now = float(atr[-1])
    close_now = float(c[-1])

    # ---- スイング（小＝左右 5 本の確定ピボット、主要＝振幅 ATR×2 以上） ----
    highs, lows = swings.find_pivots(h, l, int(tcfg["pivot_left"]), int(tcfg["pivot_right"]))
    zz = swings.alternate(highs, lows, o, c)
    zz_highs = [s for s in zz if s.kind == "high"]
    zz_lows = [s for s in zz if s.kind == "low"]
    major = structure.major_swings(zz, atr_now, float(tcfg.get("major_swing_atr", 2.0)))
    major_highs = [s for s in major if s.kind == "high"]
    major_lows = [s for s in major if s.kind == "low"]

    # ---- サポレジ ----
    sup, res = levels.build_levels(
        highs, lows, h, l, close_now, atr_now,
        cluster_atr_mult=float(tcfg["cluster_atr_mult"]),
        min_separation_atr=float(tcfg["min_separation_atr"]),
        max_support=int(tcfg["max_support"]),
        max_resistance=int(tcfg["max_resistance"]),
        round_number_step=float(tcfg["round_number_step"]),
    )

    # ---- ダウ理論の構造（押し安値・戻り高値）。相場環境の項目 4 もここから取る ----
    dow = structure.dow_state(major, c, atr_now, float(tol_cfg.get("structure_break_atr", 0.1)),
                              basis=str(tol_cfg.get("structure_basis", "close")))

    # ---- 相場環境 ----
    tcfg_trend = cfg["trend"]
    tr = trend.classify(
        c, ema_f, ema_s, atr, major_highs, major_lows,
        strong_threshold=int(tcfg_trend["strong_threshold"]),
        weak_threshold=int(tcfg_trend["weak_threshold"]),
        ema_slope_bars=int(tcfg_trend["ema_slope_bars"]),
        ema_slope_atr=float(tcfg_trend["ema_slope_atr"]),
        ema_long=ema_l,
        structure=structure.structure_score(dow),
    )
    label_eff, dir_eff, caveat = _effective_trend(
        tr, dow, n, recent_bars=int(tcfg["pivot_right"]) * 2,
        flipped_jst=(df.index[dow.flipped_index].tz_convert(ZoneInfo(tz_name)).strftime("%m/%d %H:%M") if dow.flipped_index is not None else None))

    # ---- トレンドライン → 平行チャネル ----
    tol = atr_now * float(tcfg["trendline_tolerance_atr"])
    tl_kw = dict(tolerance=tol, n_candidates=int(tcfg["trendline_candidates"]),
                 min_touches=int(tcfg["trendline_min_touches"]),
                 max_broken_age=int(tcfg.get("trendline_max_broken_age", 2 * int(tcfg["pivot_right"]))),
                 max_distance=atr_now * float(tcfg.get("trendline_max_distance_atr", 6.0)))
    tl_up = tl_dn = None
    if tr.direction >= 0:
        tl_up = trendlines.find_trendline("up", zz_highs, zz_lows, l, h, c, **tl_kw)
    if tr.direction <= 0:
        tl_dn = trendlines.find_trendline("down", zz_highs, zz_lows, l, h, c, **tl_kw)
    if tr.direction == 0:
        if tl_up and tl_up.touches < 3:
            tl_up = None
        if tl_dn and tl_dn.touches < 3:
            tl_dn = None
    far_point = str(tcfg.get("channel_far_point", "extreme"))
    ch = None
    for base in ([tl_up, tl_dn] if tr.direction >= 0 else [tl_dn, tl_up]):
        if base is not None:
            piv = [s.index for s in (zz_highs if base.kind == "up" else zz_lows)]
            ch = channels.build_channel(base, h, l, c, tol, far_point=far_point, pivot_indices=piv)
            if ch is not None:
                break

    # ---- 日足：前日・前週・本日ここまで・日足 ATR・日足 EMA ----
    htf_cfg = cfg["higher_timeframe"]["1D"]
    dl = bars.daily_levels(df_daily, now, tz_name, ema_period=int(htf_cfg["ema"]),
                           atr_period=int(htf_cfg.get("atr_period", 14)))
    if dl and dl.today and dl.today_start_utc:
        # 「本日ここまで」は日足 CSV の行ではなく、確定した 4時間足から組み立てる（日足 CSV が先の時刻まで入っていても now に整合）
        seg = df_conf[df_conf.index >= pd.Timestamp(dl.today_start_utc)]
        if len(seg):
            dl.today.update({"open": float(seg["open"].iloc[0]), "high": float(seg["high"].max()),
                             "low": float(seg["low"].min()), "close": float(seg["close"].iloc[-1])})
        else:
            dl.today = None   # 本日分の確定足がまだ無い（週明け最初の足など）
    if dl:
        bars.merge_today_into_week(dl)

    # ---- フィボナッチ（主要スイングの最後の推進波） ----
    fcfg = cfg.get("fibonacci", {})
    if dow.direction in ("up", "down"):
        fib_dir = dow.direction
    elif dir_eff != 0:
        fib_dir = "up" if dir_eff > 0 else "down"
    else:
        fib_dir = "up" if close_now > float(ema_s[-1]) else "down"
    key_pt = (dow.key_time_index, dow.key_level) if (dow.direction == fib_dir and dow.key_time_index is not None) else None
    top_pt = (dow.top_index, dow.top_price) if (dow.direction == fib_dir and dow.top_index is not None) else None
    fib_ext = [float(x) for x in fcfg.get("extensions", [1.0, 1.618])]
    fib_min = float(fcfg.get("min_wave_atr", 3.0))
    fib = fib_t = None
    if bool(fcfg.get("enabled", False)):
      fib = fibonacci.compute(major, close_now, atr_now,
                            levels=[float(x) for x in fcfg.get("levels", [0.236, 0.382, 0.5, 0.618, 0.786])],
                            extensions=fib_ext, min_wave_atr=fib_min, direction=fib_dir, high=h, low=l,
                            wave=str(fcfg.get("wave", "chart_major")), window_start=max(n - int(tcfg["bars_to_plot"]), 0),
                            key_point=key_pt, top_point=top_pt,
                            projections=[float(x) for x in fcfg.get("projections", [1.272, 1.618])])
      # 目標用の直近波（主波と同じ波なら二重に出さない）
      fib_t = fibonacci.compute_target(major, close_now, atr_now, extensions=fib_ext, min_wave_atr=fib_min,
                                       direction=fib_dir, high=h, low=l)
      if fib_t is not None and fib is not None and fib_t.start_index == fib.start_index and fib_t.end_index == fib.end_index:
          fib_t = None

    # ---- RSI ダイバージェンス ----
    dcfg = cfg.get("divergence", {})
    d_highs, d_lows = (major_highs, major_lows) if dcfg.get("swings", "minor") == "major" else (zz_highs, zz_lows)
    divs = divergence.detect(d_highs, d_lows, rsi, n, atr_now,
                             min_price_atr=float(dcfg.get("min_price_atr", 0.3)),
                             min_rsi_diff=float(dcfg.get("min_rsi_diff", 3.0)),
                             max_age_bars=int(dcfg.get("max_age_bars", 20)), hidden=bool(dcfg.get("hidden", True)),
                             max_span_bars=int(dcfg.get("max_span_bars", 60)))
    rsi_sum = momentum.rsi_summary(rsi)

    # ---- SQZMOM（文章のみ）と ATR の文脈 ----
    scfg = cfg.get("sqzmom", {})
    sqz = None
    if scfg.get("in_text", True):
        sqz = momentum.sqzmom_summary(full_h, full_l, full_c, bb_length=int(scfg.get("bb_length", 20)),
                                      bb_mult=float(scfg.get("bb_mult", 2.0)), kc_length=int(scfg.get("kc_length", 20)),
                                      kc_mult=float(scfg.get("kc_mult", 1.5)), window=n)
    acfg = cfg.get("atr_context", {})
    atr_ctx = momentum.atr_context(atr, pip, percentile_bars=int(acfg.get("percentile_bars", 100)),
                                   low_pct=float(acfg.get("low_pct", 30)), high_pct=float(acfg.get("high_pct", 70)),
                                   daily_atr=dl.daily_atr if dl else None, today=dl.today if dl else None)

    # ---- 注目価格帯（根拠の重なり） ----
    zcfg = cfg.get("zones", {})
    w = zcfg.get("weights", {})
    cands: list[zones.Candidate] = []
    for lv in sup:
        cands.append(zones.Candidate(lv.price, "サポート", f"{lv.price:.3f}（ヒゲの反応 {lv.touches} 回）",
                                     float(w.get("level", 2.0)) + min(lv.touches, 10) * 0.1))
    for lv in res:
        cands.append(zones.Candidate(lv.price, "レジスタンス", f"{lv.price:.3f}（ヒゲの反応 {lv.touches} 回）",
                                     float(w.get("level", 2.0)) + min(lv.touches, 10) * 0.1))
    if fib:
        for r, p in fib.levels.items():
            main = r in (0.382, 0.5, 0.618)
            cands.append(zones.Candidate(p, "フィボナッチ", f"主波の {r * 100:.1f}% 戻し {p:.3f}",
                                         float(w.get("fib_main" if main else "fib_other", 1.0))))
        for e, p in fib.projections.items():
            cands.append(zones.Candidate(p, "フィボ目標", f"主波の {e * 100:.1f}% {p:.3f}", float(w.get("fib_ext", 1.0))))
    for ft in ([fib_t] if fib_t else []) + ([fib] if (fib and fib.extensions and not fib_t) else []):
        for e, p in ft.extensions.items():
            nm = "N 計算値" if abs(e - 1.0) < 1e-9 else f"{e * 100:.1f}%"
            cands.append(zones.Candidate(p, "フィボ目標", f"直近波の {nm} {p:.3f}", float(w.get("fib_ext", 1.0))))
    if ch:
        cands.append(zones.Candidate(ch.lower_now, "チャネル", f"下限 {ch.lower_now:.3f}", float(w.get("channel_edge", 1.2))))
        cands.append(zones.Candidate(ch.upper_now, "チャネル", f"上限 {ch.upper_now:.3f}", float(w.get("channel_edge", 1.2))))
        cands.append(zones.Candidate(ch.center_now, "チャネル", f"中央 {ch.center_now:.3f}", float(w.get("channel_center", 0.8))))
    cands.append(zones.Candidate(float(ema_f[-1]), f"EMA{tcfg['ema_fast']}", f"{float(ema_f[-1]):.3f}", float(w.get("ema_fast", 0.8))))
    cands.append(zones.Candidate(float(ema_s[-1]), f"EMA{tcfg['ema_slow']}", f"{float(ema_s[-1]):.3f}", float(w.get("ema_slow", 1.0))))
    if ema_l is not None and not np.isnan(ema_l[-1]):
        cands.append(zones.Candidate(float(ema_l[-1]), f"EMA{ema_long_period}", f"{float(ema_l[-1]):.3f}", float(w.get("ema_long", 1.5))))
    if dl:
        if dl.daily_ema:
            cands.append(zones.Candidate(dl.daily_ema["value"], f"日足EMA{dl.daily_ema['period']}", f"{dl.daily_ema['value']:.3f}",
                                         float(w.get("daily_ema", 1.3))))
        if dl.prev_day:
            cands.append(zones.Candidate(dl.prev_day["high"], "前日高値", f"{dl.prev_day['high']:.3f}（{dl.prev_day['label']}）", float(w.get("prev_day", 1.2))))
            cands.append(zones.Candidate(dl.prev_day["low"], "前日安値", f"{dl.prev_day['low']:.3f}（{dl.prev_day['label']}）", float(w.get("prev_day", 1.2))))
            if abs(dl.prev_day["close"] - close_now) >= pip:   # 前日終値が現在値そのもの（同じ足）なら候補にしない
                cands.append(zones.Candidate(dl.prev_day["close"], "前日終値", f"{dl.prev_day['close']:.3f}", float(w.get("prev_day_close", 0.6))))
        if dl.prev_week:
            cands.append(zones.Candidate(dl.prev_week["high"], "前週高値", f"{dl.prev_week['high']:.3f}（{dl.prev_week['label']}）", float(w.get("prev_week", 1.3))))
            cands.append(zones.Candidate(dl.prev_week["low"], "前週安値", f"{dl.prev_week['low']:.3f}（{dl.prev_week['label']}）", float(w.get("prev_week", 1.3))))
    if dow.key_level is not None:
        nm = "押し安値" if dow.direction == "up" else "戻り高値"
        cands.append(zones.Candidate(dow.key_level, nm, f"{dow.key_level:.3f}（終値で割ると構造が崩れる価格）" if dow.direction == "up"
                                     else f"{dow.key_level:.3f}（終値で越えると構造が崩れる価格）", float(w.get("key_level", 1.5))))
    for rn in _round_numbers(close_now, atr_now * 4.0, 1.0):
        cands.append(zones.Candidate(rn, "節目", f"{rn:.2f}", float(w.get("round_number", 0.5))))
    z_above, z_below = zones.build(cands, close_now, atr_now, merge_atr=float(tol_cfg.get("zone_merge_atr", 0.4)),
                                   max_each_side=int(zcfg.get("max_each_side", 2)), pip=pip)

    # ---- 辞書化 ----
    last_bar = df.index[-1]
    last_bar_jst = last_bar.tz_convert(tz)

    def jst(i: int) -> str:
        return df.index[int(i)].tz_convert(tz).strftime("%m/%d %H:%M")

    def tl_dict(t):
        if t is None:
            return None
        d = asdict(t)
        d["slope"] = t.slope()
        d["t1_jst"], d["t2_jst"] = jst(t.i1), jst(t.i2)
        return d

    def ch_dict(x):
        if x is None:
            return None
        return {
            "kind": x.kind, "offset": round(x.offset, 4), "slope": x.slope(),
            "i1": x.base.i1, "p1": x.base.p1, "i2": x.base.i2, "p2": x.base.p2,
            "t1_jst": jst(x.base.i1), "t2_jst": jst(x.base.i2),
            "far_index": x.far_index, "far_price": x.far_price, "far_jst": jst(x.far_index),
            "touches_base": x.touches_base, "touches_far": x.touches_far,
            "lower_now": round(x.lower_now, 4), "center_now": round(x.center_now, 4), "upper_now": round(x.upper_now, 4),
            "position": round(x.position, 3), "position_text": channels.position_text(x.position),
            "broken": x.broken,
        }

    def lv_dict(x):
        d = asdict(x)
        d["last_touch_jst"] = jst(x.last_touch_index) if x.last_touch_index >= 0 else None
        return d

    def sw_dict(s):
        return {"index": s.index, "price": s.price, "kind": s.kind, "jst": jst(s.index)}

    def zone_dict(z: zones.Zone) -> dict:
        return {"low": round(z.low, 4), "high": round(z.high, 4), "center": round(z.center, 4), "side": z.side,
                "score": z.score, "kinds": z.kinds(), "reasons": z.reasons(),
                "distance_pips": z.distance_pips, "distance_atr": z.distance_atr,
                "distance_text": zones.distance_text(z.distance_atr)}

    def fib_dict(f):
        if f is None:
            return None
        return {"direction": f.direction, "wave": f.wave, "start_index": f.start_index, "start_price": f.start_price,
                "start_jst": jst(f.start_index), "end_index": f.end_index, "end_price": f.end_price,
                "end_jst": jst(f.end_index), "levels": {str(k): round(v, 4) for k, v in f.levels.items()},
                "extensions": {str(k): round(v, 4) for k, v in f.extensions.items()},
                "projections": {str(k): round(v, 4) for k, v in f.projections.items()},
                "ext_base_index": f.ext_base_index, "ext_base_price": f.ext_base_price,
                "ext_base_jst": jst(f.ext_base_index) if f.ext_base_index is not None else None,
                "current_ratio": round(f.current_ratio, 3) if f.current_ratio is not None else None,
                "current_band": f.current_band, "wave_pips": round((f.end_price - f.start_price) / pip, 1)}

    fib_d = fib_dict(fib)

    div_d = []
    for dv in divs:
        d = asdict(dv)
        d["t1_jst"], d["t2_jst"] = jst(dv.i1), jst(dv.i2)
        div_d.append(d)

    if slot is None:
        slot = "morning" if now.astimezone(tz).hour < int(cfg.get("posting", {}).get("morning_slot_hour_end", 15)) else "evening"

    result = {
        "symbol": cfg["symbol"],
        "timeframe": tf,
        "source": source,
        "timeframe_label": tcfg["label"],
        "slot": slot,
        "analyzed_at_jst": now.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
        "last_bar_jst": last_bar_jst.strftime("%Y-%m-%d %H:%M"),
        "last_bar_utc": last_bar.isoformat(),
        "confirmed": asdict(cinfo),
        "bars": n,
        "close": close_now,
        "atr": round(atr_now, 4),
        "pip": pip,
        "ema_fast_period": int(tcfg["ema_fast"]),
        "ema_slow_period": int(tcfg["ema_slow"]),
        "ema_long_period": ema_long_period or None,
        "trend": {"label": tr.label, "direction": tr.direction, "score": tr.score, "details": tr.details,
                  "label_effective": label_eff, "direction_effective": dir_eff, "caveat": caveat},
        "structure": {**asdict(dow), "key_jst": jst(dow.key_time_index) if dow.key_time_index is not None else None,
                      "top_jst": jst(dow.top_index) if dow.top_index is not None else None,
                      "flipped_jst": jst(dow.flipped_index) if dow.flipped_index is not None else None,
                      "major_swings": [sw_dict(s) for s in major[-8:]]},
        "supports": [lv_dict(x) for x in sup],
        "resistances": [lv_dict(x) for x in res],
        "channel": ch_dict(ch),
        "trendline_up": tl_dict(tl_up),
        "trendline_down": tl_dict(tl_dn),
        "swing_highs": [sw_dict(s) for s in zz_highs[-6:]],
        "swing_lows": [sw_dict(s) for s in zz_lows[-6:]],
        "fibonacci": fib_d,
        "fibonacci_target": fib_dict(fib_t),
        "divergences": div_d,
        "rsi": rsi_sum,
        "sqzmom": sqz,
        "atr_context": atr_ctx,
        "daily": asdict(dl) if dl else None,
        "higher_timeframe": ({"ema_period": dl.daily_ema["period"], "close": dl.daily_ema["close"], "ema": dl.daily_ema["value"],
                              "above": dl.daily_ema["above"], "date": dl.daily_ema["date"]} if dl and dl.daily_ema else None),
        "zones": {"above": [zone_dict(z) for z in z_above], "below": [zone_dict(z) for z in z_below]},
    }
    result["scenarios"] = commentary.scenarios(result)
    # 前回との変化点（台帳）。前回が同じ銘柄・時間足・データ源で、今回より新しくないときだけ使う
    prev, why_not = ledger.usable(prev, symbol=cfg["symbol"], timeframe=tf, source=source,
                                  last_bar_utc=result["last_bar_utc"], index=df_conf.index)
    if prev is not None:
        prev_last = pd.Timestamp(prev["last_bar_utc"])
        recent = df_conf[df_conf.index > prev_last]
        result["changes"] = ledger.changes_since(prev, result, recent, reach_tol=atr_now * float(tol_cfg.get("reach_atr", 0.3)), pip=pip)
        # 答え合わせ（前回のシナリオを、前回より後の確定足で判定。朝は「昨夜のプラン」、夜は「朝のプラン」）
        if bool(cfg.get("posting", {}).get("answer_check", True)):
            result["changes"]["verdict"] = ledger.judge_scenarios(prev, recent, reach_tol=atr_now * float(tol_cfg.get("reach_atr", 0.3)))
    else:
        result["changes"] = {"available": False, "lines": [why_not] if why_not else [], "reactions": []}
    result["commentary"] = commentary.build(result, cfg.get("posting", {}))
    result["_arrays"] = {"ema_fast": ema_f, "ema_slow": ema_s, "ema_long": ema_l, "rsi": rsi}
    result["_df"] = df
    return result


def run(df: pd.DataFrame, cfg: dict, out_dir: str | Path, tf: str = "4h",
        df_daily: pd.DataFrame | None = None, stem: str | None = None, now: datetime | None = None,
        slot: str | None = None, use_ledger: bool | None = None, source: str | None = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if use_ledger is None:
        use_ledger = bool(cfg.get("ledger", {}).get("enabled", True))
    if source == "sample":          # 架空データの結果を「前回」として残さない
        use_ledger = False
    prev = ledger.load_last(out_dir / "state") if use_ledger else None
    result = analyze(df, cfg, tf, df_daily, now=now, slot=slot, prev=prev, source=source)
    stamp = result["analyzed_at_jst"].replace("-", "").replace(" ", "_").replace(":", "")
    stem = stem or f"{cfg['symbol']}_{tf}_{stamp}"
    tcfg = cfg["timeframes"][tf]
    ocfg = cfg.get("output", {})
    arrays = result.pop("_arrays")
    df_used = result.pop("_df")
    png = chart.render(df_used, result, out_dir / f"{stem}.png",
                       bars_to_plot=int(tcfg["bars_to_plot"]), tz=cfg.get("timezone", "Asia/Tokyo"),
                       width_px=int(ocfg.get("image_width_px", 1600)), height_px=int(ocfg.get("image_height_px", 900)),
                       dpi=int(ocfg.get("dpi", 100)), ema_fast=arrays["ema_fast"], ema_slow=arrays["ema_slow"],
                       ema_long=arrays["ema_long"], rsi=arrays["rsi"], style_cfg=cfg.get("chart"))
    md = out_dir / f"{stem}.md"
    cm = result["commentary"]
    evidence = "\n".join(f"- {e}" for e in cm.get("evidence", []))
    slot_label = "朝のプラン" if result["slot"] == "morning" else "中間報告"
    md.write_text(
        f"# {result['symbol']} {result['timeframe_label']} {slot_label}（{result['analyzed_at_jst']} JST）\n\n"
        f"![chart]({png.name})\n\n## 解説\n\n{cm['long']}\n\n"
        f"## シナリオ表\n\n{cm['table']}\n\n"
        f"## 根拠（線 1 本ごと）\n\n{evidence}\n\n"
        f"## X投稿案（DRY RUN・未投稿・{cm.get('post_style', 'short')}・{cm.get('x_units', 0)} 単位）\n\n```\n{cm['post']}\n```\n\n"
        + "".join(f"### 返信 {i + 1}（{u} 単位）\n\n```\n{r}\n```\n\n" for i, (r, u) in enumerate(zip(cm.get("post_replies") or [], cm.get("reply_units") or [])))
        + (f"## 表現チェック\n\n見つかった語：{', '.join(cm['safety_hits'])}\n" if cm.get("safety_hits") else "")
        + ("## 注意\n\nX 投稿案が文字数上限を超えています。短くしてから投稿してください。\n" if cm.get("post_over_limit") else ""),
        encoding="utf-8")
    js = out_dir / f"{stem}.json"
    js.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    result["files"] = {"png": str(png), "md": str(md), "json": str(js)}
    if use_ledger:
        ledger.save(result, out_dir)
    return result


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)
