"""日本語の解説文（ルールベース）。第2ステージ版。

順番（docs/ANALYSIS_RULES.md「解説文」）:
  現在値と確定足 → （朝）前日の総括／（中間）朝からの変化点と前回の線への反応
  → 相場環境（EMA 3 本・点数）＋ただし書き → ダウ理論の構造（押し安値） → 日足の大局（前日・前週）
  → サポート・レジスタンス → チャネル → フィボナッチ → RSI とダイバージェンス → SQZMOM（1 行）
  → 値幅の目安（ATR） → 注目価格帯（上 2・下 2、根拠の重なり） → シナリオ（メイン／サブ） → 免責
断定表現（必ず・絶対）は使わない。最後に safety.sanitize で機械チェックする。
"""
from __future__ import annotations

import re

from . import safety

ENV_TEXT = {
    "強い上昇": "上昇基調がはっきりしています",
    "弱い上昇": "上昇寄りですが、勢いの裏付けは一部にとどまります",
    "レンジ": "方向感の乏しいレンジ相場です",
    "弱い下落": "下落寄りですが、勢いの裏付けは一部にとどまります",
    "強い下落": "下落基調がはっきりしています",
}
ARROW = {"強い上昇": "↑↑", "弱い上昇": "↑", "レンジ": "→", "弱い下落": "↓", "強い下落": "↓↓"}


def _fmt(p: float) -> str:
    return f"{p:.3f}"


def _zone_name(z: dict) -> str:
    return f"{_fmt(z['low'])}〜{_fmt(z['high'])}" if z["high"] - z["low"] >= 0.01 else _fmt(z["center"])


def _zone_kinds(z: dict, limit: int = 3) -> str:
    return "＋".join(z["kinds"][:limit])


# ---------------------------------------------------------------- シナリオ

def scenarios(result: dict) -> dict:
    close = result["close"]
    za, zb = result["zones"]["above"], result["zones"]["below"]
    res, sup = result["resistances"], result["supports"]
    st = result.get("structure") or {}
    fib = result.get("fibonacci")
    d = result["trend"].get("direction_effective", result["trend"]["direction"])

    def first_above(skip: float | None = None):
        for z in za:
            if skip is None or z["center"] > skip + 1e-9:
                return ("注目帯：" + _zone_kinds(z, 2), z["center"], z)
        for r in res:
            if skip is None or r["price"] > skip + 1e-9:
                return ("レジスタンス", r["price"], None)
        return None

    def first_below(skip: float | None = None):
        for z in zb:
            if skip is None or z["center"] < skip - 1e-9:
                return ("注目帯：" + _zone_kinds(z, 2), z["center"], z)
        for s in sup:
            if skip is None or s["price"] < skip - 1e-9:
                return ("サポート", s["price"], None)
        return None

    up = {"trigger": None, "target": None, "invalid": None}
    t = first_above()
    if t:
        up["trigger"] = {"name": t[0], "price": t[1]}
        nxt = first_above(t[1])
        if nxt is None and fib and fib["direction"] == "up":
            ext = fib["extensions"].get("1.0")
            if ext and ext > t[1]:
                nxt = ("フィボ目標 100%", ext, None)
        up["target"] = {"name": nxt[0], "price": nxt[1]} if nxt else None
    if st.get("direction") == "up" and st.get("key_level"):
        up["invalid"] = {"name": "押し安値", "price": st["key_level"]}
    else:
        b = first_below()
        up["invalid"] = {"name": b[0], "price": b[1]} if b else None

    dn = {"trigger": None, "target": None, "invalid": None}
    b = first_below()
    if b:
        dn["trigger"] = {"name": b[0], "price": b[1]}
        nxt = first_below(b[1])
        if nxt is None and fib and fib["direction"] == "down":
            ext = fib["extensions"].get("1.0")
            if ext and ext < b[1]:
                nxt = ("フィボ目標 100%", ext, None)
        dn["target"] = {"name": nxt[0], "price": nxt[1]} if nxt else None
    if st.get("direction") == "down" and st.get("key_level"):
        dn["invalid"] = {"name": "戻り高値", "price": st["key_level"]}
    else:
        a = first_above()
        dn["invalid"] = {"name": a[0], "price": a[1]} if a else None

    main = "up" if d > 0 else ("down" if d < 0 else None)

    def text(s: dict, side: str) -> str:
        if not s["trigger"]:
            return "目安になる価格帯がありません"
        verb = "上抜け" if side == "up" else "割り込み"
        out = f"{_fmt(s['trigger']['price'])}（{s['trigger']['name']}）を終値で{verb}"
        out += f" → {_fmt(s['target']['price'])}（{s['target']['name']}）へ" if s["target"] else " → 値幅の余地が広がる"
        if s["invalid"]:
            iv = "割れ" if side == "up" else "超え"
            out += f"。崩れる条件：{_fmt(s['invalid']['price'])}（{s['invalid']['name']}）を終値で{iv}"
        return out

    up["text"], dn["text"] = text(up, "up"), text(dn, "down")
    main_text = up["text"] if main == "up" else (dn["text"] if main == "down" else "レンジ：上下の注目帯の間での往来を基本に、どちらかを終値で抜けた方向を見る")
    return {"up": up, "down": dn, "main": main, "main_text": main_text}


# ---------------------------------------------------------------- 本文の各段落

def _ema_paragraph(result: dict) -> str:
    d = result["trend"]["details"]
    close = result["close"]
    f, s = d["ema_fast"], d["ema_slow"]
    pf, ps = result["ema_fast_period"], result["ema_slow_period"]
    l = d.get("ema_long")
    pl = result.get("ema_long_period")
    if l is None or not pl:
        return f"終値は EMA{ps}（{_fmt(s)}）の{d['close_vs_ema_slow']}、EMA{ps} は{d['ema_slow_slope']}。"
    above_all = close > f and close > s and close > l
    below_all = close < f and close < s and close < l
    if f > s > l and above_all:
        order = f"EMA{pf}＞EMA{ps}＞EMA{pl} の順に並び、現在値はその上にあります（上昇のパーフェクトオーダー）"
    elif f < s < l and below_all:
        order = f"EMA{pf}＜EMA{ps}＜EMA{pl} の順に並び、現在値はその下にあります（下落のパーフェクトオーダー）"
    else:
        pos = [f"{name}（{_fmt(v)}）の{'上' if close > v else '下'}" for name, v in ((f"EMA{pf}", f), (f"EMA{ps}", s), (f"EMA{pl}", l))]
        return (f"現在値は " + "、".join(pos) + f" にあり、3 本の移動平均の並びはそろっていません。EMA{ps} は{d['ema_slow_slope']}。")
    return (f"移動平均は {order}。EMA{ps} は{d['ema_slow_slope']}。"
            f"EMA{pl}（{_fmt(l)}）は長期の目安で、現在値はその{d.get('close_vs_ema_long', '')}です。")


