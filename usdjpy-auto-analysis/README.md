---
type: skill
status: draft
tags:
  - FX
  - USDJPY
  - 自動分析
created: 2026-10-03
updated: 2026-10-03
---

# USDJPY 自動分析 — 動かし方

案件の説明は [[03_PROJECTS/USDJPY_Auto_Analysis/PROJECT_OVERVIEW|PROJECT_OVERVIEW]]、線のルールは [[03_PROJECTS/USDJPY_Auto_Analysis/docs/ANALYSIS_RULES|ANALYSIS_RULES]]。

## 必要なもの

- Python 3.10 以上
- `pip install -r requirements.txt`（pandas / numpy / matplotlib / mplfinance / pyyaml / requests）
- 日本語フォント（Windows は Meiryo が自動で使われる。無い環境では文字化けするので `src/usdjpy_analysis/chart.py` の `FONT_CANDIDATES` に足す）

## 実行（このフォルダで）

```
python run_4h.py --sample                                             # 架空データで動作確認
python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv  # TradingView から書き出した CSV
python run_4h.py --gmo                                                # GMOコイン公開APIから直接（無料・キー不要）
python tests/test_pipeline.py                                         # テスト
```

結果は `output/` に 3 つ出る：`USDJPY_4h_YYYYMMDD_HHMM.png`（画像）、`.md`（解説と X 投稿案）、`.json`（数値）。
**X への投稿はしない（DRY RUN）。** 投稿部分は STEP 7 で X速報bot から流用して足す。

## CSV の形

TradingView MCP の `mcp-tv-get-ohlcv` の出力をそのまま：列 `t,o,h,l,c,v`（`t` は UTC の Unix 秒）。
一般的な `time,open,high,low,close,volume`（time は ISO か Unix 秒）も読める。

## 設定

`config/analysis.yaml`。Pivot の左右本数・ATR 期間・サポレジのまとめ幅・ライン本数・EMA 期間・トレンドラインの許容幅・画像サイズ。コードに数字を埋め込まない。

## 構成

| ファイル | 役割 |
|---|---|
| `src/usdjpy_analysis/market_data.py` | CSV / JSON / GMOコイン klines → 同じ形の DataFrame。下位足から上位足への変換 |
| `src/usdjpy_analysis/indicators.py` | EMA / RMA / ATR（Pine の ta.* と同じ定義。FX_PhoenixConfluence の tvbt.py から移植） |
| `src/usdjpy_analysis/swings.py` | Pivot High / Low、交互スイング（ZigZag 風） |
| `src/usdjpy_analysis/levels.py` | サポレジ候補のクラスタリング・反応回数・重要度・間引き |
| `src/usdjpy_analysis/trend.py` | 相場環境の 5 分類（スコア方式） |
| `src/usdjpy_analysis/trendlines.py` | 上昇・下降トレンドライン候補（2 点＋3 点目確認・ブレイク判定） |
| `src/usdjpy_analysis/chart.py` | 投稿用 PNG（mplfinance） |
| `src/usdjpy_analysis/commentary.py` | 日本語解説と X 投稿案（ルールベース。AI で磨くのは後） |
| `src/usdjpy_analysis/pipeline.py` | 上を順につなぐ。`analyze()` と `run()` |
| `run_4h.py` | 4時間足の入口 |

## 正本の場所

- 正本はこの Vault（Dropbox で全 PC に同期）
- 同じ内容を GitHub `e-almighty/almighty` のブランチ `claude/nice-sagan-kgqry5` の `usdjpy-auto-analysis/` にも置いている（履歴用）
