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
    assert dl.prev_day["label"] == "10/02 金" and dl.prev_day["high"] == 160.0
    assert dl.prev_week["label"] == "09/28〜10/02" and dl.prev_week["high"] == 160.0 and dl.prev_week["low"] == 154.0
    assert dl.this_week is None and dl.today is None
    now_fri = datetime(2026, 10, 2, 10, 5, tzinfo=JST)          # 金曜の朝：10/2 の足は進行中
    dl2 = bars.daily_levels(df, now_fri, "Asia/Tokyo", ema_period=5)
    assert dl2.prev_day["label"] == "10/01 木" and dl2.today["label"] == "10/02 金"
    assert dl2.prev_week["label"] == "09/21〜09/25" and dl2.this_week is not None
    assert dl2.this_week["high"] == 159.0                       # 確定分だけ。本日分は pipeline が 4時間足から足す
    bars.merge_today_into_week(dl2)
    assert dl2.this_week["high"] == 160.0 and dl2.this_week["close"] == dl2.today["close"]
    # --now を過去にしたとき：CSV に未来の足があっても「本日」は now 時点の進行中の足だけ
    now_wed = datetime(2026, 9, 30, 20, 5, tzinfo=JST)
    dl3 = bars.daily_levels(df, now_wed, "Asia/Tokyo", ema_period=5)
    assert dl3.prev_day["label"] == "09/29 火" and dl3.today["label"] == "09/30 水"
    # 土曜の早朝（金曜の足がまだ進行中）：今週を「前週」と呼ばない
    now_sat = datetime(2026, 10, 3, 3, 0, tzinfo=JST)
    dl4 = bars.daily_levels(df, now_sat, "Asia/Tokyo", ema_period=5)
    assert dl4.today["label"] == "10/02 金" and dl4.prev_week["label"] == "09/21〜09/25"
    # tz なしの now は設定のタイムゾーン（JST）として扱う
    done, pending, _ = bars.confirmed(df, datetime(2026, 10, 2, 10, 5))
    assert len(pending) == 1


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
    assert below[0].kinds() == ["EMA200", "EMA50"] and below[1].kinds() == ["サポート"]   # 種類は重み順
    assert zones.distance_text(0.2) == "目前" and zones.distance_text(10) == "中期の目安" and zones.distance_text(3) == "1〜2 日の射程"
    # 帯の幅は tol 以内（連鎖で広がらない）、同じ種類の 2 本目は得点に足さない、現在値をまたぐ帯は上下に分ける
    c2 = [zones.Candidate(100.00 + 0.19 * i, "節目", f"n{i}", 0.5) for i in range(6)]      # 0.19 刻み（tol=0.2）
    c2 += [zones.Candidate(101.0, "フィボナッチ", "a", 1.5), zones.Candidate(101.05, "フィボナッチ", "b", 1.5)]
    above2, below2 = zones.build(c2, close_now=100.5, atr_now=0.5, merge_atr=0.4, max_each_side=5, pip=0.01)
    for z in above2 + below2:
        assert z.high - z.low <= 0.2 + 1e-9
        assert all(m.price > 100.5 for m in z.members) or all(m.price <= 100.5 for m in z.members)
    fibz = [z for z in above2 if "フィボナッチ" in z.kinds()][0]
    assert fibz.score == 1.5 and len(fibz.members) == 2


# ---------------------------------------------------------------- 安全弁

def test_safety_replaces_banned_words():
    text, hits = safety.sanitize("ここは必ず反発するので買いです。エントリー推奨。")
    assert "必ず" not in text and "買いです" not in text and "推奨" not in text
    assert "必ず" in hits and "推奨" in hits
    # 文法を壊さない／誤検出しない
    t2, h2 = safety.sanitize("必ずしも反発するとは限らず、不確実性が高い。非推奨の形。上抜けるべきではない。")
    assert t2.startswith("必ずしも") and "不確実" in t2 and "非推奨" in t2 and "上抜けるのは一案ではない" in t2
    assert h2 == ["べき"]


