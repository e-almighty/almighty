"""投稿用チャート画像（PNG）。

描くもの（docs/ANALYSIS_RULES.md「投稿画像」）:
  銘柄・時間足・現在値・分析日時／ローソク足／サポート（緑）／レジスタンス（赤）
  トレンドライン（青）／EMA fast・slow（細線）／右端に価格ラベル
ラインは多すぎないこと。サポレジ各 1〜3 本、トレンドラインは最大 1 本ずつ。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mplfinance as mpf  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

# 日本語が出るフォントを上から順に探す（Windows → Mac → Linux）
FONT_CANDIDATES = ["Meiryo", "Yu Gothic", "Yu Gothic UI", "MS Gothic", "Hiragino Sans",
                   "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic", "IPAGothic",
                   "WenQuanYi Zen Hei", "Unifont-JP", "DejaVu Sans"]

COLOR_SUPPORT = "#1b9e4b"
COLOR_RESIST = "#d62828"
COLOR_TREND_UP = "#1f6fd6"
COLOR_TREND_DN = "#8e44ad"
COLOR_NOW = "#444444"


def pick_font() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for c in FONT_CANDIDATES:
        if c in names:
            return c
    return "DejaVu Sans"


def render(df: pd.DataFrame, result: dict, out_path: str | Path, *, bars_to_plot: int,
           tz: str, width_px: int = 1600, height_px: int = 900, dpi: int = 100,
           ema_fast=None, ema_slow=None) -> Path:
    """df: UTC index の OHLC。result: pipeline.analyze() の戻り値。"""
    font = pick_font()
    plot_df = df.tail(bars_to_plot).copy()
    plot_df.index = plot_df.index.tz_convert(tz)
    plot_df = plot_df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    offset = len(df) - len(plot_df)           # 解析の足番号 → 描画の足番号
    n = len(plot_df)

    style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        rc={"font.family": font, "font.size": 11, "axes.unicode_minus": False},
        gridstyle=":", gridcolor="#dddddd", facecolor="white", figcolor="white",
    )

    adds = []
    if ema_fast is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_fast[-n:], index=plot_df.index), color="#f39c12", width=1.0))
    if ema_slow is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_slow[-n:], index=plot_df.index), color="#2980b9", width=1.2))

    # 縦軸の範囲：描く足の高安 ± ATR。その外にあるサポレジは描かない（解説文には残る）
    atr_v = float(result.get("atr") or 0.0)
    pad = max(atr_v * 1.0, 0.05)
    y_lo = float(plot_df["Low"].min()) - pad
    y_hi = float(plot_df["High"].max()) + pad
    for lv in result["supports"] + result["resistances"]:
        if y_lo - 2 * atr_v <= lv["price"] <= y_hi + 2 * atr_v:
            y_lo = min(y_lo, lv["price"] - pad * 0.5)
            y_hi = max(y_hi, lv["price"] + pad * 0.5)
    vis_sup = [lv for lv in result["supports"] if y_lo <= lv["price"] <= y_hi]
    vis_res = [lv for lv in result["resistances"] if y_lo <= lv["price"] <= y_hi]

    hl_prices, hl_colors = [], []
    for lv in vis_sup:
        hl_prices.append(lv["price"]); hl_colors.append(COLOR_SUPPORT)
    for lv in vis_res:
        hl_prices.append(lv["price"]); hl_colors.append(COLOR_RESIST)
    hlines = dict(hlines=hl_prices, colors=hl_colors, linestyle="-", linewidths=1.4, alpha=0.9) if hl_prices else None

    alines, acolors = [], []
    for key, color in (("trendline_up", COLOR_TREND_UP), ("trendline_down", COLOR_TREND_DN)):
        tl = result.get(key)
        if not tl:
            continue
        i1 = tl["i1"] - offset
        if i1 < 0:
            # 起点が描画範囲より前なら、描画範囲の先頭から描く
            i1 = 0
        p1 = tl["p1"] + tl["slope"] * (i1 + offset - tl["i1"])
        i2 = n - 1
        p2 = tl["p1"] + tl["slope"] * (i2 + offset - tl["i1"])
        alines.append([(plot_df.index[i1], p1), (plot_df.index[i2], p2)])
        acolors.append(color)
    alines_arg = dict(alines=alines, colors=acolors, linewidths=1.6, alpha=0.95) if alines else None

    kwargs = dict(type="candle", style=style, figsize=(width_px / dpi, height_px / dpi),
                  returnfig=True, datetime_format="%m/%d %H:%M", xrotation=0, ylabel="",
                  tight_layout=False, scale_padding={"left": 0.3, "right": 1.6, "top": 0.5, "bottom": 0.6})
    if adds:
        kwargs["addplot"] = adds
    if hlines:
        kwargs["hlines"] = hlines
    if alines_arg:
        kwargs["alines"] = alines_arg
    fig, axes = mpf.plot(plot_df, **kwargs)
    ax = axes[0]
    ax.set_ylim(y_lo, y_hi)

    # 現在値（点線）
    close_now = result["close"]
    ax.axhline(close_now, color=COLOR_NOW, linestyle=":", linewidth=1.0)

    # 右端の価格ラベル
    x_label = n + 0.8
    for lv in vis_sup:
        ax.text(x_label, lv["price"], f"S {lv['price']:.3f}", color=COLOR_SUPPORT, fontsize=10, va="center", fontweight="bold")
    for lv in vis_res:
        ax.text(x_label, lv["price"], f"R {lv['price']:.3f}", color=COLOR_RESIST, fontsize=10, va="center", fontweight="bold")
    ax.text(x_label, close_now, f"現在 {close_now:.3f}", color=COLOR_NOW, fontsize=10, va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=COLOR_NOW, lw=0.8))
    for key, color, name in (("trendline_up", COLOR_TREND_UP, "上昇TL"), ("trendline_down", COLOR_TREND_DN, "下降TL")):
        tl = result.get(key)
        if tl:
            ax.text(n - 1, tl["value_now"], f" {name}", color=color, fontsize=9, va="bottom")

    # タイトル
    title = f"{result['symbol']} {result['timeframe_label']}   相場環境：{result['trend']['label']}"
    sub = f"分析日時 {result['analyzed_at_jst']}  現在値 {close_now:.3f}  （直近{n}本）"
    fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, 0.945, sub, ha="left", fontsize=10.5, color="#333333")
    fig.text(0.98, 0.945, "緑＝サポート　赤＝レジスタンス　青／紫＝トレンドライン　橙／青細線＝EMA", ha="right", fontsize=9, color="#666666")
    fig.text(0.98, 0.012, "テクニカル分析の参考情報であり、投資助言ではありません。", ha="right", fontsize=8.5, color="#888888")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_path
