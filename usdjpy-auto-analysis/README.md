---
type: skill
status: draft
tags:
  - FX
  - USDJPY
  - 自動分析
created: 2026-10-03
updated: 2026-10-04
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
python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv  # TradingView から書き出した CSV（実行時刻で朝／中間を自動判定）
python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv --slot morning   # 10:05 朝のプラン
python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv --slot evening   # 20:05 中間報告
python run_4h.py --csv ... --now "2026-10-02 20:05"                   # 実行時刻を指定（確定足の判定に使う。過去の時点を再現）
python run_4h.py --gmo                                                # GMOコイン公開APIから直接（無料・キー不要）
python -m pytest tests -q                                             # テスト（pip install pytest）
```

結果は `output/` に 3 つ出る：`USDJPY_4h_YYYYMMDD_HHMM.png`（画像）、`.md`（解説・シナリオ表・根拠・X 投稿案）、`.json`（数値）。
前回の結果は `output/state/last_result.json` と `output/ledger.csv` に残り、次回の「変化点」「前回の注目帯への反応」に使う（`--no-ledger` で無効）。
**X への投稿はしない（DRY RUN）。** 実行のたびに `output/outbox/` に「送信予定」（`…_送信予定.md`＝人が読む用、`.json`＝機械用）を書く。中身は 本体（画像＋ALT）→ 返信① → 返信② と、夜なら「朝の投稿の引用」。設定は `config/social.yaml`（`dry_run: true` のまま。本番 ON は SHO 確認後。鍵は環境変数 `X_API_KEY` などで渡し、ファイルには書かない）。`--no-plan` で書かない。

## CSV の形

TradingView MCP の `mcp-tv-get-ohlcv` の出力をそのまま：列 `t,o,h,l,c,v`（`t` は UTC の Unix 秒）。
一般的な `time,open,high,low,close,volume`（time は ISO か Unix 秒）も読める。

## 設定

`config/analysis.yaml`。Pivot の左右本数・ATR 期間・サポレジのまとめ幅・ライン本数・EMA 期間・トレンドラインの許容幅・画像サイズ、第2ステージの `tolerances`（判定幅）・`fibonacci`・`divergence`・`sqzmom`・`zones`（根拠の重み）・`posting`（X 投稿の型 thread／long／short・タイトル・長さ・ハッシュタグ・答え合わせ）・`chart.draw_*`（描く／描かない）。コードに数字を埋め込まない。

## 構成

| ファイル | 役割 |
|---|---|
| `src/usdjpy_analysis/market_data.py` | CSV / JSON / GMOコイン klines → 同じ形の DataFrame。下位足から上位足への変換 |
| `src/usdjpy_analysis/indicators.py` | EMA / RMA / ATR（Pine の ta.* と同じ定義。FX_PhoenixConfluence の tvbt.py から移植） |
| `src/usdjpy_analysis/swings.py` | Pivot High / Low、交互スイング（ZigZag 風） |
| `src/usdjpy_analysis/levels.py` | サポレジ候補のクラスタリング・反応回数・重要度・間引き |
| `src/usdjpy_analysis/trend.py` | 相場環境の 5 分類（スコア方式） |
| `src/usdjpy_analysis/trendlines.py` | 上昇・下降トレンドライン候補（2 点＋3 点目確認・ブレイク判定） |
| `src/usdjpy_analysis/channels.py` | 平行チャネル（上限・中央・下限） |
| `src/usdjpy_analysis/bars.py` | 確定足の一元管理、前日・前週・今週の高安、日足 ATR／EMA |
| `src/usdjpy_analysis/structure.py` | 主要スイングの選別、ダウ理論の状態機械（押し安値・戻り高値） |
| `src/usdjpy_analysis/fibonacci.py` | フィボナッチ・リトレースメント／エクステンション |
| `src/usdjpy_analysis/divergence.py` | RSI ダイバージェンス（通常・隠れ） |
| `src/usdjpy_analysis/momentum.py` | SQZMOM の文章、RSI の現在値、ATR の文脈（pips・分位） |
| `src/usdjpy_analysis/zones.py` | 注目価格帯（根拠の重なりをまとめて格付け） |
| `src/usdjpy_analysis/safety.py` | 表現の安全弁（断定語の検出・置換、免責） |
| `src/usdjpy_analysis/ledger.py` | 前回結果の保存と「変化点」「前回の線への反応」 |
| `src/usdjpy_analysis/chart.py` | 投稿用 PNG（mplfinance） |
| `src/usdjpy_analysis/commentary.py` | 日本語解説と X 投稿案（ルールベース。AI で磨くのは後） |
| `src/usdjpy_analysis/pipeline.py` | 上を順につなぐ。`analyze()` と `run()` |
| `social/x_publisher.py` | X 投稿プログラム（DRY RUN）。送信予定の組み立て・ALT・疑似投稿 ID の台帳書き戻し。本番送信は未実装 |
| `run_4h.py` | 4時間足の入口 |

## 正本の場所

- 正本はこの Vault（Dropbox で全 PC に同期）
- 同じ内容を GitHub `e-almighty/almighty` のブランチ `claude/nice-sagan-kgqry5` の `usdjpy-auto-analysis/` にも置いている（履歴用）