def _structure_paragraph(result: dict) -> str:
    st = result.get("structure") or {}
    if not st or st.get("direction") is None:
        return ""
    t = f"ダウ理論（主要な高値・安値、振幅 ATR×2 以上の波だけで見る）：状態は「{st['state']}」。"
    if st.get("key_level") is not None:
        if st["direction"] == "up":
            t += (f"更新対象の高値は {_fmt(st['top_price'])}（{st.get('top_jst')}）、押し安値は {_fmt(st['key_level'])}（{st.get('key_jst')} の安値）で、"
                  f"終値でここを割らない限り上昇の構造は保たれます（判定には ATR の 1 割ほどの余裕を見ます）。")
        else:
            t += (f"更新対象の安値は {_fmt(st['top_price'])}（{st.get('top_jst')}）、戻り高値は {_fmt(st['key_level'])}（{st.get('key_jst')} の高値）で、"
                  f"終値でここを越えない限り下降の構造は保たれます（判定には ATR の 1 割ほどの余裕を見ます）。")
        if st.get("wick_breaks"):
            w = min(st["wick_breaks"]) if st["direction"] == "up" else max(st["wick_breaks"])
            t += f"ヒゲでは {_fmt(w)} まで{'割り込む' if st['direction'] == 'up' else '上抜ける'}場面がありましたが、終値では維持されています。"
        if st.get("flipped_jst"):
            t += f"直近の転換は {st['flipped_jst']}（{st.get('flipped_note')}）。"
    elif st.get("note"):
        t += st["note"] + "。"
    return t


def _daily_paragraph(result: dict) -> str:
    dl = result.get("daily")
    if not dl:
        return ""
    close = result["close"]
    parts = []
    de = dl.get("daily_ema")
    if de:
        datr = dl.get("daily_atr") or 0.0
        gap = de["close"] - de["value"]
        if datr and abs(gap) < datr * 0.15:
            parts.append(f"日足では、直近の確定日足（{de['date']}）の終値 {_fmt(de['close'])} が日足EMA{de['period']}（{_fmt(de['value'])}）とほぼ重なっており"
                         f"（差 {gap / result.get('pip', 0.01):+.0f} pips）、大局の方向は決め手を欠きます。")
        else:
            parts.append(f"日足では、直近の確定日足（{de['date']}）の終値 {_fmt(de['close'])} が日足EMA{de['period']}（{_fmt(de['value'])}）の"
                         f"{'上' if de['above'] else '下'}にあり、大局は{'上方向' if de['above'] else '下方向'}優位です。")
    pdv = dl.get("prev_day")
    if pdv:
        if pdv["low"] <= close <= pdv["high"]:
            where = f"前日高値 {_fmt(pdv['high'])} と前日安値 {_fmt(pdv['low'])} の間"
        elif close > pdv["high"]:
            where = f"前日高値 {_fmt(pdv['high'])} の上"
        else:
            where = f"前日安値 {_fmt(pdv['low'])} の下"
        parts.append(f"現在値は{where}（前日＝{pdv['label']} の足）。")
    pw = dl.get("prev_week")
    if pw:
        parts.append(f"前週（{pw['label']}）の高値 {_fmt(pw['high'])}・安値 {_fmt(pw['low'])}。")
    tw = dl.get("this_week")
    if tw:
        parts.append(f"今週ここまでの高値 {_fmt(tw['high'])}・安値 {_fmt(tw['low'])}。")
    return "".join(parts)


def _prev_day_summary(result: dict) -> str:
    dl = result.get("daily")
    if not dl or not dl.get("prev_day"):
        return ""
    p = dl["prev_day"]
    pip = result.get("pip", 0.01)
    body = p["close"] - p["open"]
    kind = "陽線" if body > 0 else ("陰線" if body < 0 else "十字線")
    rng = (p["high"] - p["low"]) / pip
    upper = (p["high"] - max(p["open"], p["close"])) / pip
    lower = (min(p["open"], p["close"]) - p["low"]) / pip
    shape = ""
    if rng > 0 and upper / rng > 0.45:
        shape = "。上ヒゲが長く、上値で売りに押された形"
    elif rng > 0 and lower / rng > 0.45:
        shape = "。下ヒゲが長く、下値で買いが入った形"
    return (f"直近の確定日足（{p['label']}）は始値 {_fmt(p['open'])} → 終値 {_fmt(p['close'])} の{kind}（値幅 {rng:.0f} pips、"
            f"高値 {_fmt(p['high'])}・安値 {_fmt(p['low'])}）{shape}。")


def _channel_paragraph(ch: dict | None) -> str:
    if not ch:
        return "はっきりした平行チャネルは引けていません（レンジ、または基準になる高安がそろっていない状態）。"
    name = "上昇チャネル" if ch["kind"] == "up" else "下降チャネル"
    rng = f"{name}（下限 {_fmt(ch['lower_now'])}／中央 {_fmt(ch['center_now'])}／上限 {_fmt(ch['upper_now'])}）"
    pos = ch["position_text"]
    if "上抜け" in pos:
        text = f"{rng}の上限を終値で上抜けています。"
    elif "割り込" in pos:
        text = f"{rng}の下限を終値で割り込んでいます。"
    else:
        text = f"{rng}の中にあり、現在は{pos}の位置です。"
    if ch["broken"]:
        if ch["kind"] == "up":
            text += "基準線（下限）を終値で割り込んでおり、上昇チャネルが崩れた可能性があります。"
        else:
            text += "基準線（上限）を終値で上抜けており、下降チャネルが崩れた可能性があります。"
    return text


