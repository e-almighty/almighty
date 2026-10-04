"""第2ステージ（確定足・ダウ理論・フィボ・ダイバージェンス・注目価格帯・安全弁）のテスト。
  python -m pytest tests  または  python tests/test_stage2.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from make_sample import make_sample  # noqa: E402
from usdjpy_analysis import bars, divergence, fibonacci, market_data, pipeline, safety, structure, zones  # noqa: E402
from usdjpy_analysis.swings import Swing  # noqa: E402

CFG = HERE.parent / "config" / "analysis.yaml"
JST = ZoneInfo("Asia/Tokyo")
DATA_4H = HERE.parent / "data" / "USDJPY_4H.csv"
DATA_1D = HERE.parent / "data" / "USDJPY_1D.csv"


# ---------------------------------------------------------------- 確定足

def test_confirmed_drops_in_progress_bar():
    df = make_sample(50, start="2026-09-28")                 # 4h 足、UTC
    last_start = df.index[-1]
    now = (last_start + pd.Timedelta(hours=2)).to_pydatetime()  # 最後の足はまだ進行中
    done, pending, info = bars.confirmed(df, now)
    assert len(done) == 49 and len(pending) == 1
    assert info.bar_seconds == 4 * 3600 and info.dropped_in_progress
    now2 = (last_start + pd.Timedelta(hours=4)).to_pydatetime()  # ちょうど終了時刻 → 確定
    done2, pending2, info2 = bars.confirmed(df, now2)
    assert len(done2) == 50 and not info2.dropped_in_progress


def test_daily_levels_prev_day_and_week():
    # 日足：月〜金の 10 本（NY クローズ区切り = UTC 21:00 始まり）
    idx = pd.to_datetime([
        "2026-09-20 21:00", "2026-09-21 21:00", "2026-09-22 21:00", "2026-09-23 21:00", "2026-09-24 21:00",   # 9/21(月)〜9/25(金) の足
        "2026-09-27 21:00", "2026-09-28 21:00", "2026-09-29 21:00", "2026-09-30 21:00", "2026-10-01 21:00",   # 9/28(月)〜10/2(金)
    ], utc=True)
    base = np.arange(10, dtype=float)
    df = pd.DataFrame({"open": 150 + base, "high": 151 + base, "low": 149 + base, "close": 150.5 + base, "volume": 0.0}, index=idx)
    now = datetime(2026, 10, 4, 10, 5, tzinfo=JST)              # 日曜の朝
    dl = bars.daily_levels(df, now, "Asia/Tokyo", ema_period=5)
    assert dl.prev_day["label"] == "10/02" and dl.prev_day["high"] == 160.0
    assert dl.prev_week["label"] == "09/28〜10/02" and dl.prev_week["high"] == 160.0 and dl.prev_week["low"] == 154.0
    assert dl.this_week is None and dl.today is None
    now_fri = datetime(2026, 10, 2, 10, 5, tzinfo=JST)          # 金曜の朝：10/2 の足は進行中
    dl2 = bars.daily_levels(df, now_fri, "Asia/Tokyo", ema_period=5)
    assert dl2.prev_day["label"] == "10/01" and dl2.today["label"] == "10/02"
    assert dl2.prev_week["label"] == "09/21〜09/25" and dl2.this_week is not None


# ---------------------------------------------------------------- 主要スイングとダウ理論

def _sw(items):
    return [Swing(i, p, k) for i, p, k in items]


def test_major_swings_filters_small_waves():
    zz = _sw([(0, 100.0, "low"), (10, 110.0, "high"), (15, 109.5, "low"), (20, 110.2, "high"), (30, 100.5, "low"), (40, 112.0, "high")])
    maj = structure.major_swings(zz, atr_now=1.0, min_atr=2.0)
    assert [(s.index, s.kind) for s in maj] == [(0, "low"), (20, "high"), (30, "low"), (40, "high")]


def test_dow_state_uptrend_and_close_break():
    # 安値 100 → 高値 110 → 安値 105 → 高値 115（HH/HL：上昇、押し安値 105）
    maj = _sw([(0, 100.0, "low"), (10, 110.0, "high"), (20, 105.0, "low"), (30, 115.0, "high")])
    close = np.full(45, 112.0)
    st = structure.dow_state(maj, close, atr_now=1.0, break_atr=0.1)
    assert st.direction == "up" and st.key_level == 105.0 and "高値更新待ち" in st.state
    close2 = close.copy(); close2[40:] = 104.0                  # 終値で押し安値割れ → 下降に転換
    st2 = structure.dow_state(maj, close2, atr_now=1.0, break_atr=0.1)
    assert st2.direction == "down" and st2.key_level == 115.0 and st2.flipped_index == 40
    close3 = close.copy(); close3[40:] = 116.0                  # 高値更新中
    st3 = structure.dow_state(maj, close3, atr_now=1.0, break_atr=0.1)
    assert "高値更新中" in st3.state


def test_dow_state_wick_break_kept_on_close_basis():
    maj = _sw([(0, 100.0, "low"), (10, 110.0, "high"), (20, 105.0, "low"), (30, 115.0, "high"), (40, 104.5, "low")])
    close = np.full(50, 112.0)                                   # ヒゲは 104.5 まで割ったが終値は維持
    st = structure.dow_state(maj, close, atr_now=1.0, break_atr=0.1, basis="close")
    assert st.direction == "up" and st.key_level == 105.0 and st.wick_breaks == [104.5]
    st_w = structure.dow_state(maj, close, atr_now=1.0, break_atr=0.1, basis="wick")
    assert st_w.direction == "down" and st_w.key_level == 115.0


def test_alternate_outside_bar_order_and_dow_handles_both():
    from usdjpy_analysis import swings
    highs = _sw([(5, 110.0, "high"), (20, 112.0, "high")])
    lows = _sw([(5, 100.0, "low"), (12, 105.0, "low")])
    o = np.full(30, 101.0); c = np.full(30, 109.0)              # 足 5 は陽線 → 安値 → 高値
    zz = swings.alternate(highs, lows, o, c)
    assert [(s.index, s.kind) for s in zz] == [(5, "low"), (5, "high"), (12, "low"), (20, "high")]
    c2 = c.copy(); c2[5] = 100.5                                 # 足 5 を陰線にすると 高値 → 安値（次の安値 105 は同種なので極値 100 が残る）
    zz2 = swings.alternate(highs, lows, o, c2)
    assert [(s.index, s.kind) for s in zz2] == [(5, "high"), (5, "low"), (20, "high")]
    st = structure.dow_state(zz, np.full(30, 111.0), atr_now=1.0, break_atr=0.1)
    assert st.direction == "up" and st.key_level == 105.0        # 同じ足の高安を両方処理できる


# ---------------------------------------------------------------- フィボナッチ

def test_fibonacci_up_wave_levels():
    maj = _sw([(0, 100.0, "low"), (10, 110.0, "high"), (20, 104.0, "low"), (30, 114.0, "high")])
    high = np.full(40, 112.0); low = np.full(40, 110.0); low[35] = 108.0     # 終点の後の押しの極値＝108
    kw = dict(levels=[0.382, 0.5, 0.618], extensions=[1.0, 1.618], min_wave_atr=3.0, direction="up", high=high, low=low)
    fib = fibonacci.compute(maj, close_now=110.18, atr_now=1.0, wave="last_impulse", **kw)
    assert fib.wave == "last_impulse" and fib.start_price == 104.0 and fib.end_price == 114.0
    assert abs(fib.levels[0.5] - 109.0) < 1e-9 and abs(fib.levels[0.382] - 110.18) < 1e-9
    assert abs(fib.extensions[1.0] - 118.0) < 1e-9 and abs(fib.extensions[1.618] - (108.0 + 16.18)) < 1e-9
    assert fib.ext_base_price == 108.0 and abs(fib.current_ratio - 0.382) < 1e-6
    # 構造の波（押し安値 → 更新対象の高値）
    fib2 = fibonacci.compute(maj, close_now=110.18, atr_now=1.0, wave="structure", key_point=(0, 100.0), top_point=(30, 114.0), **kw)
    assert fib2.wave == "structure" and fib2.start_price == 100.0 and abs(fib2.levels[0.5] - 107.0) < 1e-9
    small = fibonacci.compute(maj, 110.0, atr_now=5.0, levels=[0.5], extensions=[], min_wave_atr=3.0, direction="up", high=high, low=low)
    assert small is None                                         # 波が ATR×3 未満なら引かない


# ---------------------------------------------------------------- ダイバージェンス

def test_divergence_regular_bearish_and_hidden_bullish():
    n = 60
    rsi = np.full(n, 50.0)
    highs = _sw([(20, 110.0, "high"), (50, 112.0, "high")])
    rsi[20], rsi[50] = 75.0, 70.0                                 # 価格は高値更新、RSI は切り下げ → 弱気（通常）
    lows = _sw([(10, 100.0, "low"), (45, 103.0, "low")])
    rsi[10], rsi[45] = 40.0, 30.0                                 # 安値切り上げ、RSI 切り下げ → 強気（隠れ）
    out = divergence.detect(highs, lows, rsi, n, atr_now=1.0, min_price_atr=0.3, min_rsi_diff=3.0, max_age_bars=20, hidden=True)
    kinds = {d.kind for d in out}
    assert kinds == {"bearish", "hidden_bullish"}
    out2 = divergence.detect(highs, lows, rsi, n, atr_now=1.0, min_price_atr=0.3, min_rsi_diff=3.0, max_age_bars=5, hidden=True)
    assert out2 == []                                            # 古すぎるピボットは使わない


# ---------------------------------------------------------------- 注目価格帯

def test_zones_merge_and_rank():
    c = [zones.Candidate(158.0, "レジスタンス", "r", 2.0), zones.Candidate(158.05, "フィボナッチ", "f", 1.5),
         zones.Candidate(159.5, "節目", "n", 0.5), zones.Candidate(157.4, "EMA50", "e", 1.0), zones.Candidate(157.45, "EMA200", "e2", 1.5),
         zones.Candidate(156.0, "サポート", "s", 2.0)]
    above, below = zones.build(c, close_now=157.8, atr_now=0.5, merge_atr=0.4, max_each_side=2, pip=0.01)
    assert [z.kinds() for z in above][0] == ["レジスタンス", "フィボナッチ"] and above[0].score == 3.5
    assert below[0].kinds() == ["EMA50", "EMA200"] and below[1].kinds() == ["サポート"]
    assert zones.distance_text(0.2) == "目前" and zones.distance_text(10) == "中期の目安"


# ---------------------------------------------------------------- 安全弁

def test_safety_replaces_banned_words():
    text, hits = safety.sanitize("ここは必ず反発するので買いです。エントリー推奨。")
    assert "必ず" not in text and "買いです" not in text and "推奨" not in text
    assert "必ず" in hits and "推奨" in hits


# ---------------------------------------------------------------- 通し（架空データと本物の CSV）

def test_end_to_end_sample_morning_and_evening(tmp_path):
    df = make_sample(400, seed=3)
    cfg = pipeline.load_config(CFG)
    now = (df.index[-1] + pd.Timedelta(hours=4)).to_pydatetime().astimezone(JST)
    res = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="morning")
    assert Path(res["files"]["png"]).exists() and res["slot"] == "morning"
    assert res["structure"]["direction"] in {"up", "down", "none"}
    assert res["zones"]["above"] or res["zones"]["below"]
    assert res["commentary"]["x_units"] <= cfg["posting"]["x_max_units"]
    assert "必ず" not in res["commentary"]["long"]
    # 2 回目（中間報告）は台帳から前回を読んで「変化点」を書く
    res2 = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="evening")
    assert res2["changes"]["available"] and "前回" in res2["commentary"]["long"]
    assert (tmp_path / "ledger.csv").exists() and (tmp_path / "state" / "last_result.json").exists()


def test_real_csv_snapshot_2026_10_03(tmp_path):
    """本物の CSV（2026-10-03 金曜クローズまで）での主要な数値を固定する（回帰テスト）。"""
    if not DATA_4H.exists():
        return
    cfg = pipeline.load_config(CFG)
    df = market_data.load_csv(DATA_4H)
    dfd = market_data.load_csv(DATA_1D) if DATA_1D.exists() else None
    res = pipeline.analyze(df, cfg, "4h", dfd, now=datetime(2026, 10, 4, 10, 5, tzinfo=JST), slot="morning")
    assert abs(res["close"] - 157.874) < 1e-6
    assert res["confirmed"]["last_end_jst"] == "10/03 06:00" and not res["confirmed"]["dropped_in_progress"]
    assert res["structure"]["direction"] == "up" and abs(res["structure"]["key_level"] - 156.822) < 1e-6
    assert abs(res["structure"]["top_price"] - 159.037) < 1e-6
    assert [round(l["price"], 3) for l in res["supports"]] == [156.587, 155.259, 153.240]
    assert [round(l["price"], 3) for l in res["resistances"]] == [157.957, 159.037, 160.299]
    assert res["fibonacci"] is None                               # 既定 OFF（SHO 2026-10-04）
    assert "フィボ" not in res["commentary"]["long"]
    assert not res["divergences"] or all(d["i1"] != d["i2"] for d in res["divergences"])
    # ON にすると：主波＝画像の範囲で最も大きな波（09/08 安値 152.888 → 09/24 高値 159.037）、目標＝直近波の 3 点方式
    cfg2 = pipeline.load_config(CFG); cfg2["fibonacci"]["enabled"] = True
    res2 = pipeline.analyze(df, cfg2, "4h", dfd, now=datetime(2026, 10, 4, 10, 5, tzinfo=JST), slot="morning")
    f = res2["fibonacci"]
    assert f["wave"] == "chart_major" and abs(f["start_price"] - 152.888) < 1e-6 and abs(f["end_price"] - 159.037) < 1e-6
    assert abs(f["levels"]["0.382"] - (159.037 - 6.149 * 0.382)) < 1e-3
    t = res2["fibonacci_target"]
    assert t and abs(t["start_price"] - 156.375) < 1e-6 and abs(t["end_price"] - 158.457) < 1e-6
    assert abs(t["extensions"]["1.0"] - (156.951 + (158.457 - 156.375))) < 1e-3            # N 計算値＝押しの極値＋波幅
    assert "フィボナッチ" in res2["commentary"]["long"]
    assert res["daily"]["prev_day"]["label"] == "10/02" and abs(res["daily"]["prev_day"]["high"] - 158.220) < 1e-6
    assert res["daily"]["prev_week"]["label"] == "09/28〜10/02"
    assert res["higher_timeframe"]["close"] == 157.874          # iloc[-2] のずれが直っていること
    assert res["trend"]["label"] == "強い上昇" and res["trend"]["caveat"] == ""


if __name__ == "__main__":
    import tempfile
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            if fn.__code__.co_argcount:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print("ok", name)
    print("all stage2 tests passed")
