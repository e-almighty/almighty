"""投稿用チャート画像（PNG）。

描くもの（docs/ANALYSIS_RULES.md「投稿画像」）:
  銘柄・時間足・現在値・分析日時／ローソク足／サポート（赤・太線）／レジスタンス（緑・太線）
  平行チャネル（紫＝上限・下限、薄紫の破線＝中央）／EMA20（橙）・50（青）・200（黒太線）／右端に名前入りの価格ラベル
  第2ステージ：フィボ 38.2／50／61.8（金の細い破線）／押し安値・戻り高値（点線）／前日高安（灰の破線）
              注目価格帯（薄い帯）／RSI のサブパネル（30・70 と、ダイバージェンスの線）
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
}
COLOR_NOW = "#444444"


def pick_font() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for c in FONT_CANDIDATES:
        if c in names:
            return c
    return "DejaVu Sans"


def _stack(labels: list[tuple], y_lo: float, y_hi: float, frac: float = 0.034) -> list[float]:
    """近すぎるラベルを上下にずらす。labels は (price, ...) の並び（価格順にソート済み）。"""
    min_gap = (y_hi - y_lo) * frac
    ys = [t[0] for t in labels]
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
    if ax_rsi is not None:
        for a in axes[:2]:
            a.set_position([x0, 0.245, w, 0.655])
        for a in axes[2:4]:
            a.set_position([x0, 0.075, w, 0.150])
    else:
        for a in axes[:2]:
            a.set_position([x0, 0.075, w, 0.825])
    ax.set_ylim(y_lo, y_hi)
    ax.yaxis.tick_left()
    ax.yaxis.set_label_position("left")
    x_right = n + 0.8

    # 注目価格帯（薄い帯）
    zones = result.get("zones") or {}
    if st["draw_zones"]:
        for side, color in (("above", st["zone_above_color"]), ("below", st["zone_below_color"])):
            for z in zones.get(side, [])[:2]:
                half = max((z["high"] - z["low"]) / 2.0, atr_v * 0.08)
                lo, hi = z["center"] - half, z["center"] + half
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
            ax.annotate(d["label"].replace("ダイバージェンス", "ダイバ"), xy=(x2, d["p2"]), xytext=(6, 8 if "bear" in d["kind"] else -14),
                        textcoords="offset points", fontsize=9, color=st["divergence_color"], fontweight="bold")
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

    # 現在値（点線）
    close_now = result["close"]
    ax.axhline(close_now, color=COLOR_NOW, linestyle=":", linewidth=1.0)

    # 右端の価格ラベル（色付きの箱で「サポート／レジスタンス」と明記。近すぎるラベルは上下にずらす）
    fs = float(st["level_label_size"])
    labels = [(lv["price"], f"サポート {lv['price']:.3f}", COLOR_SUPPORT, "fill") for lv in vis_sup]
    labels += [(lv["price"], f"レジスタンス {lv['price']:.3f}", COLOR_RESIST, "fill") for lv in vis_res]
    labels.append((close_now, f"現在 {close_now:.3f}", COLOR_NOW, "outline"))
    labels += [(p, t, c, "outline") for (p, t, c) in ch_labels if visible(p)]
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

    # タイトル
    tr = result["trend"]
    label = tr.get("label_effective", tr["label"])
    slot = result.get("slot")
    slot_txt = "（朝のプラン）" if slot == "morning" else ("（中間報告）" if slot == "evening" else "")
    title = f"{result['symbol']} {result['timeframe_label']}{slot_txt}   相場環境：{label}"
    conf = result.get("confirmed") or {}
    sub = f"分析日時 {result['analyzed_at_jst']}  現在値 {close_now:.3f}  確定足 {conf.get('last_end_jst', '')} まで（直近{n}本）"
    fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, 0.945, sub, ha="left", fontsize=10.5, color="#333333")
    legend = (f"赤＝サポート　緑＝レジスタンス　紫＝チャネル（破線＝中央）　"
              f"橙＝EMA{result.get('ema_fast_period', '')}　青＝EMA{result.get('ema_slow_period', '')}"
              + (f"　黒太線＝EMA{result['ema_long_period']}" if result.get("ema_long_period") else "")
              + "\n金破線＝フィボナッチ　点線＝押し安値／戻り高値　灰破線＝前日高安　薄い帯＝注目価格帯　青緑の斜線＝RSIダイバージェンス")
    fig.text(0.98, 0.935, legend, ha="right", va="center", fontsize=8.5, color="#666666")
    fig.text(0.98, 0.012, "テクニカル分析の参考情報であり、投資助言ではありません。価格は参考値（15分以上の遅延あり）。", ha="right", fontsize=8.5, color="#888888")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_path