def test_ledger_usable_rejects_mismatch(tmp_path):
    from usdjpy_analysis import ledger
    idx = pd.date_range("2026-10-01", periods=5, freq="4h", tz="UTC")
    prev = {"symbol": "USDJPY", "timeframe": "4h", "source": "csv", "last_bar_utc": idx[2].isoformat()}
    ok, _ = ledger.usable(prev, symbol="USDJPY", timeframe="4h", source="csv", last_bar_utc=idx[4].isoformat(), index=idx)
    assert ok is prev
    bad, why = ledger.usable({**prev, "source": "sample"}, symbol="USDJPY", timeframe="4h", source="csv", last_bar_utc=idx[4].isoformat(), index=idx)
    assert bad is None and "データ源" in why
    bad2, why2 = ledger.usable(prev, symbol="USDJPY", timeframe="4h", source="csv", last_bar_utc=idx[1].isoformat(), index=idx)
    assert bad2 is None and "新しい" in why2


# ---------------------------------------------------------------- 通し（架空データと本物の CSV）

def test_end_to_end_sample_morning_and_evening(tmp_path):
    df = make_sample(400, seed=3)
    cfg = pipeline.load_config(CFG)
    now = (df.index[-1] + pd.Timedelta(hours=4)).to_pydatetime().astimezone(JST)
    res = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="morning", source="csv")
    assert Path(res["files"]["png"]).exists() and res["slot"] == "morning"
    assert res["structure"]["direction"] in {"up", "down", "none"}
    assert res["zones"]["above"] or res["zones"]["below"]
    assert res["commentary"]["x_units"] <= cfg["posting"]["x_max_units"]
    assert "必ず" not in res["commentary"]["long"]
    # 2 回目（中間報告）は台帳から前回を読んで「変化点」を書く
    res2 = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="evening", source="csv")
    assert res2["changes"]["available"] and "前回" in res2["commentary"]["long"]
    assert (tmp_path / "ledger.csv").exists() and (tmp_path / "state" / "last_result.json").exists()
    assert not res2["commentary"]["post_over_limit"]
    # 架空データ（source="sample"）は台帳に残さない。別のデータ源の前回は比較に使わない
    pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="evening", source="sample")
    res3 = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"), now=now, slot="evening", source="gmo")
    assert not res3["changes"]["available"] and "データ源" in res3["changes"]["lines"][0]


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
    assert res["daily"]["prev_day"]["label"] == "10/02 金" and abs(res["daily"]["prev_day"]["high"] - 158.220) < 1e-6
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


def test_post_long_and_short_styles_and_priority_trim():
    from usdjpy_analysis import commentary
    # 優先度つきの切り詰め：優先度 0 の行は残り、数字の大きい行から落ちる
    items = [(0, "頭"), (6, "値幅"), (1, "線"), (0, "免責"), (0, "#tag")]
    out = commentary._fit_post_priority(items, max_units=14)
    assert "値幅" not in out and "頭" in out and "免責" in out and "#tag" in out
    # ハッシュタグはリストでも文字列でもよい
    assert commentary._hashtag_line({"hashtags": ["#a", "#b"]}) == "#a #b"
    assert commentary._hashtag_line({"hashtags": "#a #b"}) == "#a #b"
    # 実データで long／short の両方が上限内に収まり、long には各見出しとハッシュタグ 10 個が入る
    df = market_data.load_csv(DATA_4H)
    dfd = market_data.load_csv(DATA_1D)
    cfg = pipeline.load_config(CFG)
    now = datetime(2026, 10, 4, 10, 5, tzinfo=JST)
    res = pipeline.analyze(df, cfg, "4h", dfd, now=now, slot="morning", source="csv")
    long_post = commentary.build(res, dict(cfg["posting"], post_style="long"))
    short_post = commentary.build(res, dict(cfg["posting"], post_style="short", x_max_units=280))
    assert not long_post["post_over_limit"] and not short_post["post_over_limit"]
    assert short_post["x_units"] <= 280 < long_post["x_units"]
    for head in ("▼相場環境", "▼構造（ダウ理論）", "▼注目価格帯", "▼シナリオ", "※テクニカル分析の参考情報"):
        assert head in long_post["post"]
    assert long_post["post"].rstrip().splitlines()[-1].count("#") == len(cfg["posting"]["hashtags"])
    # thread：本体＋返信 2 投。本体に分かれ目・シナリオ・根拠、返信に環境と線
    th = commentary.build(res, dict(cfg["posting"], post_style="thread"))
    assert len(th["post_replies"]) == 2 and all(u <= cfg["posting"]["reply_max_units"] for u in th["reply_units"])
    assert "▼シナリオ" in th["post"] and "▼判断の根拠" in th["post"] and "▼相場環境" in th["post_replies"][0] and "▼サポート" in th["post_replies"][1]
    assert th["post"].splitlines()[0].endswith("が分かれ目")


