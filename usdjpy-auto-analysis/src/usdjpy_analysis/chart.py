"""投稿用チャート画像（PNG）。

描くもの（docs/ANALYSIS_RULES.md「投稿画像」）:
  銘柄・時間足・現在値・分析日時／ローソク足／サポート（赤・太線）／レジスタンス（緑・太線）
  平行チャネル（紫＝上限・下限、薄紫の破線＝中央）／EMA20（橙）・50（青）・200（黒太線）／右端に名前入りの価格ラベル
ラインは多すぎないこと。サポレジ各 1〜3 本、チャネルは 1 組。
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

# 見た目の既定値。config/analysis.yaml の chart: で上書きできる
DEFAULT_STYLE = {
    "support_color": "#d62828",     # サポート＝赤（SHO の指定・2026-10-04）
    "resistance_color": "#1b9e4b",  # レジスタンス＝緑（SHO の指定・2026-10-04）
    "level_linewidth": 2.8,         # サポレジの線の太さ（「バーンと」分かるように）
    "level_label_size": 11,         # 右端のラベルの文字サイズ
    "channel_color": "#6a1b9a",         # チャネル上限・下限（紫）
    "channel_center_color": "#b39ddb",  # チャネル中央（薄い紫・破線）
    "channel_linewidth": 1.8,
    "ema_fast_color": "#f39c12",        # EMA20 = 橙
    "ema_slow_color": "#2980b9",        # EMA50 = 青
    "ema_long_color": "#111111",        # EMA200 = 黒・太め（SHO の指定・2026-10-04）
    "ema_long_width": 2.4,
}
COLOR_NOW = "#444444"


def pick_font() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for c in FONT_CANDIDATES:
        if c in names:
            return c
    return "DejaVu Sans"


def render(df: pd.DataFrame, result: dict, out_path: str | Path, *, bars_to_plot: int,
           tz: str, width_px: int = 1600, height_px: int = 900, dpi: int = 100,
           ema_fast=None, ema_slow=None, ema_long=None, style_cfg: dict | None = None) -> Path:
    """df: UTC index の OHLC。result: pipeline.analyze() の戻り値。style_cfg: analysis.yaml の chart:"""
    st = {**DEFAULT_STYLE, **(style_cfg or {})}
    COLOR_SUPPORT, COLOR_RESIST = st["support_color"], st["resistance_color"]
    COLOR_CH, COLOR_CHC = st["channel_color"], st["channel_center_color"]
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
        adds.append(mpf.make_addplot(pd.Series(ema_fast[-n:], index=plot_df.index), color=st["ema_fast_color"], width=1.0))
    if ema_slow is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_slow[-n:], index=plot_df.index), color=st["ema_slow_color"], width=1.2))
    if ema_long is not None:
        adds.append(mpf.make_addplot(pd.Series(ema_long[-n:], index=plot_df.index), color=st["ema_long_color"], width=float(st["ema_long_width"])))

    # 縦軸の範囲：描く足の高安 ± ATR。その外にあるサポレジは描かない（解説文には残る）
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
    vis_sup = [lv for lv in result["supports"] if y_lo <= lv["price"] <= y_hi]
    vis_res = [lv for lv in result["resistances"] if y_lo <= lv["price"] <= y_hi]

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
    fig, axes = mpf.plot(plot_df, **kwargs)
    ax = axes[0]
    ax.set_ylim(y_lo, y_hi)
    ax.yaxis.tick_left()          # 価格の目盛りは左へ。右端はサポレジのラベル専用にする
    ax.yaxis.set_label_position("left")

    # 平行チャネル（上限・下限＝実線、中央＝破線）。x は足の番号（0 〜 n-1）
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

    # 現在値（点線）
    close_now = result["close"]
    ax.axhline(close_now, color=COLOR_NOW, linestyle=":", linewidth=1.0)

    # 右端の価格ラベル（色付きの箱で「サポート／レジスタンス」と明記。近すぎるラベルは上下にずらす）
    x_label = n + 0.8
    fs = float(st["level_label_size"])
    labels = [(lv["price"], f"サポート {lv['price']:.3f}", COLOR_SUPPORT, "fill") for lv in vis_sup]
    labels += [(lv["price"], f"レジスタンス {lv['price']:.3f}", COLOR_RESIST, "fill") for lv in vis_res]
    labels.append((close_now, f"現在 {close_now:.3f}", COLOR_NOW, "outline"))
    labels += [(p, t, c, "outline") for (p, t, c) in ch_labels if y_lo <= p <= y_hi]
    labels.sort(key=lambda t: t[0])
    min_gap = (y_hi - y_lo) * 0.034
    ys = [t[0] for t in labels]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < min_gap:
            ys[i] = ys[i - 1] + min_gap
    for (price, text, color, kind), y in zip(labels, ys):
        if kind == "fill":
            ax.text(x_label, y, text, color="white", fontsize=fs, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc=color, ec=color, lw=1.0))
        else:
            ax.text(x_label, y, text, color=color, fontsize=fs - 1, va="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=0.9))

    # タイトル
    title = f"{result['symbol']} {result['timeframe_label']}   相場環境：{result['trend']['label']}"
    sub = f"分析日時 {result['analyzed_at_jst']}  現在値 {close_now:.3f}  （直近{n}本）"
    fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.02, 0.945, sub, ha="left", fontsize=10.5, color="#333333")
    legend = (f"赤＝サポート　緑＝レジスタンス　紫＝チャネル（破線＝中央）　"
              f"橙＝EMA{result.get('ema_fast_period', '')}　青＝EMA{result.get('ema_slow_period', '')}"
              + (f"　黒太線＝EMA{result['ema_long_period']}" if result.get("ema_long_period") else ""))
    fig.text(0.98, 0.945, legend, ha="right", fontsize=9, color="#666666")
    fig.text(0.98, 0.012, "テクニカル分析の参考情報であり、投資助言ではありません。", ha="right", fontsize=8.5, color="#888888")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return out_path
