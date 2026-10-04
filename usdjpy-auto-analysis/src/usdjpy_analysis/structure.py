"""主要スイングの選別と、ダウ理論の構造判定（押し安値・戻り高値）。

主要スイング：交互スイング（ZigZag 風）のうち、直前の反対側スイングからの振幅が ATR × major_swing_atr 以上のものだけ。
  左右 5 本のピボットは小さな波も拾うので、ダウ理論・フィボ・相場環境の「高安の切り上げ・切り下げ」は主要スイングを参照する。

ダウ理論（状態機械・足を古い順にたどる）:
  上昇：高値を更新したとき、その高値の直前の主要安値 ＝ 押し安値。終値で押し安値を割らない限り上昇の構造は保たれる。
        終値で押し安値を ATR × break_atr 以上割った足で「下降」に転換し、直前の主要高値が戻り高値になる。
  下降：上下を逆にして同じ（戻り高値）。
  basis="close"（既定）は終値で判定。basis="wick" はヒゲ（主要安値そのもの）で判定する。
  状態：上昇継続（高値更新中）／上昇（高値更新待ち・調整中）／下降継続（安値更新中）／下降（安値更新待ち・戻り中）／方向感なし
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .swings import Swing


def major_swings(zz: list[Swing], atr_now: float, min_atr: float) -> list[Swing]:
    """交互スイングから振幅の小さい波を取り除く。結果も交互（高→安→高…）になる。"""
    if not zz:
        return []
    th = atr_now * min_atr
    out: list[Swing] = [zz[0]]
    for s in zz[1:]:
        last = out[-1]
        if s.kind == last.kind:
            better = (s.kind == "high" and s.price > last.price) or (s.kind == "low" and s.price < last.price)
            if better:
                out[-1] = s
            continue
        if abs(s.price - last.price) >= th:
            out.append(s)
    return out


@dataclass
class DowState:
    direction: str            # "up" | "down" | "none"
    state: str                # 日本語の状態名
    key_level: float | None   # 押し安値（上昇）または戻り高値（下降）
    key_time_index: int | None
    last_high: float | None   # 直近の主要高値
    last_low: float | None    # 直近の主要安値
    note: str                 # 高安の推移（文章用）
    top_price: float | None = None     # 上昇なら更新対象の高値、下降なら更新対象の安値
    top_index: int | None = None
    flipped_index: int | None = None   # 最後に構造が転換した足（終値ブレイク）
    flipped_note: str = ""
    wick_breaks: list[float] = field(default_factory=list)  # ヒゲでは割った（越えた）が終値では維持した主要安値（高値）
    basis: str = "close"


def dow_state(major: list[Swing], close: np.ndarray, atr_now: float, break_atr: float = 0.1,
              basis: str = "close") -> DowState:
    n = len(close)
    tol = atr_now * break_atr
    at: dict[int, list[Swing]] = {}
    for s in major:                       # 同じ足に高値と安値があれば、major の並び順（足の向き）で両方処理する
        at.setdefault(s.index, []).append(s)
    highs_seen: list[Swing] = []
    lows_seen: list[Swing] = []
    state = "none"
    key: Swing | None = None
    top: Swing | None = None
    flipped_index = None
    flipped_note = ""
    wick_breaks: list[float] = []

    def last_opposite(kind: str) -> Swing | None:
        pool = lows_seen if kind == "high" else highs_seen
        return pool[-1] if pool else None

    for i in range(n):
        for s in at.get(i, []):
            if s.kind == "high":
                prev = highs_seen[-1] if highs_seen else None
                if state == "up":
                    if top is not None and s.price > top.price:
                        top = s
                        key = last_opposite("high") or key      # 押し安値を更新
                elif state == "down":
                    if key is not None and s.price > key.price:
                        if basis == "wick" and s.price > key.price + tol:
                            old_key = key
                            state, top, key = "up", s, last_opposite("high")
                            flipped_index, flipped_note = i, f"戻り高値 {old_key.price:.3f} を高値で上抜け、上昇の構造に転換"
                            wick_breaks = []
                        elif basis == "close":
                            wick_breaks.append(s.price)
                elif state == "none":
                    if prev is not None and s.price > prev.price and len(lows_seen) >= 2 and lows_seen[-1].price > lows_seen[-2].price:
                        state, top, key = "up", s, lows_seen[-1]
                highs_seen.append(s)
            else:
                prev = lows_seen[-1] if lows_seen else None
                if state == "down":
                    if top is not None and s.price < top.price:
                        top = s
                        key = last_opposite("low") or key       # 戻り高値を更新
                elif state == "up":
                    if key is not None and s.price < key.price:
                        if basis == "wick" and s.price < key.price - tol:
                            old_key = key
                            state, top, key = "down", s, last_opposite("low")
                            flipped_index, flipped_note = i, f"押し安値 {old_key.price:.3f} を安値で割り込み、下降の構造に転換"
                            wick_breaks = []
                        elif basis == "close":
                            wick_breaks.append(s.price)
                elif state == "none":
                    if prev is not None and s.price < prev.price and len(highs_seen) >= 2 and highs_seen[-1].price < highs_seen[-2].price:
                        state, top, key = "down", s, highs_seen[-1]
                lows_seen.append(s)
        # 終値によるブレイク（basis=close）。その足のスイングを処理してから判定する
        if basis == "close" and key is not None:
            c = float(close[i])
            if state == "up" and c < key.price - tol:
                old = key
                state = "down"
                top = lows_seen[-1] if lows_seen else None
                key = highs_seen[-1] if highs_seen else None
                flipped_index, flipped_note = i, f"押し安値 {old.price:.3f} を終値で割り込み、下降の構造に転換"
                wick_breaks = []
            elif state == "down" and c > key.price + tol:
                old = key
                state = "up"
                top = highs_seen[-1] if highs_seen else None
                key = lows_seen[-1] if lows_seen else None
                flipped_index, flipped_note = i, f"戻り高値 {old.price:.3f} を終値で上抜け、上昇の構造に転換"
                wick_breaks = []

    lh = highs_seen[-1].price if highs_seen else None
    ll = lows_seen[-1].price if lows_seen else None
    c = float(close[-1])
    if state == "none" or key is None:
        if len(highs_seen) >= 2 and len(lows_seen) >= 2:
            hh = highs_seen[-1].price > highs_seen[-2].price
            hl = lows_seen[-1].price > lows_seen[-2].price
            kind = "拡大（高値切り上げ・安値切り下げ）" if (hh and not hl) else ("収れん（高値切り下げ・安値切り上げ）" if (hl and not hh) else "判定できず")
            note = f"高値 {highs_seen[-2].price:.3f}→{highs_seen[-1].price:.3f}、安値 {lows_seen[-2].price:.3f}→{lows_seen[-1].price:.3f}"
            return DowState("none", f"方向感なし・{kind}", None, None, lh, ll, note, basis=basis)
        return DowState("none", "主要スイングが少なく判定できず", None, None, lh, ll, "", basis=basis)

    if state == "up":
        if c > top.price:
            st = "上昇継続（高値更新中）"
        else:
            st = "上昇（高値更新待ち・調整中）"
        note = f"更新対象の高値は {top.price:.3f}、押し安値は {key.price:.3f}"
        if wick_breaks:
            note += f"。ヒゲでは押し安値を割る場面（{min(wick_breaks):.3f}）がありましたが、終値では維持"
        return DowState("up", st, key.price, key.index, lh, ll, note, top.price, top.index, flipped_index, flipped_note, wick_breaks, basis)
    if c < top.price:
        st = "下降継続（安値更新中）"
    else:
        st = "下降（安値更新待ち・戻り中）"
    note = f"更新対象の安値は {top.price:.3f}、戻り高値は {key.price:.3f}"
    if wick_breaks:
        note += f"。ヒゲでは戻り高値を越える場面（{max(wick_breaks):.3f}）がありましたが、終値では維持"
    return DowState("down", st, key.price, key.index, lh, ll, note, top.price, top.index, flipped_index, flipped_note, wick_breaks, basis)


def structure_score(dow: DowState) -> tuple[int, str]:
    """相場環境の項目 4（高安の切り上げ・切り下げ）をダウ理論の構造から決める。"""
    if dow.direction == "up":
        return 1, "主要な高値・安値は切り上げ（上昇の構造）"
    if dow.direction == "down":
        return -1, "主要な高値・安値は切り下げ（下降の構造）"
    return 0, dow.state.replace("方向感なし・", "主要な高安は")
