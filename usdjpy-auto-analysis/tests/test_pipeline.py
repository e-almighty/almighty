"""最低限の動作テスト:  python -m pytest tests  または  python tests/test_pipeline.py"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from make_sample import make_sample  # noqa: E402
from usdjpy_analysis import indicators, market_data, pipeline, swings  # noqa: E402

CFG = HERE.parent / "config" / "analysis.yaml"


def test_pivots_basic():
    h = [1, 2, 3, 5, 3, 2, 1, 2, 3, 4, 3, 2, 1]
    l = [0, 1, 2, 4, 2, 1, 0, 1, 2, 3, 2, 1, 0]
    highs, lows = swings.find_pivots(h, l, 2, 2)
    assert [s.index for s in highs] == [3, 9]
    assert [s.index for s in lows] == [6]


def test_ema_matches_pine_seed():
    e = indicators.ema([1, 2, 3, 4], 3)
    assert abs(e[0] - 1.0) < 1e-9          # 初値で初期化
    assert abs(e[1] - 1.5) < 1e-9          # alpha=0.5


def test_csv_roundtrip(tmp_path):
    df = make_sample(80)
    p = tmp_path / "x.csv"
    out = df.copy()
    out["t"] = (out.index.view("int64") // 10**9)
    out = out.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})
    out[["t", "o", "h", "l", "c", "v"]].to_csv(p, index=False)
    back = market_data.load_csv(p)
    assert len(back) == 80 and back.index.tz is not None
    assert abs(float(back["close"].iloc[-1]) - float(df["close"].iloc[-1])) < 1e-6


def test_end_to_end(tmp_path):
    df = make_sample(400, seed=3)
    cfg = pipeline.load_config(CFG)
    res = pipeline.run(df, cfg, tmp_path, "4h", market_data.resample(df, "1D"))
    assert Path(res["files"]["png"]).exists()
    assert Path(res["files"]["md"]).exists()
    assert res["trend"]["label"] in {"強い上昇", "弱い上昇", "レンジ", "弱い下落", "強い下落"}
    assert len(res["supports"]) <= 3 and len(res["resistances"]) <= 3
    for lv in res["supports"]:
        assert lv["price"] < res["close"]
    for lv in res["resistances"]:
        assert lv["price"] > res["close"]
    assert "必ず" not in res["commentary"]["long"] and "絶対" not in res["commentary"]["long"]


if __name__ == "__main__":
    import tempfile
    test_pivots_basic(); test_ema_matches_pine_seed()
    with tempfile.TemporaryDirectory() as d:
        test_csv_roundtrip(Path(d)); test_end_to_end(Path(d))
    print("all tests passed")
