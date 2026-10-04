"""ドル円 4時間足を解析して、画像と日本語解説を output/ に保存する。

使い方（このフォルダで）:
  python run_4h.py --csv data/USDJPY_4H.csv                        # CSV から
  python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv
  python run_4h.py --gmo                                           # GMOコイン公開APIから直接（SHOのPCで）
  python run_4h.py --sample                                        # 動作確認用の架空データ

X への投稿はしない（DRY RUN）。投稿案は output/*.md に書き出すだけ。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from usdjpy_analysis import market_data, pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="USDJPY 4時間足 自動分析（DRY RUN）")
    ap.add_argument("--csv", help="4時間足の CSV（t,o,h,l,c,v または time,open,high,low,close）")
    ap.add_argument("--json", help="mcp-tv-get-ohlcv の JSON")
    ap.add_argument("--daily", help="日足の CSV（任意。大局判定に使う）")
    ap.add_argument("--gmo", action="store_true", help="GMOコイン公開APIから 4時間足と日足を取得")
    ap.add_argument("--sample", action="store_true", help="架空データで動作確認")
    ap.add_argument("--config", default=str(HERE / "config" / "analysis.yaml"))
    ap.add_argument("--out", default=str(HERE / "output"))
    args = ap.parse_args()

    cfg = pipeline.load_config(args.config)
    df_daily = None
    if args.sample:
        sys.path.insert(0, str(HERE / "tests"))
        from make_sample import make_sample  # type: ignore
        df = make_sample(400, seed=7)
        df_daily = market_data.resample(df, "1D")
    elif args.gmo:
        import pandas as pd
        y = pd.Timestamp.utcnow().year
        df = market_data.fetch_gmo_klines("USD_JPY", "4hour", [str(y - 1), str(y)])
        df_daily = market_data.fetch_gmo_klines("USD_JPY", "1day", [str(y - 1), str(y)])
    elif args.csv:
        df = market_data.load_csv(args.csv)
    elif args.json:
        df = market_data.load_json(args.json)
    else:
        ap.error("--csv / --json / --gmo / --sample のどれかを指定してください")
        return 2
    if args.daily:
        df_daily = market_data.load_csv(args.daily)

    result = pipeline.run(df, cfg, args.out, "4h", df_daily)
    print("=== 解説 ===")
    print(result["commentary"]["long"])
    print()
    print("=== 根拠 ===")
    for e in result["commentary"].get("evidence", []):
        print("-", e)
    print()
    print("=== X投稿案（未投稿） ===")
    print(result["commentary"]["post"])
    print()
    print("保存先:")
    for k, v in result["files"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
