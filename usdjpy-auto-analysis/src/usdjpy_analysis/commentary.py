"""日本語の解説文（ルールベース）。

docs/ANALYSIS_RULES.md「解説文」に従う:
  現在のトレンド／サポート／レジスタンス／注目ポイント／上方向シナリオ／下方向シナリオ
  断定表現（必ず・絶対）は使わない。「〜に注目」「〜が焦点」「〜の可能性」で書く。

AI（Claude API）で文章を磨く段階は後回し。まずは数値から機械的に組み立てる。
"""
from __future__ import annotations


def _fmt(p: float) -> str:
    return f"{p:.3f}"


def _nearest(levels: list[dict]) -> dict | None:
    return levels[0] if levels else None


def build(result: dict) -> dict:
    sym = result["symbol"]
    tf = result["timeframe_label"]
    close = result["close"]
    trend = result["trend"]
    sup = result["supports"]
    res = result["resistances"]
    s1 = _nearest(sup)
    r1 = _nearest(res)
    tl_up = result.get("trendline_up")
    tl_dn = result.get("trendline_down")
    htf = result.get("higher_timeframe")

    lines: list[str] = []
    lines.append(f"{sym} {tf}。現在値は {_fmt(close)} 円付近。")

    # 相場環境
    d = trend["details"]
    env = {
        "強い上昇": "上昇基調がはっきりしています",
        "弱い上昇": "上昇基調ですが、上値はやや重い状態です",
        "レンジ": "方向感の乏しいレンジ相場です",
        "弱い下落": "下落基調ですが、下値はやや堅い状態です",
        "強い下落": "下落基調がはっきりしています",
    }[trend["label"]]
    lines.append(f"相場環境は「{trend['label']}」。{env}。"
                 f"終値は EMA{result['ema_slow_period']}（{_fmt(d['ema_slow'])}）の{d['close_vs_ema_slow']}、"
                 f"EMA{result['ema_slow_period']} は{d['ema_slow_slope']}。{d['structure']}。")

    if htf:
        lines.append(f"日足では、前日終値（{_fmt(htf['close'])}）が日足EMA{htf['ema_period']}（{_fmt(htf['ema'])}）の"
                     f"{'上' if htf['above'] else '下'}にあり、大局は{'上方向' if htf['above'] else '下方向'}優位です。")

    # サポート・レジスタンス
    if sup:
        lines.append("直近サポートは " + "、".join(f"{_fmt(l['price'])}円（反応{l['touches']}回）" for l in sup) + "。")
    else:
        lines.append("表示範囲に明確なサポート候補はありません。")
    if res:
        lines.append("レジスタンスは " + "、".join(f"{_fmt(l['price'])}円（反応{l['touches']}回）" for l in res) + "。")
    else:
        lines.append("表示範囲に明確なレジスタンス候補はありません。")

    # トレンドライン
    if tl_up:
        st = "割り込んでおり、短期の流れが変化した可能性があります" if tl_up["broken"] else "維持しています"
        lines.append(f"上昇トレンドライン（{_fmt(tl_up['value_now'])}円付近・接触{tl_up['touches']}回）を{st}。")
    if tl_dn:
        st = "上抜けており、短期の流れが変化した可能性があります" if tl_dn["broken"] else "が上値を抑えています"
        lines.append(f"下降トレンドライン（{_fmt(tl_dn['value_now'])}円付近・接触{tl_dn['touches']}回）{st}。")

    # シナリオ
    up_target = r1["price"] if r1 else None
    dn_target = s1["price"] if s1 else None
    if up_target:
        nxt = res[1]["price"] if len(res) > 1 else None
        lines.append(f"上方向：{_fmt(up_target)}円を終値で上抜けると" + (f"、次は {_fmt(nxt)}円が視野に入ります。" if nxt else "、上値余地が広がります。"))
    if dn_target:
        nxt = sup[1]["price"] if len(sup) > 1 else None
        lines.append(f"下方向：{_fmt(dn_target)}円を終値で割り込むと" + (f"、次は {_fmt(nxt)}円が意識されます。" if nxt else "、下値を探る展開に注意です。"))

    focus = []
    if r1:
        focus.append(f"{_fmt(r1['price'])}円")
    if s1:
        focus.append(f"{_fmt(s1['price'])}円")
    if focus:
        lines.append("次に注目する価格帯は " + " と ".join(focus) + " です。")

    long_text = "\n".join(lines)

    # X 投稿用の短文（全角 ≒ 140 文字以内が目安）
    arrow = {"強い上昇": "↑↑", "弱い上昇": "↑", "レンジ": "→", "弱い下落": "↓", "強い下落": "↓↓"}[trend["label"]]
    post = [f"📊 {sym} {tf} {arrow} {trend['label']}", f"現在 {_fmt(close)}"]
    if r1:
        post.append(f"R {_fmt(r1['price'])}" + (f" / {_fmt(res[1]['price'])}" if len(res) > 1 else ""))
    if s1:
        post.append(f"S {_fmt(s1['price'])}" + (f" / {_fmt(sup[1]['price'])}" if len(sup) > 1 else ""))
    if tl_up:
        post.append("上昇TL " + ("割れ" if tl_up["broken"] else "維持"))
    if tl_dn:
        post.append("下降TL " + ("上抜け" if tl_dn["broken"] else "継続"))
    if r1 and s1:
        post.append(f"{_fmt(r1['price'])}超えで上値試し、{_fmt(s1['price'])}割れで調整に注意")
    post.append("#USDJPY #ドル円 #テクニカル分析")
    post_text = "\n".join(post)

    return {"long": long_text, "post": post_text}