def _fib_paragraph(result: dict) -> str:
    fib = result.get("fibonacci")
    if not fib:
        return ""
    wave_note = {"chart_major": "画像に写る範囲で最も大きな波", "structure": "ダウ理論の構造と同じ波"}.get(fib.get("wave"), "主要スイングの最後の推進波")
    if fib["direction"] == "up":
        base = (f"フィボナッチは {fib['start_jst']} の安値 {_fmt(fib['start_price'])}（押し安値）→ {fib['end_jst']} の高値 {_fmt(fib['end_price'])}"
                f"（{fib['wave_pips']:.0f} pips の上昇波・{wave_note}）を基準にしています。"
                if fib.get("wave") == "structure" else
                f"フィボナッチは {fib['start_jst']} の安値 {_fmt(fib['start_price'])} → {fib['end_jst']} の高値 {_fmt(fib['end_price'])}"
                f"（{fib['wave_pips']:.0f} pips の上昇波・{wave_note}）を基準にしています。")
    else:
        base = (f"フィボナッチは {fib['start_jst']} の高値 {_fmt(fib['start_price'])}（戻り高値）→ {fib['end_jst']} の安値 {_fmt(fib['end_price'])}"
                f"（{abs(fib['wave_pips']):.0f} pips の下降波・{wave_note}）を基準にしています。"
                if fib.get("wave") == "structure" else
                f"フィボナッチは {fib['start_jst']} の高値 {_fmt(fib['start_price'])} → {fib['end_jst']} の安値 {_fmt(fib['end_price'])}"
                f"（{abs(fib['wave_pips']):.0f} pips の下降波・{wave_note}）を基準にしています。")
    lv = fib["levels"]
    main = "、".join(f"{float(k) * 100:.1f}%＝{_fmt(v)}" for k, v in lv.items() if float(k) in (0.382, 0.5, 0.618))
    t = base + f"押し目（戻り）の目安は {main}。"
    if fib.get("current_band"):
        t += f"現在値は{fib['current_band']}の位置です。"
    # 他の根拠との重なり（注目価格帯の中身から拾う）
    overlaps = []
    for z in result["zones"]["above"] + result["zones"]["below"]:
        if "フィボナッチ" in z["kinds"] and len(z["kinds"]) >= 2:
            fl = [r.split("：", 1)[1] for r in z["reasons"] if r.startswith("フィボナッチ：")]
            others = [k for k in z["kinds"] if k != "フィボナッチ"]
            if fl:
                m = re.search(r"(\d+\.\d)%.*?(\d+\.\d{3})", fl[0])
                if m:
                    overlaps.append(f"{m.group(1)}% の {m.group(2)} は {'・'.join(others[:3])} と重なります")
    if overlaps:
        t += "根拠の重なり：" + "。".join(overlaps[:3]) + "。"
    tgt = result.get("fibonacci_target") or (fib if fib.get("extensions") else None)
    if tgt and tgt.get("extensions") and tgt.get("ext_base_price") is not None:
        pt = "押し" if tgt["direction"] == "up" else "戻り"
        names = {1.0: "N 計算値（100%）", 1.618: "161.8%"}
        t += (f"目標は直近の波 {_fmt(tgt['start_price'])}→{_fmt(tgt['end_price'])}（{tgt['start_jst']}→{tgt['end_jst']}）の"
              f"{pt}の極値 {_fmt(tgt['ext_base_price'])}（{tgt.get('ext_base_jst')}）を 3 点目にして、"
              + "、".join(f"{names.get(float(k), f'{float(k) * 100:.1f}%')}＝{_fmt(v)}" for k, v in tgt["extensions"].items()) + "。")
    proj = fib.get("projections") or {}
    if proj:
        t += "主波を伸ばした中期の目安は " + "、".join(f"{float(k) * 100:.1f}%＝{_fmt(v)}" for k, v in proj.items()) + "。"
    return t


def _rsi_paragraph(result: dict) -> str:
    r = result.get("rsi")
    if not r:
        return ""
    t = f"RSI(14) は {r['value']:.1f}。{r['zone']}で、{r['slope']}です。"
    divs = result.get("divergences") or []
    if divs:
        for d in divs:
            kind = "高値" if d["kind"] in ("bearish", "hidden_bearish") else "安値"
            t += (f"{d['label']}：{d['t1_jst']} の{kind} {_fmt(d['p1'])}（RSI {d['r1']:.1f}）→ {d['t2_jst']} の{kind} {_fmt(d['p2'])}"
                  f"（RSI {d['r2']:.1f}）。{d['meaning']}。")
        t += "ダイバージェンスは「反転」ではなく「勢いの変化」のサインとして扱い、構造の崩れと合わさって初めて転換の根拠にします。"
    else:
        t += "直近の確定スイングで RSI のダイバージェンスは検出されていません。"
    return t


CIRCLED = "①②③④⑤"


def _zones_paragraph(result: dict) -> tuple[str, list[str]]:
    za, zb = result["zones"]["above"], result["zones"]["below"]
    lines = []
    ev = []
    if za:
        s = "上の注目価格帯：" + "　".join(
            f"{CIRCLED[i]} {_zone_name(z)}（{z['distance_text']}・{z['distance_pips']:.0f} pips）＝{_zone_kinds(z)}" for i, z in enumerate(za[:5]))
        lines.append(s)
    if zb:
        s = "下の注目価格帯：" + "　".join(
            f"{CIRCLED[i]} {_zone_name(z)}（{z['distance_text']}・{z['distance_pips']:.0f} pips）＝{_zone_kinds(z)}" for i, z in enumerate(zb[:5]))
        lines.append(s)
    for side, zs in (("上", za), ("下", zb)):
        for i, z in enumerate(zs[:5]):
            ev.append(f"{side}の注目価格帯{CIRCLED[i]} {_zone_name(z)}（得点 {z['score']:.1f}）：" + "／".join(z["reasons"][:5]))
    return "\n".join(lines), ev


# ---------------------------------------------------------------- まとめ

def _x_units(s: str) -> int:
    return sum(1 if ord(ch) < 128 else 2 for ch in s)


def _fit_post(lines: list[str], max_units: int, keep_last: int = 1) -> str:
    body = list(lines)
    while _x_units("\n".join(body)) > max_units and len(body) > keep_last + 2:
        del body[-1 - keep_last]
    return "\n".join(body)


def max_units_of(posting: dict) -> int:
    return int(posting.get("x_max_units", 280))


def _hashtag_line(posting: dict) -> str:
    """ハッシュタグは config の posting.hashtags（文字列でもリストでも可）。"""
    tags = posting.get("hashtags", "#USDJPY #ドル円 #テクニカル分析")
    if isinstance(tags, (list, tuple)):
        tags = " ".join(str(t).strip() for t in tags if str(t).strip())
    return str(tags)


def _fit_post_priority(items: list[tuple[int, str]], max_units: int) -> str:
    """(優先度, 行) の列。優先度 0 は落とさない。上限を超える間、優先度の大きい行から順に落とす。"""
    body = list(items)
    while _x_units("\n".join(t for _, t in body)) > max_units:
        droppable = [i for i, (pr, _) in enumerate(body) if pr > 0]
        if not droppable:
            break
        worst = max(droppable, key=lambda i: body[i][0])
        del body[worst]
    # 空行が続いたら 1 本に
    out: list[str] = []
    for _, t in body:
        if t == "" and (not out or out[-1] == ""):
            continue
        out.append(t)
    return "\n".join(out)


