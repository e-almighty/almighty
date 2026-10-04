"""勢い・値幅の文脈：SQZMOM（文章のみ）、RSI の現在値、ATR の位置づけ。

SQZMOM は画像に描かない（SHO 2026-10-04）。解説文に 1 行だけ入れる。
  「いつ動きやすいか」を示す指標で、「どちらへ」は示さない、と役割を分けて書く。
ATR は「値幅の目安」としてだけ使う（pips と、過去 N 本の中での位置づけ）。
"""
from __future__ import annotations

import numpy as np

from . import indicators


def _runs(mask: np.ndarray) -> list[int]:
    out, cur = [], 0
    for v in mask:
        if v:
            cur += 1
        else:
            if cur:
                out.append(cur)
            cur = 0
    if cur:
        out.append(cur)
    return out


def sqzmom_summary(high, low, close, *, bb_length: int, bb_mult: float, kc_length: int, kc_mult: float,
                   window: int = 300) -> dict | None:
    val, on, off = indicators.sqzmom(high, low, close, bb_length, bb_mult, kc_length, kc_mult)
    if len(val) < kc_length + 5 or np.isnan(val[-1]):
        return None
    v = val[-window:]
    on_w = on[-window:]
    # 現在のスクイーズ状態と継続本数
    streak = 0
    for x in on_w[::-1]:
        if x:
            streak += 1
        else:
            break
    runs = _runs(on_w)
    median_run = float(np.median(runs)) if runs else None
    # 解放からの本数（直近でスクイーズが終わった位置）
    since_release = None
    if streak == 0:
        idx = np.where(on_w)[0]
        if len(idx):
            since_release = int(len(on_w) - 1 - idx[-1])
    # モメンタムの色（LazyBear の 4 色）と連続縮小/拡大の本数
    v1, v0 = float(v[-1]), float(v[-2])
    if v1 > 0:
        color = "lime" if v1 > v0 else "green"
    else:
        color = "red" if v1 < v0 else "maroon"
    k = 1
    while k < min(len(v) - 1, 10):
        a, b = float(v[-k]), float(v[-k - 1])
        same = (abs(a) > abs(b)) == (abs(v1) > abs(v0)) and (np.sign(a) == np.sign(v1))
        if not same:
            break
        k += 1
    expanding = abs(v1) > abs(v0)
    if on_w[-1]:
        length_note = ""
        if median_run:
            length_note = "（過去の継続の中央値 " + f"{median_run:.0f} 本より" + ("長め）" if streak > median_run else "短め）")
        state = f"スクイーズ中（{streak} 本連続{length_note}）。値動きが圧縮されており、解放後に大きめの動きが出やすい局面"
    elif since_release is not None and since_release <= 6:
        state = f"スクイーズ解放から {since_release + 1} 本目。動き出した直後で、方向はモメンタムの符号を参考にする局面"
    else:
        state = "スクイーズなし（値動きは圧縮されていない）"
    sign = "プラス" if v1 > 0 else "マイナス"
    mom = f"モメンタムは{sign}で{'拡大' if expanding else '縮小'}中（{k} 本連続）"
    text = f"SQZMOM：{state}。{mom}。※この指標は「いつ動きやすいか」の目安で、方向は示しません。"
    return {"value": round(v1, 4), "prev": round(v0, 4), "color": color, "squeeze_on": bool(on_w[-1]),
            "streak": streak, "median_run": median_run, "since_release": since_release,
            "expanding": expanding, "consecutive": k, "text": text}


def rsi_summary(rsi: np.ndarray) -> dict | None:
    if len(rsi) < 3 or np.isnan(rsi[-1]):
        return None
    from .divergence import rsi_zone_text
    r = float(rsi[-1])
    r3 = float(rsi[-4]) if len(rsi) >= 4 and not np.isnan(rsi[-4]) else r
    slope = "上向き" if r - r3 > 2 else ("下向き" if r - r3 < -2 else "横ばい")
    return {"value": round(r, 1), "zone": rsi_zone_text(r), "slope": slope}


def atr_context(atr: np.ndarray, pip: float, *, percentile_bars: int, low_pct: float, high_pct: float,
                daily_atr: float | None = None, today: dict | None = None) -> dict:
    a = float(atr[-1])
    hist = atr[-percentile_bars:]
    hist = hist[~np.isnan(hist)]
    pct = float((hist < a).mean() * 100) if len(hist) else 50.0
    level = "低め" if pct < low_pct else ("高め" if pct > high_pct else "標準的")
    out = {"atr": round(a, 4), "atr_pips": round(a / pip, 1), "percentile": round(pct, 0), "level": level,
           "daily_atr": None, "daily_atr_pips": None, "today_range_pips": None, "today_ratio": None}
    if daily_atr:
        out["daily_atr"] = round(daily_atr, 4)
        out["daily_atr_pips"] = round(daily_atr / pip, 1)
        if today:
            rng = today["high"] - today["low"]
            out["today_range_pips"] = round(rng / pip, 1)
            out["today_ratio"] = round(rng / daily_atr, 2) if daily_atr > 0 else None
    return out


def atr_text(ctx: dict) -> str:
    t = (f"値幅の目安：4時間足の ATR(14) は {ctx['atr_pips']:.0f} pips で、過去 {int(ctx['percentile'])} ％の足より大きい"
         f"（{ctx['level']}）。")
    if ctx.get("daily_atr_pips"):
        t += f" 日足の ATR(14) は {ctx['daily_atr_pips']:.0f} pips（1 日の値幅の目安）。"
        if ctx.get("today_ratio") is not None:
            r = ctx["today_ratio"]
            note = "まだ余地があります" if r < 0.4 else ("平均的な消化です" if r < 0.8 else "1 日分をほぼ出し切っています")
            t += f" 本日ここまでの値幅は {ctx['today_range_pips']:.0f} pips（日足 ATR の {r * 100:.0f} ％、{note}）。"
    return t
