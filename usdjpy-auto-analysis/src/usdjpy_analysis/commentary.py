"""日本語の解説文（ルールベース）。

docs/ANALYSIS_RULES.md「解説文」に従う:
  現在値 → 相場環境（EMA 3 本の並び）→ 日足の大局 → サポート → レジスタンス → チャネル
  → 上方向シナリオ → 下方向シナリオ → 注目価格帯 → 根拠（線 1 本ごとに「なぜそこか」）
  断定表現（必ず・絶対）は使わない。「〜に注目」「〜が焦点」「〜の可能性」で書く。

AI（Claude API）で文章を磨く段階は後回し。まずは数値から機械的に組み立てる。
"""
from __future__ import annotations


def _fmt(p: float) -> str:
    return f"{p:.3f}"


def _nearest(levels: list[dict]) -> dict | None:
    return levels[0] if levels else None


def _ema_paragraph(result: dict) -> str:
    d = result["trend"]["details"]
    close = result["close"]
    f, s = d["ema_fast"], d["ema_slow"]
    pf, ps = result["ema_fast_period"], result["ema_slow_period"]
    l = d.get("ema_long")
    pl = result.get("ema_long_period")
    if l is None or not pl:
        return (f"終値は EMA{ps}（{_fmt(s)}）の{d['close_vs_ema_slow']}、EMA{ps} は{d['ema_slow_slope']}。")
    above_all = close > f and close > s and close > l
    below_all = close < f and close < s and close < l
    if f > s > l and above_all:
        order = f"EMA{pf}＞EMA{ps}＞EMA{pl} の順に並び、現在値はその上にあります（上昇のパーフェクトオーダー）"
    elif f < s < l and below_all:
        order = f"EMA{pf}＜EMA{ps}＜EMA{pl} の順に並び、現在値はその下にあります（下落のパーフェクトオーダー）"
    else:
        pos = []
        for name, v in ((f"EMA{pf}", f), (f"EMA{ps}", s), (f"EMA{pl}", l)):
            pos.append(f"{name}（{_fmt(v)}）の{'上' if close > v else '下'}")
        order = "現在値は " + "、".join(pos) + " にあり、3 本の並びはそろっていません"
    return (f"移動平均は {order}。EMA{ps} は{d['ema_slow_slope']}。"
            f"EMA{pl}（{_fmt(l)}）は長期の目安で、現在値はその{d.get('close_vs_ema_long', '')}です。")


def _channel_paragraph(ch: dict | None) -> str:
    if not ch:
        return "はっきりした平行チャネルは引けていません（レンジ、または基準になる高安がそろっていない状態）。"
    name = "上昇チャネル" if ch["kind"] == "up" else "下降チャネル"
    text = (f"{name}（下限 {_fmt(ch['lower_now'])}／中央 {_fmt(ch['center_now'])}／上限 {_fmt(ch['upper_now'])}）"
            f"の中にあり、現在は{ch['position_text']}の位置です。")
    if ch["broken"]:
        side = "下限" if ch["kind"] == "up" else "上限"
        text += f"ただし基準線（{side}）を終値で越えており、チャネルが崩れた可能性があります。"
    return text