def _ema_short(result: dict) -> str:
    d = result["trend"]["details"]
    close = result["close"]
    f, s = d["ema_fast"], d["ema_slow"]
    pf, ps, pl = result["ema_fast_period"], result["ema_slow_period"], result.get("ema_long_period")
    l = d.get("ema_long")
    if l is None or not pl:
        return f"終値は EMA{ps} の{d['close_vs_ema_slow']}、EMA{ps} は{d['ema_slow_slope']}"
    if f > s > l and close > f:
        return f"EMA{pf}＞{ps}＞{pl} の上昇パーフェクトオーダーで、現在値はその上。EMA{ps} は{d['ema_slow_slope']}"
    if f < s < l and close < f:
        return f"EMA{pf}＜{ps}＜{pl} の下落パーフェクトオーダーで、現在値はその下。EMA{ps} は{d['ema_slow_slope']}"
    if close > f and close > s and close > l:
        return f"現在値は EMA{pf}・{ps}・{pl} すべての上（並びはそろっていない）。EMA{ps} は{d['ema_slow_slope']}"
    if close < f and close < s and close < l:
        return f"現在値は EMA{pf}・{ps}・{pl} すべての下（並びはそろっていない）。EMA{ps} は{d['ema_slow_slope']}"
    pos = [f"EMA{n} の{'上' if close > v else '下'}" for n, v in ((pf, f), (ps, s), (pl, l))]
    return "現在値は " + "、".join(pos) + f"。EMA{ps} は{d['ema_slow_slope']}"


_WD_JA = "月火水木金土日"

# 投稿の型（posting.post_style）
#   short          … 280 向けの 6 行（旧来）
#   long           … 1 本の長文。並び順は posting.layout（classic＝環境→構造→…→シナリオ／scenario_first＝シナリオ→注目帯→環境…）
#   thread         … 短い本体＋返信 2 投（本体＝分かれ目・シナリオ・根拠、返信 1＝環境・構造・日足・チャネル、返信 2＝線・RSI・SQZMOM・値幅・2 番目の帯）
# 2026-10-04 の X 発信リサーチ（docs/X発信リサーチ_2026-10-04.md 5・9 章）に基づく。どれも config だけで切り替えられる。


def _date_label(result: dict) -> str:
    at = result.get("analyzed_at_jst")
    if not at:
        return ""
    try:
        from datetime import datetime as _dt
        d = _dt.strptime(at[:10], "%Y-%m-%d")
        return f"{d.strftime('%m/%d')}({_WD_JA[d.weekday()]})"
    except ValueError:
        return at[:10]


def _verdict(result: dict) -> dict | None:
    v = (result.get("changes") or {}).get("verdict")
    return v if isinstance(v, dict) and (v.get("up") or v.get("down")) else None


def _hook_short(result: dict, sc: dict, main: str | None) -> str:
    """タイトル行に入れる短い争点：朝は「158.00 が分かれ目」、夜は答え合わせ「朝の 158.00 は抜けず」。"""
    v = _verdict(result)
    if result.get("slot") == "evening" and v and v.get("main_side"):
        m, up = v["main_side"], v["main"] == "up"
        t = f"{m['trigger']:.2f}"
        st = m["status"]
        if st == "未発動":
            return f"朝の {t} は{'抜けず' if up else '割れず'}"
        if st == "発動":
            return f"朝の {t} を{'抜けた' if up else '割った'}"
        if st == "到達":
            return f"朝の {t} を{'抜けて' if up else '割って'} {m['target']:.2f} に到達"
        return f"朝の見立ては崩れ（{m['invalid']:.2f} {'割れ' if up else '超え'}）"
    if main in ("up", "down"):
        s = sc["up"] if main == "up" else sc["down"]
        if s.get("trigger"):
            return f"{s['trigger']['price']:.2f} が分かれ目"
    za, zb = result["zones"]["above"], result["zones"]["below"]
    if za and zb:
        return f"{zb[0]['high']:.2f}〜{za[0]['low']:.2f} の往来"
    return ""


def _title_lines(result: dict, posting: dict, sc: dict, main: str | None, label: str, slot_label: str) -> list[str]:
    """投稿の頭：タイトル（【今日のドル円】10/04(土) 朝のプラン｜158.00 が分かれ目）→ 一言のタグライン → 📊 相場環境 ＋ 現在値 → 🔑 結論 1 行。
    X で読まれている相場解説の共通点（1 行目に争点・冒頭 2 行で結論・画像つき・毎日同じ型・【ドル円】見出し）を型にしたもの。
    文言は config の posting.title で変えられる。"""
    tcfg = posting.get("title") or {}
    sym, tf, close = result["symbol"], result["timeframe_label"], result["close"]
    conf = result.get("confirmed") or {}
    slot = result.get("slot", "morning")
    tmpl = tcfg.get(slot) or ("【今日のドル円】{date} 朝のプラン｜{hook_short}" if slot == "morning" else "【今日のドル円】{date} 夜の中間報告｜{hook_short}")
    head = str(tmpl).format(date=_date_label(result), slot=slot_label, symbol=sym, timeframe=tf, hook_short=_hook_short(result, sc, main))
    head = head.rstrip("｜| ")   # 争点が作れなかったときに区切りだけ残さない
    out = [head]
    tagline = tcfg.get("tagline")
    if tagline:
        out.append(str(tagline))
    out.append(f"📊 {sym} {tf} {ARROW[label]} {label}｜現在 {_fmt(close)}（{conf.get('last_end_jst', '')} 確定足まで）")
    if tcfg.get("hook", True):
        hk = _hook(result, sc, main)
        if hk:
            out.append("🔑 " + hk)
    return out


def _hook(result: dict, sc: dict, main: str | None) -> str:
    """結論 1 行（キャッチ）。断定しない言い回しで「どこを抜けたら・割ったらどうなるか」を先に出す。"""
    sq = result.get("sqzmom") or {}
    pre = f"値動きは {sq['streak']} 本圧縮中。" if sq.get("squeeze_on") and sq.get("streak") else ("値動きは圧縮中。" if sq.get("squeeze_on") else "")
    if main in ("up", "down"):
        s = sc["up"] if main == "up" else sc["down"]
        if not s.get("trigger"):
            return ""
        trg = _fmt(s["trigger"]["price"])
        if main == "up":
            t = f"{pre}{trg} を終値で抜けるか"
            if s.get("target"):
                t += f"。抜ければ {_fmt(s['target']['price'])} が視野"
            if s.get("invalid"):
                t += f"、{_fmt(s['invalid']['price'])} 割れで上目線は崩れ"
        else:
            t = f"{pre}{trg} を終値で割るか"
            if s.get("target"):
                t += f"。割れば {_fmt(s['target']['price'])} が視野"
            if s.get("invalid"):
                t += f"、{_fmt(s['invalid']['price'])} 超えで下目線は崩れ"
        return t
    za, zb = result["zones"]["above"], result["zones"]["below"]
    if za and zb:
        return f"{pre}{_fmt(zb[0]['high'])}〜{_fmt(za[0]['low'])} の往来。終値で抜けた側を見る"
    return ""


