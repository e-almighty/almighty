"""前回の結果を残し、次回に「変化点」と「前回の線への反応」を書くための台帳。

output/state/last_result.json … 直前の実行の要約（1 件）
output/ledger.csv            … 実行ごとの 1 行（追記専用）。答え合わせの材料
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd


def summary_of(result: dict) -> dict:
    zones = result.get("zones") or {}
    return {
        "symbol": result.get("symbol"),
        "timeframe": result.get("timeframe"),
        "source": result.get("source"),
        "analyzed_at_jst": result["analyzed_at_jst"],
        "last_bar_utc": result.get("last_bar_utc"),
        "slot": result.get("slot"),
        "close": result["close"],
        "trend_label": result["trend"]["label"],
        "trend_effective": result["trend"].get("label_effective", result["trend"]["label"]),
        "dow_state": (result.get("structure") or {}).get("state"),
        "zones_above": [round(z["center"], 3) for z in zones.get("above", [])],
        "zones_below": [round(z["center"], 3) for z in zones.get("below", [])],
        "supports": [round(l["price"], 3) for l in result["supports"]],
        "resistances": [round(l["price"], 3) for l in result["resistances"]],
        "scenario_main": (result.get("scenarios") or {}).get("main_text"),
        "scenarios": _scenario_summary(result.get("scenarios") or {}),
        "post_id": result.get("post_id"),          # X の投稿 ID（投稿プログラムが書く。夜は朝の投稿を引用するのに使う）
    }


def _scenario_summary(sc: dict) -> dict:
    """答え合わせに要る数字だけ：方向ごとの発動価格・行き先・崩れる価格。"""
    def side(s: dict | None) -> dict | None:
        if not s or not s.get("trigger"):
            return None
        return {"trigger": round(float(s["trigger"]["price"]), 3),
                "target": round(float(s["target"]["price"]), 3) if s.get("target") else None,
                "invalid": round(float(s["invalid"]["price"]), 3) if s.get("invalid") else None}
    return {"main": sc.get("main"), "up": side(sc.get("up")), "down": side(sc.get("down"))}


def load_last(state_dir: Path) -> dict | None:
    p = Path(state_dir) / "last_result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def usable(prev: dict | None, *, symbol: str, timeframe: str, source: str | None, last_bar_utc: str,
           index) -> tuple[dict | None, str]:
    """前回結果を使ってよいか。使えないときは (None, 理由)。"""
    if prev is None:
        return None, ""
    if prev.get("symbol") != symbol or prev.get("timeframe") != timeframe:
        return None, "前回の結果は別の銘柄・時間足のため比較していません。"
    if source and prev.get("source") and prev["source"] != source:
        return None, f"前回の結果はデータ源が違う（{prev['source']}）ため比較していません。"
    try:
        pt = pd.Timestamp(prev.get("last_bar_utc"))
        ct = pd.Timestamp(last_bar_utc)
    except Exception:
        return None, "前回の結果の時刻が読めないため比較していません。"
    if pt > ct:
        return None, "前回の結果の方が新しい足に基づくため比較していません。"
    if index is not None and pt not in index:
        return None, "前回の最終足が今回のデータに無いため比較していません。"
    return prev, ""


def save(result: dict, out_dir: Path) -> None:
    state_dir = Path(out_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    s = summary_of(result)
    (state_dir / "last_result.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    p = Path(out_dir) / "ledger.csv"
    header = list(s.keys())
    if p.exists():
        with p.open(encoding="utf-8", newline="") as f:
            first = f.readline().rstrip("\r\n").split(",")
        if first != header:          # 列が変わったら古い台帳を退避して新しく始める
            p.rename(p.with_name(f"ledger_old_{len(list(p.parent.glob('ledger_old_*.csv'))) + 1}.csv"))
    new = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow([json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for v in s.values()])


def changes_since(prev: dict | None, result: dict, df_recent, *, reach_tol: float, pip: float) -> dict:
    """前回との違いと、前回の注目帯に価格が届いたか。df_recent: 前回の最終足より後の足（UTC index）。"""
    out = {"available": prev is not None, "lines": [], "reactions": []}
    if prev is None:
        return out
    if prev.get("last_bar_utc") == result.get("last_bar_utc"):
        out["lines"].append("前回から新しい確定足はありません（同じ足に基づく再計算）。")
    cur_label = result["trend"].get("label_effective", result["trend"]["label"])
    if prev.get("trend_effective") != cur_label:
        out["lines"].append(f"相場環境：「{prev.get('trend_effective')}」→「{cur_label}」に変わりました。")
    cur_dow = (result.get("structure") or {}).get("state")
    if prev.get("dow_state") and cur_dow and prev["dow_state"] != cur_dow:
        out["lines"].append(f"構造：「{prev['dow_state']}」→「{cur_dow}」。")
    move = (result["close"] - float(prev["close"])) / pip
    out["lines"].append(f"前回（{prev['analyzed_at_jst']}）の現在値 {float(prev['close']):.3f} から {move:+.0f} pips。")
    if df_recent is not None and len(df_recent) > 0:
        hi = float(np.max(df_recent["high"].to_numpy()))
        lo = float(np.min(df_recent["low"].to_numpy()))
        last_c = float(df_recent["close"].to_numpy()[-1])
        for p in prev.get("zones_above", []):
            if hi >= p - reach_tol:
                out["reactions"].append(f"上の注目帯 {p:.3f} に到達（高値 {hi:.3f}）→ " + ("終値で上抜け" if last_c > p else "終値は帯の下に戻る（反発）"))
        for p in prev.get("zones_below", []):
            if lo <= p + reach_tol:
                out["reactions"].append(f"下の注目帯 {p:.3f} に到達（安値 {lo:.3f}）→ " + ("終値で割れ" if last_c < p else "終値は帯の上に戻る（反発）"))
        if not out["reactions"] and (prev.get("zones_above") or prev.get("zones_below")):
            out["reactions"].append("前回の注目帯にはまだ届いていません。")
    return out


# ---------------------------------------------------------------- 答え合わせ（2026-10-05・リサーチ 7-2）

def judge_side(side: dict | None, df_recent, *, up: bool, reach_tol: float) -> dict | None:
    """前回のシナリオ 1 方向を、前回より後の確定足で判定する。
    未発動 … 発動価格を終値で抜けていない（崩れもしていない）
    発動   … 発動価格を終値で抜けた（上なら超え、下なら割れ）
    到達   … 発動のあと、行き先に reach_tol 以内まで届いた
    無効化 … 発動する前に崩れる条件を終値で満たした（発動後に崩れた場合は「発動→崩れ」）"""
    if not side or side.get("trigger") is None:
        return None
    trig, tgt, inv = side["trigger"], side.get("target"), side.get("invalid")
    status, detail = "未発動", ""
    if df_recent is None or len(df_recent) == 0:
        return {"status": status, "trigger": trig, "target": tgt, "invalid": inv, "detail": "新しい確定足なし"}
    h = df_recent["high"].to_numpy(dtype=float)
    l = df_recent["low"].to_numpy(dtype=float)
    c = df_recent["close"].to_numpy(dtype=float)
    for i in range(len(c)):
        if status == "未発動":
            if inv is not None and ((up and c[i] < inv) or ((not up) and c[i] > inv)):
                status, detail = "無効化", f"終値 {c[i]:.3f} で崩れる条件 {inv:.3f} を{'割れ' if up else '超え'}"
                break
            if (up and c[i] > trig) or ((not up) and c[i] < trig):
                status, detail = "発動", f"終値 {c[i]:.3f} で {trig:.3f} を{'超え' if up else '割れ'}"
        elif status == "発動":
            if tgt is not None and ((up and h[i] >= tgt - reach_tol) or ((not up) and l[i] <= tgt + reach_tol)):
                status, detail = "到達", f"行き先 {tgt:.3f} に到達（{'高値' if up else '安値'} {(h[i] if up else l[i]):.3f}）"
                break
            if inv is not None and ((up and c[i] < inv) or ((not up) and c[i] > inv)):
                status, detail = "発動→崩れ", f"発動のあと終値 {c[i]:.3f} で崩れる条件 {inv:.3f} を{'割れ' if up else '超え'}"
                break
    if status == "未発動":
        ext = float(np.max(h)) if up else float(np.min(l))
        detail = f"{'高値' if up else '安値'} {ext:.3f} まで（発動価格 {trig:.3f} は終値で{'超えず' if up else '割れず'}）"
    return {"status": status, "trigger": trig, "target": tgt, "invalid": inv, "detail": detail}


def judge_scenarios(prev: dict | None, df_recent, *, reach_tol: float) -> dict | None:
    """前回の朝（または前回）のシナリオを答え合わせする。prev に scenarios が無ければ None。"""
    if not prev or not isinstance(prev.get("scenarios"), dict):
        return None
    sc = prev["scenarios"]
    main = sc.get("main")
    out = {"main": main, "prev_slot": prev.get("slot"), "prev_at": prev.get("analyzed_at_jst"), "prev_post_id": prev.get("post_id"),
           "up": judge_side(sc.get("up"), df_recent, up=True, reach_tol=reach_tol),
           "down": judge_side(sc.get("down"), df_recent, up=False, reach_tol=reach_tol)}
    if main in ("up", "down"):
        out["main_side"] = out[main]
        out["sub_side"] = out["down" if main == "up" else "up"]
    else:
        out["main_side"] = out["sub_side"] = None
    return out