def build(result: dict) -> dict:
    sym = result["symbol"]
    tf = result["timeframe_label"]
    close = result["close"]
    trend = result["trend"]
    sup = result["supports"]
    res = result["resistances"]
    s1 = _nearest(sup)
    r1 = _nearest(res)
    ch = result.get("channel")
    htf = result.get("higher_timeframe")

    lines: list[str] = []
    lines.append(f"{sym} {tf}。現在値は {_fmt(close)} 円付近。")

    env = {
        "強い上昇": "上昇基調がはっきりしています",
        "弱い上昇": "上昇基調ですが、上値はやや重い状態です",
        "レンジ": "方向感の乏しいレンジ相場です",
        "弱い下落": "下落基調ですが、下値はやや堅い状態です",
        "強い下落": "下落基調がはっきりしています",
    }[trend["label"]]
    lines.append(f"相場環境は「{trend['label']}」。{env}。{trend['details']['structure']}。")
    lines.append(_ema_paragraph(result))

    if htf:
        lines.append(f"日足では、前日終値（{_fmt(htf['close'])}）が日足EMA{htf['ema_period']}（{_fmt(htf['ema'])}）の"
                     f"{'上' if htf['above'] else '下'}にあり、大局は{'上方向' if htf['above'] else '下方向'}優位です。")

    if sup:
        lines.append("サポートは " + "、".join(f"{_fmt(l['price'])}円" for l in sup) + "。")
    else:
        lines.append("表示範囲に明確なサポート候補はありません。")
    if res:
        lines.append("レジスタンスは " + "、".join(f"{_fmt(l['price'])}円" for l in res) + "。")
    else:
        lines.append("表示範囲に明確なレジスタンス候補はありません。")

    lines.append(_channel_paragraph(ch))

    # シナリオ（サポレジとチャネルのうち、現在値に近い方を目先の目安にする）
    up_candidates = [("レジスタンス", r1["price"]) for _ in [0] if r1]
    dn_candidates = [("サポート", s1["price"]) for _ in [0] if s1]
    if ch:
        if ch["upper_now"] > close:
            up_candidates.append(("チャネル上限", ch["upper_now"]))
        if ch["lower_now"] < close:
            dn_candidates.append(("チャネル下限", ch["lower_now"]))
    if up_candidates:
        nm, p = min(up_candidates, key=lambda t: t[1])
        nxt = res[1]["price"] if (len(res) > 1 and nm == "レジスタンス") else (r1["price"] if (r1 and nm != "レジスタンス" and r1["price"] > p) else None)
        lines.append(f"上方向：目先は{nm} {_fmt(p)}円。終値で上抜けると" + (f"、次は {_fmt(nxt)}円が視野に入ります。" if nxt else "、上値余地が広がります。"))
    if dn_candidates:
        nm, p = max(dn_candidates, key=lambda t: t[1])
        nxt = sup[1]["price"] if (len(sup) > 1 and nm == "サポート") else (s1["price"] if (s1 and nm != "サポート" and s1["price"] < p) else None)
        lines.append(f"下方向：目先は{nm} {_fmt(p)}円。終値で割り込むと" + (f"、次は {_fmt(nxt)}円が意識されます。" if nxt else "、下値を探る展開に注意です。"))

    focus = []
    if r1:
        focus.append(f"{_fmt(r1['price'])}円")
    if s1:
        focus.append(f"{_fmt(s1['price'])}円")
    if focus:
        lines.append("次に注目する価格帯は " + " と ".join(focus) + " です。")

    long_text = "\n".join(lines)

    # 根拠（線 1 本ごと）
    ev: list[str] = []
    for l in res:
        ev.append(f"レジスタンス {_fmt(l['price'])}：解析範囲でヒゲが {l['touches']} 回反応（最後は {l.get('last_touch_jst') or '不明'}）、"
                  f"スイング高安 {l['pivots']} 個が集まる価格帯" + ("、心理的節目に近い" if l.get("is_round") else ""))
    for l in sup:
        ev.append(f"サポート {_fmt(l['price'])}：解析範囲でヒゲが {l['touches']} 回反応（最後は {l.get('last_touch_jst') or '不明'}）、"
                  f"スイング高安 {l['pivots']} 個が集まる価格帯" + ("、心理的節目に近い" if l.get("is_round") else ""))
    if ch:
        if ch["kind"] == "up":
            ev.append(f"上昇チャネル：下限線は {ch['t1_jst']} と {ch['t2_jst']} の安値を結んだ線（接触 {ch['touches_base']} 回）。"
                      f"上限線はそれと平行で、{ch['far_jst']} の高値 {_fmt(ch['far_price'])} を通る（接触 {ch['touches_far']} 回）。"
                      f"中央線は上限と下限の中間")
        else:
            ev.append(f"下降チャネル：上限線は {ch['t1_jst']} と {ch['t2_jst']} の高値を結んだ線（接触 {ch['touches_base']} 回）。"
                      f"下限線はそれと平行で、{ch['far_jst']} の安値 {_fmt(ch['far_price'])} を通る（接触 {ch['touches_far']} 回）。"
                      f"中央線は上限と下限の中間")
    d = trend["details"]
    ev.append(f"相場環境「{trend['label']}」：終値と EMA{result['ema_slow_period']} の位置（{d['close_vs_ema_slow']}）、"
              f"EMA{result['ema_fast_period']} と EMA{result['ema_slow_period']} の位置（{d['ema_fast_vs_slow']}）、"
              f"EMA{result['ema_slow_period']} の傾き（{d['ema_slow_slope']}）、高値安値の切り上げ・切り下げ（{d['structure']}）の 4 点を点数化（合計 {trend['score']:+d}）")

    # X 投稿用の短文（全角 ≒ 140 文字以内が目安）
    arrow = {"強い上昇": "↑↑", "弱い上昇": "↑", "レンジ": "→", "弱い下落": "↓", "強い下落": "↓↓"}[trend["label"]]
    post = [f"📊 {sym} {tf} {arrow} {trend['label']}", f"現在 {_fmt(close)}"]
    if r1:
        post.append(f"R {_fmt(r1['price'])}" + (f" / {_fmt(res[1]['price'])}" if len(res) > 1 else ""))
    if s1:
        post.append(f"S {_fmt(s1['price'])}" + (f" / {_fmt(sup[1]['price'])}" if len(sup) > 1 else ""))
    if ch:
        post.append(("上昇CH" if ch["kind"] == "up" else "下降CH") + f" {_fmt(ch['lower_now'])}〜{_fmt(ch['upper_now'])}（{ch['position_text']}）")
    if r1 and s1:
        post.append(f"{_fmt(r1['price'])}超えで上値試し、{_fmt(s1['price'])}割れで調整に注意")
    post.append("#USDJPY #ドル円 #テクニカル分析")
    post_text = "\n".join(post)

    return {"long": long_text, "evidence": ev, "post": post_text}