def _level_tag(l: dict) -> str:
    """線に名札：156.587（反応 8 回・9/30）。裸の数字を出さない（リサーチ 3-1）。"""
    t = _fmt(l["price"])
    bits = []
    if l.get("touches"):
        bits.append(f"反応 {l['touches']} 回")
    lt = l.get("last_touch_jst")
    if lt and len(lt) >= 5:
        bits.append(lt[:5].lstrip("0").replace("/0", "/"))
    return t + (f"（{'・'.join(bits)}）" if bits else "")


def _reason_line(result: dict, label: str) -> str:
    """▼判断の根拠：押し安値 156.822 が終値で無傷＋EMA20・50・200 の上、で「上昇の構造」。前提が崩れる価格は 156.822 の 1 つだけ"""
    st = result.get("structure") or {}
    d = result["trend"]["details"]
    close = result["close"]
    pf, ps, pl = result["ema_fast_period"], result["ema_slow_period"], result.get("ema_long_period")
    emas = [(pf, d["ema_fast"]), (ps, d["ema_slow"])] + ([(pl, d["ema_long"])] if d.get("ema_long") is not None and pl else [])
    above = [n for n, v in emas if close > v]
    below = [n for n, v in emas if close < v]
    if len(above) == len(emas):
        ema_txt = "EMA" + "・".join(str(n) for n in above) + " の上"
    elif len(below) == len(emas):
        ema_txt = "EMA" + "・".join(str(n) for n in below) + " の下"
    else:
        ema_txt = "EMA の上下に挟まれた位置"
    if st.get("key_level") is not None and st.get("direction") in ("up", "down"):
        up = st["direction"] == "up"
        nm = "押し安値" if up else "戻り高値"
        hurt = "ヒゲでは割れたが終値では無傷" if (up and st.get("wick_breaks")) else ("ヒゲでは超えたが終値では無傷" if (not up and st.get("wick_breaks")) else "終値で無傷")
        return (f"▼判断の根拠：{nm} {_fmt(st['key_level'])} が{hurt}＋{ema_txt}、で「{'上昇' if up else '下降'}の構造」と判定（相場環境は「{label}」）。"
                f"前提が崩れる価格は {_fmt(st['key_level'])} の 1 つだけ")
    return f"▼判断の根拠：{ema_txt}、主要な高値安値は「{d['structure']}」で相場環境は「{label}」"


def _side_label(side: dict, up: bool) -> str:
    t = f"{side['trigger']:.3f} 終値{'超え' if up else '割れ'}"
    if side.get("target") is not None:
        t += f" → {side['target']:.3f}"
    return t


def _answer_lines(result: dict) -> list[str]:
    """✅ 答え合わせ。夜は「朝のプラン」を 2〜3 行、朝は「昨夜のプラン」を 1 行。前回の結果（台帳）が無ければ出ない。"""
    v = _verdict(result)
    if not v:
        return []
    up_first = v.get("main") != "down"
    sides = [("up", True), ("down", False)] if up_first else [("down", False), ("up", True)]
    names = {"up": "メイン" if v.get("main") == "up" else ("サブ" if v.get("main") == "down" else "上方向"),
             "down": "メイン" if v.get("main") == "down" else ("サブ" if v.get("main") == "up" else "下方向")}
    if result.get("slot") == "evening":
        out = ["✅ 朝のプランの答え合わせ"]
        for k, up in sides:
            sd = v.get(k)
            if sd:
                out.append(f"{names[k]}（{_side_label(sd, up)}）：{sd['status']}。{sd['detail']}")
        chg = result.get("changes") or {}
        rx = [r for r in chg.get("reactions", []) if "届いていません" not in r]
        if rx:
            out.append("→ " + "／".join(rx[:2]))
        return out
    # 朝：昨夜のプランを 1 行
    bits = [f"{names[k]}{v[k]['status']}" for k, _ in sides if v.get(k)]
    when = "昨夜" if v.get("prev_slot") == "evening" else "前回"
    return [f"✅ {when}のプラン：" + "・".join(bits)] if bits else []