def test_answer_check_judge_and_evening_post(tmp_path):
    from usdjpy_analysis import ledger, commentary
    idx = pd.date_range("2026-10-01 01:00", periods=4, freq="4h", tz="UTC")
    def bars(closes, highs, lows):
        return pd.DataFrame({"open": closes, "high": highs, "low": lows, "close": closes, "volume": 0.0}, index=idx)
    side = {"trigger": 158.0, "target": 159.0, "invalid": 156.8}
    # 未発動：終値が 158.0 を超えない
    r = ledger.judge_side(side, bars([157.5, 157.9, 157.8, 157.7], [157.9, 158.05, 157.9, 157.8], [157.3, 157.6, 157.5, 157.4]), up=True, reach_tol=0.15)
    assert r["status"] == "未発動" and "超えず" in r["detail"]
    # 発動 → 到達
    r = ledger.judge_side(side, bars([157.5, 158.2, 158.6, 158.7], [157.9, 158.3, 158.9, 158.8], [157.3, 157.9, 158.2, 158.4]), up=True, reach_tol=0.15)
    assert r["status"] == "到達"
    # 発動する前に崩れ
    r = ledger.judge_side(side, bars([157.5, 156.7, 157.0, 158.2], [157.9, 157.2, 157.3, 158.3], [157.3, 156.5, 156.8, 157.9]), up=True, reach_tol=0.15)
    assert r["status"] == "無効化"
    # 下方向：割れ → 到達
    dn = {"trigger": 157.5, "target": 156.9, "invalid": 158.0}
    r = ledger.judge_side(dn, bars([157.6, 157.4, 157.1, 157.0], [157.8, 157.6, 157.3, 157.2], [157.4, 157.2, 156.95, 156.9]), up=False, reach_tol=0.1)
    assert r["status"] == "到達"
    # 通し：金曜 10:05 の朝 → 同日 20:05 の夜。夜の投稿に ✅ 答え合わせ、1 行目に「朝の …」
    if not DATA_4H.exists():
        return
    cfg = pipeline.load_config(CFG)
    df = market_data.load_csv(DATA_4H); dfd = market_data.load_csv(DATA_1D)
    m = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=datetime(2026, 10, 2, 10, 5, tzinfo=JST), slot="morning", source="csv")
    prev = ledger.load_last(tmp_path / "state")
    assert prev and prev["scenarios"]["up"]["trigger"] and prev["slot"] == "morning"
    e = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=datetime(2026, 10, 2, 20, 5, tzinfo=JST), slot="evening", source="csv")
    v = e["changes"]["verdict"]
    assert v and v["up"]["status"] in {"未発動", "発動", "到達", "無効化", "発動→崩れ"}
    post = e["commentary"]["post"]
    assert "✅ 朝のプランの答え合わせ" in post and post.splitlines()[0].startswith("【今日のドル円】10/02(金) 夜の中間報告｜朝の ")
    assert "■ 朝のプランの答え合わせ" in e["commentary"]["long"]
    # 翌朝：昨夜のプランを 1 行
    nm = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=datetime(2026, 10, 3, 10, 5, tzinfo=JST), slot="morning", source="csv")
    assert "✅ 昨夜のプラン：" in nm["commentary"]["post"]


