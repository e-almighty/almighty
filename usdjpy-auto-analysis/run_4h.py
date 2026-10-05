"""ドル円 4時間足を解析して、画像と日本語解説を output/ に保存する。

使い方（このフォルダで）:
  python run_4h.py --csv data/USDJPY_4H.csv                        # CSV から
  python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv
  python run_4h.py --gmo                                           # GMOコイン公開APIから直接（SHOのPCで）
  python run_4h.py --sample                                        # 動作確認用の架空データ
  python run_4h.py --csv ... --slot morning                          # 10:05 朝のプラン（--slot evening で 20:05 中間報告、省略時は時刻で自動）
  python run_4h.py --csv ... --now "2026-10-03 20:05"                # 実行時刻を指定（確定足の判定に使う。テスト用）

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
    ap.add_argument("--slot", choices=["morning", "evening", "auto"], default="auto",
                    help="morning=朝のプラン(10:05) / evening=中間報告(20:05) / auto=実行時刻で決める")
    ap.add_argument("--now", help="実行時刻を指定（例 '2026-10-03 20:05'、JST）。省略時は現在時刻")
    ap.add_argument("--no-ledger", action="store_true", help="前回結果（output/state）を読まない・書かない")
    args = ap.parse_args()

    cfg = pipeline.load_config(args.config)
    df_daily = None
    source = "sample" if args.sample else ("gmo" if args.gmo else ("csv" if args.csv else "json"))
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

    now = None
    if args.now:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.fromisoformat(args.now)
        if now.tzinfo is None:
            now = now.replace(tzinfo=ZoneInfo(cfg.get("timezone", "Asia/Tokyo")))
    slot = None if args.slot == "auto" else args.slot
    result = pipeline.run(df, cfg, args.out, "4h", df_daily, now=now, slot=slot,
                          use_ledger=(False if args.no_ledger else None), source=source)
    print("=== 解説 ===")
    print(result["commentary"]["long"])
    print()
    print("=== シナリオ表 ===")
    print(result["commentary"]["table"])
    print()
    print("=== 根拠 ===")
    for e in result["commentary"].get("evidence", []):
        print("-", e)
    print()
    print(f"=== X投稿案（未投稿・{result['commentary']['x_units']} 単位） ===")
    print(result["commentary"]["post"])
    for i, (r, u) in enumerate(zip(result["commentary"].get("post_replies") or [], result["commentary"].get("reply_units") or [])):
        print(f"--- 返信 {i + 1}（{u} 単位） ---")
        print(r)
    if result["commentary"].get("safety_hits"):
        print("（表現チェックで見つかった語：", ", ".join(result["commentary"]["safety_hits"]), "）")
    if result["commentary"].get("post_over_limit"):
        print("（注意：X 投稿案が文字数上限を超えています）")
    print()
    print("保存先:")
    for k, v in result["files"].items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