def _post_blocks(result: dict, posting: dict, sc: dict, main: str | None, label: str, slot_label: str) -> dict[str, list[tuple[int, str]]]:
    """投稿の部品（(優先度, 行) の列）。並べ方は post_style／layout が決める。"""
    sym, tf, close = result["symbol"], result["timeframe_label"], result["close"]
    tr = result["trend"]
    st = result.get("structure") or {}
    sup, res = result["supports"], result["resistances"]
    ch = result.get("channel")
    za, zb = result["zones"]["above"], result["zones"]["below"]
    B: dict[str, list[tuple[int, str]]] = {}

    B["title"] = [(0, t) for t in _title_lines(result, posting, sc, main, label, slot_label)]
    B["answer"] = [(0, t) for t in _answer_lines(result)]

    env = f"▼相場環境：{_ema_short(result)}。{tr['details']['structure']}"
    if tr.get("label_effective") and tr["label_effective"] != tr["label"]:
        env += f"。点数だけなら「{tr['label']}」だが構造と食い違うため一段弱めて「{label}」"
    B["env"] = [(2, env)]

    if st.get("key_level") is not None and st.get("direction") in ("up", "down"):
        up = st["direction"] == "up"
        B["structure"] = [(0, f"▼構造（ダウ理論）：{st['state']}。更新対象の{'高値' if up else '安値'} {_fmt(st['top_price'])}（{(st.get('top_jst') or '')[:5]}）／"
                               f"{'押し安値' if up else '戻り高値'} {_fmt(st['key_level'])}（{(st.get('key_jst') or '')[:5]}）。終値で{'押し安値を割らない' if up else '戻り高値を越えない'}限り"
                               f"{'上昇' if up else '下降'}の構造は維持")]
    elif st.get("state"):
        B["structure"] = [(0, f"▼構造（ダウ理論）：{st['state']}")]
    else:
        B["structure"] = []

    dl = result.get("daily") or {}
    de = dl.get("daily_ema")
    B["daily"] = []
    if de:
        datr = dl.get("daily_atr") or 0.0
        gap = de["close"] - de["value"]
        pd_ = dl.get("prev_day") or {}
        candle = ""
        if pd_.get("open") is not None and pd_.get("close") is not None:
            candle = f"直近の確定日足（{pd_.get('label', de.get('date', ''))}）は{'陽線' if pd_['close'] >= pd_['open'] else '陰線'}。"
        if datr and abs(gap) < datr * 0.15:
            B["daily"].append((3, f"▼日足：{candle}終値 {_fmt(de['close'])} は日足EMA{de['period']}（{_fmt(de['value'])}）とほぼ重なり、大局は決め手を欠く"))
        else:
            B["daily"].append((3, f"▼日足：{candle}終値 {_fmt(de['close'])} は日足EMA{de['period']}（{_fmt(de['value'])}）の{'上' if de['above'] else '下'}で、大局は{'上' if de['above'] else '下'}優位"))

    B["levels"] = []
    if sup:
        B["levels"].append((1, "▼サポート " + "／".join(_level_tag(l) for l in sup)))
    if res:
        B["levels"].append((1, "▼レジスタンス " + "／".join(_level_tag(l) for l in res)))
    B["channel"] = [(4, f"▼チャネル：{'上昇' if ch['kind'] == 'up' else '下降'}CH 下限 {_fmt(ch['lower_now'])}／中央 {_fmt(ch['center_now'])}／上限 {_fmt(ch['upper_now'])}。現在は{ch['position_text']}")] if ch else []

    B["rsi"] = []
    r = result.get("rsi")
    if r:
        dv = result.get("divergences") or []
        dtxt = "、".join(d["label"] for d in dv) if dv else "ダイバージェンスなし"
        zone = str(r["zone"]).split("（")[0]
        B["rsi"].append((2, f"▼RSI(14) {r['value']:.1f}：{zone}・{r['slope']}。{dtxt}"))
    B["sqzmom"] = []
    sq = result.get("sqzmom")
    if sq:
        if sq["squeeze_on"]:
            state = f"スクイーズ {sq['streak']} 本連続"
            if sq.get("median_run"):
                state += f"（過去の中央値 {sq['median_run']:.0f} 本）"
        elif sq.get("since_release") is not None and sq["since_release"] <= 6:
            state = f"スクイーズ解放から {sq['since_release'] + 1} 本目"
        else:
            state = "スクイーズなし"
        B["sqzmom"].append((4, f"▼SQZMOM：{state}。モメンタムは{'プラス' if sq['value'] > 0 else 'マイナス'}で{'拡大' if sq['expanding'] else '縮小'}中"))
    B["atr"] = []
    ac = result.get("atr_context")
    if ac:
        t = f"▼値幅の目安：{tf} ATR {ac['atr_pips']:.0f} pips"
        if ac.get("daily_atr_pips"):
            t += f"／日足 ATR {ac['daily_atr_pips']:.0f} pips"
        B["atr"].append((6, t))

    B["zones"] = []
    B["zones_first"] = []     # 上下 1 本ずつ（thread の本体用）
    B["zones_second"] = []    # 2 番目の帯（thread の返信用）
    if za or zb:
        B["zones"].append((1, "▼注目価格帯"))
        for i, z in enumerate(za[:2]):
            line = f"上{CIRCLED[i]} {_zone_name(z)}＝{_zone_kinds(z, 3)}（{z['distance_text']}）"
            B["zones"].append((1 if i == 0 else 5, line))
            (B["zones_first"] if i == 0 else B["zones_second"]).append((1, line))
        for i, z in enumerate(zb[:2]):
            line = f"下{CIRCLED[i]} {_zone_name(z)}＝{_zone_kinds(z, 3)}（{z['distance_text']}）"
            B["zones"].append((1 if i == 0 else 5, line))
            (B["zones_first"] if i == 0 else B["zones_second"]).append((1, line))

    def sc_line(name: str, s: dict, up: bool) -> str:
        if not s.get("trigger"):
            return f"{name}：発動条件なし（根拠の重なる帯が見当たらない）"
        t = f"{name}：{_fmt(s['trigger']['price'])} を終値で{'超え' if up else '割れ'} → "
        t += _fmt(s["target"]["price"]) if s.get("target") else "次の帯"
        if s.get("invalid"):
            t += f"。崩れる条件：{_fmt(s['invalid']['price'])} {'割れ' if up else '超え'}"
        return t
    S = [(0, "▼シナリオ")]
    if main == "up":
        S += [(0, sc_line("メイン（上）", sc["up"], True)), (1, sc_line("サブ（下）", sc["down"], False))]
    elif main == "down":
        S += [(0, sc_line("メイン（下）", sc["down"], False)), (1, sc_line("サブ（上）", sc["up"], True))]
    else:
        S += [(0, f"{sc['main_text']}"), (1, sc_line("上方向", sc["up"], True)), (1, sc_line("下方向", sc["down"], False))]
    B["scenario"] = S
    B["reason"] = [(2, _reason_line(result, label))]
    slot = result.get("slot", "morning")
    nxt = posting.get("next_note") or {}
    B["next"] = [(3, str(nxt[slot]))] if nxt.get(slot) else []
    B["disclaimer"] = [(0, str(posting.get("disclaimer_long") or "※テクニカル分析の参考情報であり投資助言ではありません。価格は参考値（15分以上の遅延あり）、判定は確定足の終値に基づきます"))]
    B["disclaimer_short"] = [(0, str(posting.get("disclaimer_short") or "※テクニカル分析の参考情報で、売買の勧誘ではありません。判定は確定足の終値"))]
    B["tags"] = [(0, _hashtag_line(posting))] if _hashtag_line(posting).strip() else []
    return B


_SEP = [(0, "")]


def _long_post(result: dict, posting: dict, sc: dict, main: str | None, label: str, slot_label: str) -> list[tuple[int, str]]:
    B = _post_blocks(result, posting, sc, main, label, slot_label)
    layout = str(posting.get("layout", "scenario_first"))
    if layout == "classic":
        order = ["title", _SEP, "answer", _SEP, "env", "structure", "daily", "levels", "channel", "rsi", "sqzmom", "atr", _SEP, "zones", _SEP, "scenario", _SEP, "disclaimer", "tags"]
    else:   # scenario_first（リサーチ第 2 案）：分かれ目 → シナリオ → 注目帯 → 環境・構造・日足 → 線と指標 → 根拠 → 免責
        order = ["title", _SEP, "answer", _SEP, "scenario", _SEP, "zones", _SEP, "env", "structure", "daily", "levels", "channel", "rsi", "sqzmom", "atr", _SEP, "reason", "next", _SEP, "disclaimer", "tags"]
    out: list[tuple[int, str]] = []
    for k in order:
        out += k if isinstance(k, list) else B[k]
    return out