def test_x_publisher_plan_dry_run(tmp_path):
    """送信予定（DRY RUN）：本体＋返信 2 投、画像と ALT、夜は朝の疑似投稿 ID を引用。X には送らない。"""
    if not DATA_4H.exists():
        return
    sys.path.insert(0, str(HERE.parent))
    from social import x_publisher
    cfg = pipeline.load_config(CFG)
    scfg = x_publisher.load_social_config(HERE.parent / "config" / "social.yaml")
    assert scfg.get("dry_run") is True
    df = market_data.load_csv(DATA_4H); dfd = market_data.load_csv(DATA_1D)
    m = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=datetime(2026, 10, 2, 10, 5, tzinfo=JST), slot="morning", source="csv")
    plan = x_publisher.write_plan(m, dict(scfg, outbox_dir="outbox"), tmp_path, cfg["posting"])
    assert plan["dry_run"] and len(plan["posts"]) == 3 and plan["posts"][1]["in_reply_to"] == "seq:1" and plan["posts"][2]["in_reply_to"] == "seq:2"
    assert plan["posts"][0]["media"] and "ドル円" not in plan["posts"][0]["media"][0]["alt"] or "USDJPY" in plan["posts"][0]["media"][0]["alt"]
    # 朝は 4時間足＋日足の 2 枚（それぞれ ALT つき）。夜は日足を作らないので 1 枚
    assert len(plan["posts"][0]["media"]) == 2 and Path(plan["posts"][0]["media"][1]["path"]).name.endswith("_daily.png")
    assert "日足" in plan["posts"][0]["media"][1]["alt"] and "前週高値" in plan["posts"][0]["media"][1]["alt"]
    assert Path(plan["files"]["md"]).exists() and Path(plan["files"]["json"]).exists()
    pid = x_publisher.mark_posted_dry_run(tmp_path / "state", plan)
    assert pid and pid.startswith("dryrun-")
    e = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=datetime(2026, 10, 2, 20, 5, tzinfo=JST), slot="evening", source="csv")
    plan2 = x_publisher.build_plan(e, scfg, cfg["posting"])
    assert plan2["quote_morning"]["post_id"] == pid and plan2["posts"][0]["quote_of"] == pid
    assert plan2["scheduled_at_jst"] == "2026-10-02 20:05"
    assert len(plan2["posts"][0]["media"]) == 1 and "png_daily" not in e["files"]


def test_image_finish_title_band_and_daily(tmp_path):
    """画像の仕上げ（2026-10-07）：タイトル帯＝投稿の 1 行目、🔑 結論、日足の 2 枚目、夜は朝のプランの帯。設定で全部 OFF にもできる。"""
    from usdjpy_analysis import chart
    cfg = pipeline.load_config(CFG)
    df = make_sample(400, seed=5)
    dfd = market_data.resample(df, "1D")
    now = (df.index[-1] + pd.Timedelta(hours=4)).to_pydatetime().astimezone(JST)
    m = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=now, slot="morning", source="csv")
    cm = m["commentary"]
    assert cm["title_line"].startswith("【今日のドル円】") and cm["title_line"] == cm["post"].splitlines()[0]
    assert "必ず" not in cm["hook"]
    assert Path(m["files"]["png"]).exists() and Path(m["files"]["png_daily"]).exists()
    e = pipeline.run(df, cfg, tmp_path, "4h", dfd, now=now, slot="evening", source="csv")
    assert "png_daily" not in e["files"] and Path(e["files"]["png"]).exists()      # 夜は朝のプランの帯を塗り足した 4H 1 枚だけ
    # 日足なし・帯なし・矢印なしでも落ちない（従来の見出しに戻る）
    cfg2 = pipeline.load_config(CFG)
    cfg2["chart"].update({"title_band": False, "footer_hook": False, "draw_scenario_arrows": False, "evening_overlay": False, "draw_zones": False})
    cfg2["output"]["daily_image"] = False
    r = pipeline.run(df, cfg2, tmp_path / "plain", "4h", None, now=now, slot="morning", source="csv")
    assert Path(r["files"]["png"]).exists() and "png_daily" not in r["files"]
    assert chart.render_daily(dfd.head(5), m, tmp_path / "x.png", tz="Asia/Tokyo") is None    # 日足が短すぎれば作らない
    assert chart._wrap("あ" * 70, 62)[1].endswith("…") is False and len(chart._wrap("あ" * 70, 62)) == 2
