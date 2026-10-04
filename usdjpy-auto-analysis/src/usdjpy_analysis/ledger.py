"""前回の結果を残し、次回に「変化点」と「前回の線への反応」を書くための台帳。

output/state/last_result.json … 直前の実行の要約（1 件）
output/ledger.csv            … 実行ごとの 1 行（追記専用）。答え合わせの材料
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def summary_of(result: dict) -> dict:
    zones = result.get("zones") or {}
    return {
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
    }


def load_last(state_dir: Path) -> dict | None:
    p = Path(state_dir) / "last_result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(result: dict, out_dir: Path) -> None:
    state_dir = Path(out_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    s = summary_of(result)
    (state_dir / "last_result.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    p = Path(out_dir) / "ledger.csv"
    new = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(list(s.keys()))
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