def _thread_post(result: dict, posting: dict, sc: dict, main: str | None, label: str, slot_label: str) -> tuple[list[tuple[int, str]], list[list[tuple[int, str]]]]:
    """リサーチ第 1 案：短い本体＋返信 2 投。本体だけ読んでも、返信まで読んでも成立する。"""
    B = _post_blocks(result, posting, sc, main, label, slot_label)
    zf = ([(1, "▼見ている水準（上下 1 本ずつ）")] + B["zones_first"]) if B["zones_first"] else []
    body = B["title"] + _SEP + B["answer"] + _SEP + zf + _SEP + B["scenario"] + _SEP + B["reason"] + B["next"] + _SEP + B["disclaimer_short"] + B["tags"]
    r1 = [(0, "▼補足①（環境・構造・日足）")] + B["env"] + B["structure"] + B["daily"] + B["channel"]
    r2 = [(0, "▼補足②（線と指標）")] + B["levels"] + B["rsi"] + B["sqzmom"] + B["atr"] + ([(1, "2 番目の注目帯：" + "／".join(t for _, t in B["zones_second"]))] if B["zones_second"] else [])
    return body, [r1, r2]


def build(result: dict, posting: dict | None = None) -> dict:
    posting = posting or {}
    sym, tf, close = result["symbol"], result["timeframe_label"], result["close"]
    tr = result["trend"]
    label = tr.get("label_effective", tr["label"])
    sup, res = result["supports"], result["resistances"]
    ch = result.get("channel")
    slot = result.get("slot", "morning")
    slot_label = "朝のプラン" if slot == "morning" else "中間報告"
    conf = result.get("confirmed") or {}
    chg = result.get("changes") or {}
    sc = result.get("scenarios") or scenarios(result)

    lines: list[str] = []
    head = f"{sym} {tf}（{slot_label}）。現在値 {_fmt(close)} 円。"
    if conf:
        head += f"判定は {conf['last_start_jst']} 始まりの足（{conf['last_end_jst']} 確定）までの確定足に基づきます。"
    lines.append(head)

    # 朝：前日の総括／中間：変化点と前回の線への反応
    if slot == "morning":
        pdsum = _prev_day_summary(result)
        if pdsum:
            lines.append("■ 前日の総括　" + pdsum)
        al = _answer_lines(result)
        if al:
            lines.append("■ " + al[0].lstrip("✅ "))
        if chg.get("available") and chg.get("reactions"):
            lines.append("■ 前回の注目帯への反応　" + "／".join(chg["reactions"]))
    else:
        al = _answer_lines(result)
        if al:
            lines.append("■ 朝のプランの答え合わせ　" + "\n".join(al[1:]))
        if chg.get("available"):
            body = "／".join(chg.get("lines", [])) or "大きな変化はありません。"
            lines.append("■ 前回からの変化点　" + body)
            if chg.get("reactions"):
                lines.append("■ 前回の注目帯への反応　" + "／".join(chg["reactions"]))
        tdy = (result.get("daily") or {}).get("today")
        if tdy:
            lines.append(f"■ 本日ここまで　高値 {_fmt(tdy['high'])}・安値 {_fmt(tdy['low'])}・直近 {_fmt(tdy['close'])}。")

    # 相場環境
    env = f"■ 相場環境　「{label}」。{ENV_TEXT[label]}。"
    if tr.get("label_effective") and tr["label_effective"] != tr["label"]:
        env += f"（点数だけなら「{tr['label']}」ですが、下の理由で一段弱めています）"
    env += tr["details"]["structure"] + "。" + _ema_paragraph(result)
    if tr.get("caveat"):
        env += tr["caveat"]
    lines.append(env)

    stp = _structure_paragraph(result)
    if stp:
        lines.append("■ 構造　" + stp)
    dp = _daily_paragraph(result)
    if dp:
        lines.append("■ 日足の大局　" + dp)

    sr = ("サポートは " + "、".join(f"{_fmt(l['price'])}円" for l in sup) + "。") if sup else "表示範囲に明確なサポート候補はありません。"
    sr += ("レジスタンスは " + "、".join(f"{_fmt(l['price'])}円" for l in res) + "。") if res else "表示範囲に明確なレジスタンス候補はありません。"
    lines.append("■ サポート・レジスタンス　" + sr)
    lines.append("■ チャネル　" + _channel_paragraph(ch))
    if result.get("fibonacci"):
        lines.append("■ フィボナッチ　" + _fib_paragraph(result))
    rp = _rsi_paragraph(result)
    if rp:
        lines.append("■ RSI　" + rp)
    if result.get("sqzmom"):
        lines.append("■ SQZMOM　" + result["sqzmom"]["text"].split("：", 1)[-1])
    if result.get("atr_context"):
        from .momentum import atr_text
        lines.append("■ 値幅の目安　" + atr_text(result["atr_context"]).split("：", 1)[-1])
    zp, zone_ev = _zones_paragraph(result)
    if zp:
        lines.append("■ 注目価格帯（根拠が重なる所）\n" + zp)

    main = sc.get("main")
    if main == "up":
        lines.append(f"■ シナリオ　メイン（上方向）：{sc['up']['text']}。\nサブ（下方向）：{sc['down']['text']}。")
    elif main == "down":
        lines.append(f"■ シナリオ　メイン（下方向）：{sc['down']['text']}。\nサブ（上方向）：{sc['up']['text']}。")
    else:
        lines.append(f"■ シナリオ　{sc['main_text']}。\n上方向：{sc['up']['text']}。\n下方向：{sc['down']['text']}。")
    lines.append(safety.DISCLAIMER)
    long_text = "\n".join(lines)

    # シナリオ表（markdown）
    def row(name: str, s: dict) -> str:
        trg = f"{_fmt(s['trigger']['price'])} を終値で{'上抜け' if name.startswith('上') else '割り込み'}（{s['trigger']['name']}）" if s.get("trigger") else "—"
        tgt = f"{_fmt(s['target']['price'])}（{s['target']['name']}）" if s.get("target") else "—"
        inv = f"{_fmt(s['invalid']['price'])}（{s['invalid']['name']}）" if s.get("invalid") else "—"
        return f"| {name} | {trg} | {tgt} | {inv} |"
    tag_up = "上方向（メイン）" if main == "up" else "上方向"
    tag_dn = "下方向（メイン）" if main == "down" else "下方向"
    table = "| シナリオ | 発動条件 | 行き先 | 崩れる条件 |\n|---|---|---|---|\n" + row(tag_up, sc["up"]) + "\n" + row(tag_dn, sc["down"])

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
                      f"上限線はそれと平行で、{ch['far_jst']} の高値 {_fmt(ch['far_price'])} を通る（接触 {ch['touches_far']} 回）。中央線は上限と下限の中間")
        else:
            ev.append(f"下降チャネル：上限線は {ch['t1_jst']} と {ch['t2_jst']} の高値を結んだ線（接触 {ch['touches_base']} 回）。"
                      f"下限線はそれと平行で、{ch['far_jst']} の安値 {_fmt(ch['far_price'])} を通る（接触 {ch['touches_far']} 回）。中央線は上限と下限の中間")
    st = result.get("structure") or {}
    if st.get("key_level") is not None:
        nm = "押し安値" if st["direction"] == "up" else "戻り高値"
        ev.append(f"{nm} {_fmt(st['key_level'])}：更新対象の{'高値' if st['direction'] == 'up' else '安値'} {_fmt(st['top_price'])}"
                  f"（{st.get('top_jst')}）を付ける起点になった主要{'安値' if st['direction'] == 'up' else '高値'}（{st.get('key_jst')}）。"
                  f"ダウ理論で構造が崩れるかどうかを決める唯一の価格")
    fib = result.get("fibonacci")
    if fib:
        wv = {"chart_major": "画像に写る範囲で最も大きな波（主波）", "structure": "ダウ理論の構造と同じ波（押し安値→更新対象の高値）"}.get(fib.get("wave"), "主要スイングの最後の推進波")
        ev.append(f"フィボナッチ：{wv} {_fmt(fib['start_price'])}（{fib['start_jst']}）→ {_fmt(fib['end_price'])}（{fib['end_jst']}）"
                  f"を 0〜100% とし、38.2／50／61.8% を押し目（戻り）の目安として描画。23.6／78.6% は文章のみ。"
                  f"目標（N 計算値・161.8%）は終点の後の押し（戻り）の極値を 3 点目にして計算")
    for d in result.get("divergences") or []:
        ev.append(f"{d['label']}：価格 {_fmt(d['p1'])}→{_fmt(d['p2'])}、RSI {d['r1']:.1f}→{d['r2']:.1f}（{d['t1_jst']}→{d['t2_jst']}）。"
                  f"価格差が ATR×0.3 以上・RSI 差が 3 以上・2 つ目のピボットが直近 20 本以内の条件を満たす")
    d = tr["details"]
    ev.append(f"相場環境「{tr['label']}」：終値と EMA{result['ema_slow_period']} の位置（{d['close_vs_ema_slow']}）、"
              f"EMA{result['ema_fast_period']} と EMA{result['ema_slow_period']} の位置（{d['ema_fast_vs_slow']}）、"
              f"EMA{result['ema_slow_period']} の傾き（{d['ema_slow_slope']}）、主要な高値安値の切り上げ・切り下げ（{d['structure']}）の 4 点を点数化（合計 {tr['score']:+d}）"
              + (f"。ダウ理論の構造と食い違うため表示は「{label}」に一段弱めた" if label != tr["label"] else ""))
    ev.extend(zone_ev)
    dl = result.get("daily") or {}
    if dl.get("prev_day"):
        p = dl["prev_day"]
        ev.append(f"前日高値 {_fmt(p['high'])}・前日安値 {_fmt(p['low'])}（{p['label']} の日足。確定した最後の日足から機械的に決まる水準）")

    # X 投稿用の短文（全角 2・半角 1 で x_max_units 以内）。入りきらないときは後ろの行から落とす（ハッシュタグは残す）
    za, zb = result["zones"]["above"], result["zones"]["below"]
    post = _title_lines(result, posting, sc, main, label, slot_label)
    if za:
        post.append(f"上の注目帯 {_zone_name(za[0])}＝{_zone_kinds(za[0], 2)}")
    if zb:
        post.append(f"下の注目帯 {_zone_name(zb[0])}＝{_zone_kinds(zb[0], 2)}")
    # メインは短く：「158.000 上抜け→159.018」
    main_s = sc["up"] if main == "up" else (sc["down"] if main == "down" else None)
    if main_s and main_s.get("trigger"):
        verb = "上抜け" if main == "up" else "割れ"
        line = f"メイン：{_fmt(main_s['trigger']['price'])} {verb}"
        if main_s.get("target"):
            line += f"→{_fmt(main_s['target']['price'])}"
        post.append(line)
    elif main is None:
        post.append("メイン：上下の注目帯の間での往来。終値で抜けた方向を見る")
    if st.get("key_level") is not None and st.get("direction") in ("up", "down"):
        post.append(("押し安値 " if st["direction"] == "up" else "戻り高値 ") + _fmt(st["key_level"]) + " が分かれ目")
    # 長い形（ブルー認証向け・SHO 2026-10-04）：チャートの下に「相場環境 → 構造 → 日足 → 線 → RSI/SQZMOM → 注目帯 → シナリオ」の順で
    # ほどほどの長さ（短い形の約 4 倍、1,100〜1,300 単位が目安）。上限を超えるときは優先度の低い行から落とす
    style = str(posting.get("post_style", "short"))
    replies: list[str] = []
    if style == "long":
        post_text = _fit_post_priority(_long_post(result, posting, sc, main, label, slot_label), max_units_of(posting))
    elif style == "thread":
        body, reps = _thread_post(result, posting, sc, main, label, slot_label)
        reply_max = int(posting.get("reply_max_units", max_units_of(posting)))
        post_text = _fit_post_priority(body, max_units_of(posting))
        replies = [_fit_post_priority(r, reply_max) for r in reps]
    else:
        post.append(_hashtag_line(posting))
        post_text = _fit_post(post, max_units_of(posting))
    max_units = max_units_of(posting)

    # 表現の安全弁
    long_text, hits1 = safety.sanitize(long_text)
    table, hits2 = safety.sanitize(table)
    post_text, hits3 = safety.sanitize(post_text)
    hits = list(hits1 + hits2 + hits3)
    clean_replies = []
    for r in replies:
        r2, h = safety.sanitize(r)
        clean_replies.append(r2)
        hits += h
    hits = sorted(set(hits))
    # 画像に焼き込む 2 行（リサーチ 9 章の 6：タイトル帯と 🔑 結論。投稿の 1 行目と同じ文言にして、画像だけ見ても結論が分かるようにする）
    title_line, _ = safety.sanitize(_title_lines(result, posting, sc, main, label, slot_label)[0])
    hook_line, _ = safety.sanitize(_hook(result, sc, main))
    return {"long": long_text, "table": table, "evidence": ev, "post": post_text, "post_replies": clean_replies,
            "post_style": style, "safety_hits": hits,
            "x_units": _x_units(post_text), "reply_units": [_x_units(r) for r in clean_replies],
            "post_over_limit": _x_units(post_text) > max_units,
            "title_line": title_line, "hook": hook_line}
