"""投稿用チャート画像（PNG）。

描くもの（docs/ANALYSIS_RULES.md「投稿画像」）:
  銘柄・時間足・現在値・分析日時／ローソク足／サポート（赤・太線）／レジスタンス（緑・太線）
  平行チャネル（紫＝上限・下限、薄紫の破線＝中央）／EMA20（橙）・50（青）・200（黒太線）／右端に名前入りの価格ラベル
  第2ステージ：フィボ 38.2／50／61.8（金の細い破線）／押し安値・戻り高値（点線）／前日高安（灰の破線）
              注目価格帯（薄い帯）／RSI のサブパネル（30・70 と、ダイバージェンスの線）
  画像の仕上げ（リサーチ 9 章の 6・7、2026-10-07）：上端にタイトル帯（投稿の 1 行目と同じ文言）、最下段に 🔑 結論 1 行、
              注目帯は上下 1 つずつ、シナリオの矢印（メイン＝実線、サブ＝点線、崩れる価格＝赤点線）、
              夜は朝のプランの帯と実際の到達を塗り足す。2 枚目に日足（EMA50・前週高安・押し安値だけ）。
ラインは多すぎないこと。サポレジ各 1〜3 本、チャネルは 1 組、フィボは 3 本、前日高安 2 本、押し安値 1 本。
SQZMOM は描かない（SHO 2026-10-04）。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mplfinance as mpf  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

# 日本語が出るフォントを上から順に探す（Windows → Mac → Linux）
FONT_CANDIDATES = ["Meiryo", "Yu Gothic", "Yu Gothic UI", "MS Gothic", "Hiragino Sans",
                   "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "IPAGothic",
                   "WenQuanYi Zen Hei", "Unifont-JP", "DejaVu Sans"]

# 見た目の既定値。config/analysis.yaml の chart: で上書きできる
DEFAULT_STYLE = {
    "support_color": "#d62828",     # サポート＝赤（SHO の指定・2026-10-04）
    "resistance_color": "#1b9e4b",  # レジスタンス＝緑（SHO の指定・2026-10-04）
    "level_linewidth": 2.8,
    "level_label_size": 11,
    "channel_color": "#6a1b9a",
    "channel_center_color": "#b39ddb",
    "channel_linewidth": 1.8,
    "ema_fast_color": "#f39c12",
    "ema_slow_color": "#2980b9",
    "ema_long_color": "#111111",
    "ema_long_width": 2.4,
    "draw_fib": True,
    "draw_key_level": True,
    "draw_prev_day": True,
    "draw_zones": True,
    "draw_rsi_panel": True,
    "draw_divergence": True,
    "fib_color": "#c8a000",
    "key_level_color": "#8e2d2d",
    "prev_day_color": "#888888",
    "zone_above_color": "#1b9e4b",
    "zone_below_color": "#d62828",
    "zone_alpha": 0.10,
    "rsi_color": "#5b2c6f",
    "divergence_color": "#00897b",     # 青緑（EMA20 の橙と見分けるため）
    # 画像の仕上げ（2026-10-07）
    "title_band": True,                # 上端の帯に投稿の 1 行目（【今日のドル円】… が分かれ目）を焼き込む
    "title_band_color": "#1f2a44",     # 帯の色（濃紺）。文字は白
    "footer_hook": True,               # 最下段に 🔑 結論 1 行を焼き込む
    "footer_color": "#fff6d5",         # 結論の帯の色（薄い黄）
    "zones_draw_each_side": 1,         # 注目帯を上下いくつ描くか（リサーチ：各 1 つ）
    "draw_scenario_arrows": True,      # メイン＝実線の矢印、サブ＝点線の矢印、崩れる価格＝赤の点線
    "scenario_up_color": "#1b9e4b",
    "scenario_down_color": "#d62828",
    "invalid_color": "#c62828",
    "evening_overlay": True,           # 夜：朝のプランの帯（発動価格→行き先）と、朝以降の実際の高値／安値を塗り足す
    "morning_band_color": "#ffb300",
}
COLOR_NOW = "#444444"
STATUS_COLOR = {"到達": "#1b9e4b", "発動": "#1565c0", "未発動": "#666666", "無効化": "#c62828", "発動→崩れ": "#c62828"}


def pick_font() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for c in FONT_CANDIDATES:
        if c in names:
            return c
    return "DejaVu Sans"


def font_has(font_name: str, ch: str) -> bool:
    """そのフォントに文字（絵文字など）があるか。無ければ呼び出し側で別の表記にする。"""
    try:
        from matplotlib.ft2font import FT2Font
        path = font_manager.findfont(font_manager.FontProperties(family=font_name), fallback_to_default=False)
        return FT2Font(path).get_char_index(ord(ch)) != 0
    except Exception:
        return False


def _wrap(text: str, width: int) -> list[str]:
    """全角 1・半角 0.5 で数えて width ごとに折り返す（最大 2 行）。"""
    lines, cur, w = [], "", 0.0
    for ch in text:
        cw = 0.5 if ord(ch) < 128 else 1.0
        if w + cw > width and cur:
            lines.append(cur); cur, w = "", 0.0
        cur += ch; w += cw
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][:-1] + "…"
    return lines


def _draw_title_band(fig, st: dict, title: str, right_text: str, sub: str, legend: str) -> None:
    """上端の帯：左に投稿の 1 行目（刺さるタイトル）、右に相場環境と現在値。帯の下に分析日時と凡例。"""
    fig.patches.append(Rectangle((0, 0.925), 1, 0.075, transform=fig.transFigure, color=st["title_band_color"], zorder=0))
    fig.text(0.015, 0.9625, title, ha="left", va="center", fontsize=17, fontweight="bold", color="white")
    if right_text:
        fig.text(0.985, 0.9625, right_text, ha="right", va="center", fontsize=12, fontweight="bold", color="white")
    fig.text(0.015, 0.906, sub, ha="left", va="center", fontsize=9.5, color="#333333")
    fig.text(0.985, 0.906, legend, ha="right", va="center", fontsize=8, color="#666666")


def _draw_footer(fig, st: dict, font: str, hook: str, disclaimer: str) -> None:
    """最下段の帯：🔑 結論 1 行（フォントに絵文字が無ければ「結論」の札）。右端に免責。"""
    fig.patches.append(Rectangle((0, 0), 1, 0.072, transform=fig.transFigure, color=st["footer_color"], zorder=0))
    if hook:
        lines = _wrap(hook, 62)
        if font_has(font, "🔑"):
            text = "🔑 " + "\n".join(lines)
        else:
            fig.text(0.015, 0.036, "結論", ha="left", va="center", fontsize=10.5, fontweight="bold", color="white",
                     bbox=dict(boxstyle="round,pad=0.3", fc=st["title_band_color"], ec=st["title_band_color"]))
            text = "\n".join(lines)
        fig.text(0.052 if not font_has(font, "🔑") else 0.015, 0.036, text, ha="left", va="center",
                 fontsize=12.5 if len(lines) == 1 else 11, fontweight="bold", color="#222222", linespacing=1.25)
    fig.text(0.985, 0.012, disclaimer, ha="right", va="bottom", fontsize=7.5, color="#777777")


def _stack(labels: list[tuple], y_lo: float, y_hi: float, frac: float = 0.034) -> list[float]:
    """近すぎるラベルを上下にずらす。labels は (price, ...) の並び（価格順にソート済み）。"""
    min_gap = (y_hi - y_lo) * frac
    ys = [t[0] for t in labels]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < min_gap:
            ys[i] = ys[i - 1] + min_gap
    # 上端からはみ出したら、全体を下にずらす（下端は y_lo まで）
    over = ys[-1] - (y_hi - min_gap * 0.5) if ys else 0.0
    if over > 0:
        ys = [max(y - over, y_lo + min_gap * 0.5) for y in ys]
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < min_gap:
                ys[i] = ys[i - 1] + min_gap
    return ys


def render(df: pd.DataFrame, result: dict, out_path: str | Path, *, bars_to_plot: int,
           tz: str, width_px: int = 1600, height_px: int = 900, dpi: int = 100,
           ema_fast=None, ema_slow=None, ema_long=None, rsi=None, style_cfg: dict | None = None) -> Path:
    """df: UTC index の OHLC（解析に使った確定足）。result: pipeline.analyze() の戻り値。"""
    st = {**DEFAULT_STYLE, **(style_cfg or {})}
    COLOR_SUPPORT, COLOR_RESIST = st["support_color"], st["resistance_color"]
    COLOR_CH, COLOR_CHC = st["channel_color"], st["channel_center_color"]
    font = pick_font()
    plot_df = df.tail(bars_to_plot).copy()
    plot_df.index = plot_df.index.tz_convert(tz)
    plot_df = plot_df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    offset = len(df) - len(plot_df)           # 解析の足番号 → 描画の足番号
    n = len(plot_df)
    use_rsi = bool(st["draw_rsi_panel"]) and rsi is not None and len(rsi) >= n and not np.all(np.isnan(rsi[-n:]))

    style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        rc={"font.family": font, "font.size": 11, "axes.unicode_minus": False},
        gridstyle=":", gridcolor="#dddddd", facecolor="white", figcolor="white",
    )

    adds = []
    if ema_fast is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_fast[-n:], index=plot_df.index), color=st["ema_fast_color"], width=1.0))
    if ema_slow is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_slow[-n:], index=plot_df.index), color=st["ema_slow_color"], width=1.2))
    if ema_long is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_long[-n:], index=plot_df.index), color=st["ema_long_color"], width=float(st["ema_long_width"])))
    if use_rsi:
        adds.append(mpf.make_addplot(pd.Series(rsi[-n:], index=plot_df.index), panel=1, color=st["rsi_color"], width=1.3))

    # 縦軸の範囲：描く足の高安 ± ATR。その近く（±2ATR）にある線は範囲を少し広げて入れる。遠い線は描かない
    atr_v = float(result.get("atr") or 0.0)
    pad = max(atr_v * 1.0, 0.05)
    y_lo = float(plot_df["Low"].min()) - pad
    y_hi = float(plot_df["High"].max()) + pad
    ch = result.get("channel")
    extra = [lv["price"] for lv in result["supports"] + result["resistances"]]
    if ch:
        extra += [ch["lower_now"], ch["upper_now"]]
    for p in extra:
        if y_lo - 2 * atr_v <= p <= y_hi + 2 * atr_v:
            y_lo = min(y_lo, p - pad * 0.5)
            y_hi = max(y_hi, p + pad * 0.5)

    def visible(p: float) -> bool:
        return y_lo <= p <= y_hi

    vis_sup = [lv for lv in result["supports"] if visible(lv["price"])]
    vis_res = [lv for lv in result["resistances"] if visible(lv["price"])]

    hl_prices, hl_colors = [], []
    for lv in vis_sup:
        hl_prices.append(lv["price"]); hl_colors.append(COLOR_SUPPORT)
    for lv in vis_res:
        hl_prices.append(lv["price"]); hl_colors.append(COLOR_RESIST)
    hlines = dict(hlines=hl_prices, colors=hl_colors, linestyle="-", linewidths=float(st["level_linewidth"]), alpha=0.95) if hl_prices else None

    kwargs = dict(type="candle", style=style, figsize=(width_px / dpi, height_px / dpi),
                  returnfig=True, datetime_format="%m/%d %H:%M", xrotation=0, ylabel="",
                  tight_layout=False, scale_padding={"left": 1.0, "right": 2.6, "top": 1.1, "bottom": 0.6})
    if adds:
        kwargs["addplot"] = adds
    if hlines:
        kwargs["hlines"] = hlines
    if use_rsi:
        kwargs["panel_ratios"] = (4, 1)
    fig, axes = mpf.plot(plot_df, **kwargs)
    ax = axes[0]
    ax_rsi = axes[2] if use_rsi and len(axes) > 2 else None
    # 余白を詰めて横幅を使う（mplfinance の既定は左右の余白が大きい）
    x0, w = 0.055, 0.735
    band = bool(st["title_band"]) and bool(((result.get("commentary") or {}).get("title_line")))
    foot = bool(st["footer_hook"]) and bool(((result.get("commentary") or {}).get("hook")))
    top = 0.885 if band else 0.90
    bottom = 0.115 if foot else 0.075
    if ax_rsi is not None:
        for a in axes[:2]:
            a.set_position([x0, bottom + 0.165, w, top - bottom - 0.165])
        for a in axes[2:4]:
            a.set_position([x0, bottom, w, 0.135])
    else:
        for a in axes[:2]:
            a.set_position([x0, bottom, w, top - bottom])
    ax.set_ylim(y_lo, y_hi)
    ax.yaxis.tick_left()
    ax.yaxis.set_label_position("left")
    sc = result.get("scenarios") or {}
    arrows_on = bool(st["draw_scenario_arrows"]) and any((sc.get(k) or {}).get("trigger") and (sc.get(k) or {}).get("target") for k in ("up", "down"))
    margin = 7.0 if arrows_on else 0.8          # 右端に矢印用の余白（足 7 本ぶん）を空け、その右に価格ラベル
    for a in axes:
        a.set_xlim(-1.0, n + margin)
    x_right = n + margin - 0.2

    # 注目価格帯（薄い帯）
    zones = result.get("zones") or {}
    if st["draw_zones"]:
        for side, color in (("above", st["zone_above_color"]), ("below", st["zone_below_color"])):
            for z in zones.get(side, [])[:max(0, int(st.get("zones_draw_each_side", 1)))]:
                lo, hi = z["low"], z["high"]
                if hi - lo < atr_v * 0.16:              # 細すぎる帯は最低幅（0.16 ATR）に広げる
                    mid = (lo + hi) / 2.0
                    lo, hi = mid - atr_v * 0.08, mid + atr_v * 0.08
                if hi < y_lo or lo > y_hi:
                    continue
                ax.axhspan(lo, hi, color=color, alpha=float(st["zone_alpha"]), zorder=0.5, lw=0)

    # 平行チャネル（上限・下限＝実線、中央＝破線）
    ch_labels = []
    if ch:
        i1 = max(ch["i1"] - offset, 0)
        i2 = n - 1

        def ch_val(i_plot: int, which: str) -> float:
            base = ch["p1"] + ch["slope"] * (i_plot + offset - ch["i1"])
            lower, upper = (base, base + ch["offset"]) if ch["kind"] == "up" else (base - ch["offset"], base)
            return {"lower": lower, "upper": upper, "center": (lower + upper) / 2.0}[which]
        lw = float(st["channel_linewidth"])
        for which, color, ls, w in (("lower", COLOR_CH, "-", lw), ("upper", COLOR_CH, "-", lw), ("center", COLOR_CHC, "--", lw * 0.8)):
            ax.plot([i1, i2], [ch_val(i1, which), ch_val(i2, which)], color=color, linestyle=ls, linewidth=w, alpha=0.95, zorder=3)
        name = "上昇CH" if ch["kind"] == "up" else "下降CH"
        ch_labels = [(ch["upper_now"], f"{name}上限 {ch['upper_now']:.3f}", COLOR_CH),
                     (ch["center_now"], f"{name}中央 {ch['center_now']:.3f}", COLOR_CHC),
                     (ch["lower_now"], f"{name}下限 {ch['lower_now']:.3f}", COLOR_CH)]

    # 左側に名前を出す細い線：フィボ／押し安値／前日高安
    left_labels: list[tuple[float, str, str]] = []
    fib = result.get("fibonacci")
    if st["draw_fib"] and fib:
        draw_levels = [float(x) for x in (st.get("fib_draw_levels") or [0.382, 0.5, 0.618])]
        for k, p in fib["levels"].items():
            if float(k) in draw_levels and visible(p):
                ax.axhline(p, color=st["fib_color"], linestyle=(0, (6, 4)), linewidth=1.1, alpha=0.9, zorder=2)
                left_labels.append((p, f"フィボ {float(k) * 100:.1f}%  {p:.3f}", st["fib_color"]))
    stc = result.get("structure") or {}
    if st["draw_key_level"] and stc.get("key_level") is not None and visible(stc["key_level"]):
        nm = "押し安値" if stc.get("direction") == "up" else "戻り高値"
        ax.axhline(stc["key_level"], color=st["key_level_color"], linestyle=":", linewidth=1.6, alpha=0.95, zorder=2)
        left_labels.append((stc["key_level"], f"{nm}  {stc['key_level']:.3f}", st["key_level_color"]))
    dl = result.get("daily") or {}
    if st["draw_prev_day"] and dl.get("prev_day"):
        p = dl["prev_day"]
        for nm, v in (("前日高値", p["high"]), ("前日安値", p["low"])):
            if visible(v):
                ax.axhline(v, color=st["prev_day_color"], linestyle="--", linewidth=1.0, alpha=0.9, zorder=2)
                left_labels.append((v, f"{nm}  {v:.3f}", st["prev_day_color"]))

    # ダイバージェンスの線（価格側と RSI 側）
    divs = result.get("divergences") or []
    if st["draw_divergence"]:
        for d in divs:
            x1, x2 = d["i1"] - offset, d["i2"] - offset
            if x2 < 0:
                continue
            ax.plot([x1, x2], [d["p1"], d["p2"]], color=st["divergence_color"], linewidth=1.8, alpha=0.95, zorder=4)
            ax.annotate(d["label"].replace("ダイバージェンス", "ダイバ"), xy=((x1 + x2) / 2.0, (d["p1"] + d["p2"]) / 2.0),
                        xytext=(0, 10 if "bear" in d["kind"] else -14), textcoords="offset points", ha="center",
                        fontsize=9, color=st["divergence_color"], fontweight="bold")
            if ax_rsi is not None:
                ax_rsi.plot([x1, x2], [d["r1"], d["r2"]], color=st["divergence_color"], linewidth=1.8, alpha=0.95, zorder=4)

    # RSI パネル：30／70／50
    if ax_rsi is not None:
        ax_rsi.axhline(70, color="#999999", linestyle="--", linewidth=0.8)
        ax_rsi.axhline(30, color="#999999", linestyle="--", linewidth=0.8)
        ax_rsi.axhline(50, color="#cccccc", linestyle=":", linewidth=0.8)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.yaxis.tick_left()
        ax_rsi.yaxis.set_label_position("left")
        ax_rsi.set_yticks([30, 50, 70])
        ax_rsi.text(0.004, 0.96, "RSI(14)", transform=ax_rsi.transAxes, fontsize=9, color=st["rsi_color"], va="top", ha="left")
        r_now = float(rsi[-1])
        ax_rsi.text(x_right, r_now, f"RSI {r_now:.1f}", color=st["rsi_color"], fontsize=9.5, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=st["rsi_color"], lw=0.8))

    # シナリオの矢印（右端の余白に）：メイン＝実線、サブ＝点線（発動価格 → 行き先）。崩れる価格＝赤の点線（右のラベル列に「崩れる条件」）
    invalid_label = None
    if arrows_on:
        for side in ("up", "down"):
            s_ = sc.get(side) or {}
            if not (s_.get("trigger") and s_.get("target")):
                continue
            p1, p2 = float(s_["trigger"]["price"]), float(s_["target"]["price"])
            if not visible(p1):
                continue
            p2c = min(max(p2, y_lo + pad * 0.2), y_hi - pad * 0.2)   # 行き先が枠外なら枠の端まで
            is_main = sc.get("main") == side
            x_arrow = n + (1.6 if is_main else 4.3)
            color = st["scenario_up_color"] if side == "up" else st["scenario_down_color"]
            arr = FancyArrowPatch((x_arrow, p1), (x_arrow, p2c), arrowstyle="-|>", mutation_scale=18,
                                  color=color, linewidth=2.6 if is_main else 1.6,
                                  linestyle="-" if is_main else (0, (3, 3)), alpha=0.95, zorder=5)
            ax.add_patch(arr)
            ax.plot([n - 0.3, x_arrow], [p1, p1], color=color, linewidth=0.9, linestyle=":", alpha=0.8, zorder=4)   # 発動価格から矢印へ
            ax.text(x_arrow + 1.15, (p1 + p2c) / 2.0, "メイン" if is_main else "サブ", rotation=90, ha="center", va="center",
                    fontsize=8, fontweight="bold", color=color, zorder=6)
            if is_main and s_.get("invalid") and visible(float(s_["invalid"]["price"])):
                pi = float(s_["invalid"]["price"])
                ax.plot([n * 0.8, x_right - 0.3], [pi, pi], color=st["invalid_color"], linestyle=(0, (2, 2)), linewidth=1.5, zorder=4)
                invalid_label = (pi, f"崩れる条件 {pi:.3f}", st["invalid_color"], "outline")

    # 夜：朝のプラン（発動価格 → 行き先）の帯と、朝以降の実際の高値／安値を塗り足す（答え合わせが絵で分かるように）
    verdict = (result.get("changes") or {}).get("verdict") or {}
    m = verdict.get("main_side") if isinstance(verdict, dict) else None
    if st["evening_overlay"] and result.get("slot") == "evening" and m and m.get("trigger") and verdict.get("prev_at"):
        try:
            prev_at = pd.Timestamp(verdict["prev_at"]).tz_localize(tz)
            i0 = int(np.searchsorted(plot_df.index.values, prev_at.tz_convert("UTC").to_datetime64()))
        except Exception:
            i0 = None
        if i0 is not None and 0 <= i0 < n:
            up = verdict.get("main") == "up"
            trig, tgt = float(m["trigger"]), float(m["target"]) if m.get("target") else None
            lo_b, hi_b = (trig, tgt) if tgt is not None else (trig - atr_v * 0.1, trig + atr_v * 0.1)
            lo_b, hi_b = min(lo_b, hi_b), max(lo_b, hi_b)
            lo_b, hi_b = max(lo_b, y_lo), min(hi_b, y_hi)
            if hi_b > lo_b:
                ax.fill_between([i0 - 0.5, n - 0.5], lo_b, hi_b, color=st["morning_band_color"], alpha=0.16, zorder=0.6, lw=0)
            ax.axvline(i0 - 0.5, color=st["morning_band_color"], linestyle="--", linewidth=1.0, alpha=0.9, zorder=1)
            status = m.get("status", "")
            sc_col = STATUS_COLOR.get(status, "#666666")
            label = f"朝のプラン {trig:.3f}→{tgt:.3f}" if tgt is not None else f"朝のプラン {trig:.3f}"
            ax.text(i0 - 1.0, min(hi_b, y_hi) if up else max(lo_b, y_lo), f"{label}  {status}", color=sc_col, fontsize=9, fontweight="bold",
                    ha="right", va="bottom" if up else "top", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=sc_col, lw=0.8, alpha=0.9))
            seg = plot_df.iloc[i0:]
            if len(seg):
                if up:
                    j = int(seg["High"].to_numpy().argmax()); px = float(seg["High"].iloc[j]); nm = "朝以降の高値"
                else:
                    j = int(seg["Low"].to_numpy().argmin()); px = float(seg["Low"].iloc[j]); nm = "朝以降の安値"
                if visible(px):
                    ax.plot([i0 + j], [px], marker="v" if up else "^", color=sc_col, markersize=9, zorder=7)
                    ax.text(i0 + j - 0.6, px, f"{nm} {px:.3f}", color=sc_col, fontsize=8.5, fontweight="bold",
                            ha="right", va="bottom" if up else "top", zorder=7,
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=sc_col, lw=0.6, alpha=0.85))

    # 現在値（点線）
    close_now = result["close"]
    ax.axhline(close_now, color=COLOR_NOW, linestyle=":", linewidth=1.0)

    # 右端の価格ラベル（色付きの箱で「サポート／レジスタンス」と明記。近すぎるラベルは上下にずらす）
    fs = float(st["level_label_size"])
    labels = [(lv["price"], f"サポート {lv['price']:.3f}", COLOR_SUPPORT, "fill") for lv in vis_sup]
    labels += [(lv["price"], f"レジスタンス {lv['price']:.3f}", COLOR_RESIST, "fill") for lv in vis_res]
    labels.append((close_now, f"現在 {close_now:.3f}", COLOR_NOW, "outline"))
    labels += [(p, t, c, "outline") for (p, t, c) in ch_labels if visible(p)]
    if invalid_label:
        labels.append(invalid_label)
    labels.sort(key=lambda t: t[0])
    ys = _stack(labels, y_lo, y_hi)
    for (price, text, color, kind), y in zip(labels, ys):
        if kind == "fill":
            ax.text(x_right, y, text, color="white", fontsize=fs, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc=color, ec=color, lw=1.0))
        else:
            ax.text(x_right, y, text, color=color, fontsize=fs - 1, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.9))

    # 左端の小さなラベル（フィボ・押し安値・前日高安）
    if left_labels:
        left_labels.sort(key=lambda t: t[0])
        ys = _stack(left_labels, y_lo, y_hi, frac=0.03)
        for (price, text, color), y in zip(left_labels, ys):
            ax.text(0.3, y, text, color=color, fontsize=8.5, va="center", ha="left",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.6, alpha=0.9), zorder=6)

    # タイトル（帯）：投稿の 1 行目をそのまま焼き込む（画像だけ見ても争点が分かる）。帯を使わないときは従来の見出し
    tr = result["trend"]
    label = tr.get("label_effective", tr["label"])
    slot = result.get("slot")
    slot_txt = "（朝のプラン）" if slot == "morning" else ("（中間報告）" if slot == "evening" else "")
    title = f"{result['symbol']} {result['timeframe_label']}{slot_txt}   相場環境：{label}"
    conf = result.get("confirmed") or {}
    sub = f"分析日時 {result['analyzed_at_jst']}  現在値 {close_now:.3f}  確定足 {conf.get('last_end_jst', '')} まで（直近{n}本）"
    cm = result.get("commentary") or {}
    legend1 = ("赤＝サポート　緑＝レジスタンス　" + ("紫＝チャネル（破線＝中央）　" if ch else "")
               + f"橙＝EMA{result.get('ema_fast_period', '')}　青＝EMA{result.get('ema_slow_period', '')}"
               + (f"　黒太線＝EMA{result['ema_long_period']}" if result.get("ema_long_period") else ""))
    parts2 = []
    if st["draw_fib"] and fib and any(visible(p) for p in fib["levels"].values()):
        parts2.append("金破線＝フィボナッチ")
    if st["draw_key_level"] and stc.get("key_level") is not None and visible(stc["key_level"]):
        parts2.append("点線＝" + ("押し安値" if stc.get("direction") == "up" else "戻り高値"))
    if st["draw_prev_day"] and dl.get("prev_day") and (visible(dl["prev_day"]["high"]) or visible(dl["prev_day"]["low"])):
        parts2.append("灰破線＝前日高安")
    if st["draw_zones"] and (zones.get("above") or zones.get("below")):
        parts2.append("薄い帯＝注目価格帯")
    if st["draw_scenario_arrows"] and sc and (sc.get("up") or sc.get("down")):
        parts2.append("右端の矢印＝シナリオ（実線＝メイン・点線＝サブ）　赤点線＝崩れる条件")
    if ax_rsi is not None:
        parts2.append("下段＝RSI(14)" + ("　青緑の斜線＝ダイバージェンス" if divs and st["draw_divergence"] else ""))
    legend = legend1 + ("\n" + "　".join(parts2) if parts2 else "")
    disclaimer = "テクニカル分析の参考情報であり、投資助言ではありません。価格は参考値（15分以上の遅延あり）。"
    if band:
        _draw_title_band(fig, st, cm["title_line"], f"相場環境：{label}　現在 {close_now:.3f}", sub, legend)
    else:
        fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=15, fontweight="bold")
        fig.text(0.02, 0.945, sub, ha="left", fontsize=10.5, color="#333333")
        fig.text(0.98, 0.935, legend, ha="right", va="center", fontsize=8.5, color="#666666")
    if foot:
        _draw_footer(fig, st, font, cm["hook"], disclaimer)
    else:
        fig.text(0.98, 0.012, disclaimer, ha="right", fontsize=8.5, color="#888888")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_path


def render_daily(df_daily: pd.DataFrame, result: dict, out_path: str | Path, *, months: int = 6, tz: str,
                 width_px: int = 1600, height_px: int = 900, dpi: int = 100, ema_period: int = 50,
                 style_cfg: dict | None = None) -> Path | None:
    """2 枚目：日足（過去 months か月）。位置関係を見せるだけなので線は 3 種類まで：日足 EMA（既定 50）・前週高安・4時間足の押し安値／戻り高値。
    df_daily: UTC index の日足。result: pipeline.analyze() の戻り値（daily・structure・commentary を使う）。"""
    if df_daily is None or len(df_daily) < 10:
        return None
    st = {**DEFAULT_STYLE, **(style_cfg or {})}
    font = pick_font()
    from . import indicators
    d = df_daily.copy()
    last_bar = result.get("last_bar_utc")
    if last_bar:
        try:
            d = d[d.index <= pd.Timestamp(last_bar)]      # 解析に使った最後の 4時間足より後に始まる日足は描かない
        except Exception:
            pass
    if len(d) < 10:
        return None
    ema = indicators.ema(d["close"].to_numpy(dtype=float), int(ema_period))
    n = min(len(d), max(40, int(months) * 22))
    plot_df = d.tail(n).copy()
    plot_df.index = plot_df.index.tz_convert(tz)
    plot_df = plot_df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    style = mpf.make_mpf_style(base_mpf_style="yahoo", rc={"font.family": font, "font.size": 11, "axes.unicode_minus": False},
                               gridstyle=":", gridcolor="#dddddd", facecolor="white", figcolor="white")
    adds = [mpf.make_addplot(pd.Series(ema[-n:], index=plot_df.index), color=st["ema_slow_color"], width=1.8)]

    dl = result.get("daily") or {}
    stc = result.get("structure") or {}
    pw = dl.get("prev_week") or {}
    key = stc.get("key_level") if stc.get("direction") in ("up", "down") else None
    key_name = "押し安値" if stc.get("direction") == "up" else "戻り高値"

    atr_d = float(dl.get("daily_atr") or 0.0) or float((plot_df["High"] - plot_df["Low"]).tail(14).mean())
    pad = max(atr_d * 1.0, 0.1)
    y_lo = float(plot_df["Low"].min()) - pad
    y_hi = float(plot_df["High"].max()) + pad

    def visible(p: float | None) -> bool:
        return p is not None and y_lo <= float(p) <= y_hi

    hl_prices, hl_colors, hl_styles = [], [], []
    for v in (pw.get("high"), pw.get("low")):
        if visible(v):
            hl_prices.append(float(v)); hl_colors.append(st["prev_day_color"]); hl_styles.append("--")
    hlines = dict(hlines=hl_prices, colors=hl_colors, linestyle=hl_styles, linewidths=1.4, alpha=0.95) if hl_prices else None
    kwargs = dict(type="candle", style=style, figsize=(width_px / dpi, height_px / dpi), returnfig=True,
                  datetime_format="%m/%d", xrotation=0, ylabel="", tight_layout=False, addplot=adds,
                  scale_padding={"left": 1.0, "right": 2.6, "top": 1.1, "bottom": 0.6})
    if hlines:
        kwargs["hlines"] = hlines
    fig, axes = mpf.plot(plot_df, **kwargs)
    ax = axes[0]
    cm = result.get("commentary") or {}
    band = bool(st["title_band"])
    foot = bool(st["footer_hook"])
    x0, w = 0.055, 0.735
    top = 0.885 if band else 0.90
    bottom = 0.115 if foot else 0.075
    for a in axes[:2]:
        a.set_position([x0, bottom, w, top - bottom])
    ax.set_ylim(y_lo, y_hi)
    ax.yaxis.tick_left()
    ax.yaxis.set_label_position("left")
    x_right = n + 0.8

    if visible(key):
        ax.axhline(float(key), color=st["key_level_color"], linestyle=":", linewidth=1.8, alpha=0.95, zorder=2)
    close_now = float(result["close"])
    ax.axhline(close_now, color=COLOR_NOW, linestyle=":", linewidth=1.0)

    labels = [(close_now, f"現在 {close_now:.3f}", COLOR_NOW, "outline")]
    if visible(pw.get("high")):
        labels.append((float(pw["high"]), f"前週高値 {float(pw['high']):.3f}", st["prev_day_color"], "outline"))
    if visible(pw.get("low")):
        labels.append((float(pw["low"]), f"前週安値 {float(pw['low']):.3f}", st["prev_day_color"], "outline"))
    if visible(key):
        labels.append((float(key), f"{key_name} {float(key):.3f}", st["key_level_color"], "outline"))
    ema_now = float(ema[-1])
    if visible(ema_now):
        labels.append((ema_now, f"日足EMA{ema_period} {ema_now:.3f}", st["ema_slow_color"], "fill"))
    labels.sort(key=lambda t: t[0])
    ys = _stack(labels, y_lo, y_hi)
    fs = float(st["level_label_size"])
    for (price, text, color, kind), y in zip(labels, ys):
        if kind == "fill":
            ax.text(x_right, y, text, color="white", fontsize=fs, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc=color, ec=color, lw=1.0))
        else:
            ax.text(x_right, y, text, color=color, fontsize=fs - 1, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.9))

    # 文言：タイトル帯（投稿と同じ日付・「日足の位置づけ」）、最下段は日足の大局 1 行
    above = close_now > ema_now
    date = (cm.get("title_line") or "").split("】")[-1].split(" ")[0] if cm.get("title_line") else result.get("analyzed_at_jst", "")[:10]
    title = f"【今日のドル円】{date} 日足の位置づけ｜EMA{ema_period} の{'上' if above else '下'}側"
    tr = result["trend"]
    label = tr.get("label_effective", tr["label"])
    conf = result.get("confirmed") or {}
    sub = f"分析日時 {result['analyzed_at_jst']}  日足 直近{n}本（約{months}か月）  4時間足の確定足 {conf.get('last_end_jst', '')} まで"
    legend = f"青＝日足EMA{ema_period}　灰破線＝前週高安　点線＝4時間足の{key_name}（ダウ理論の分かれ目）"
    bits = [f"日足では EMA{ema_period}（{ema_now:.3f}）の{'上' if above else '下'}側で推移"]
    if pw.get("high") is not None and pw.get("low") is not None:
        bits.append(f"前週レンジ {float(pw['low']):.3f}〜{float(pw['high']):.3f}")
    if key is not None:
        bits.append(f"4時間足の{key_name} {float(key):.3f} が日足でも目印")
    hook = "。".join(bits) + "。"
    disclaimer = "テクニカル分析の参考情報であり、投資助言ではありません。価格は参考値（15分以上の遅延あり）。"
    if band:
        _draw_title_band(fig, st, title, f"4時間足の相場環境：{label}　現在 {close_now:.3f}", sub, legend)
    else:
        fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=15, fontweight="bold")
        fig.text(0.02, 0.945, sub, ha="left", fontsize=10.5, color="#333333")
        fig.text(0.98, 0.935, legend, ha="right", va="center", fontsize=8.5, color="#666666")
    if foot:
        _draw_footer(fig, st, font, hook, disclaimer)
    else:
        fig.text(0.98, 0.012, disclaimer, ha="right", fontsize=8.5, color="#888888")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_path
