---
type: project
status: active
tags:
  - FX
  - USDJPY
  - 自動分析
  - X投稿
created: 2026-10-03
updated: 2026-10-03
通貨ペア: USDJPY
次の一手: SHOのPCでTradingViewから4時間足CSVを書き出し、本物のデータで画像を作ってSHOが線の引き方を確認する（STEP 3）
---

# USDJPY 自動テクニカル分析・チャート投稿システム

ドル円に限定して、「数値解析 → ライン描画 → 画像生成 → 日本語解説 →（後で）X投稿」を自動化する。
**自動売買ではない。** 売買注文を出す機能は作らない。

依頼者：SHO ／ 引き継ぎメモ：2026-10-03 ／ 作業：Claude Code

## 現在の状態（2026-10-03）

- **STEP 1 完了**：既存資産の棚卸しと TradingView 公式 MCP の確認 → [[03_PROJECTS/USDJPY_Auto_Analysis/docs/STEP1_報告_2026-10-03|STEP 1 報告]]
- **STEP 2 試作完了（架空データで動作確認済み）**：4時間足について、データ読込 → スイング高安 → サポレジ → 相場環境 → トレンドライン → PNG → 日本語解説 まで。X 投稿なし
- **未実施**：本物のドル円データでの実行（クラウドの作業部屋から市場データ元に通信できないため）。SHO の PC で TradingView MCP から CSV を書き出してもらう（下の「SHO の手順」）

## 役割分担（決定事項）

| 時間足 | 役割 | 投稿 |
|---|---|---|
| 4時間足 | 定期の相場解説 | 09:00 / 13:00 / 17:00 / 21:00 JST（予定・まだ投稿しない） |
| 1時間足 | 中間アップデート | 設定ファイルで時刻指定（後で） |
| 5分足 | 変化・速報（イベント駆動） | 条件成立時のみ（後で） |

- データ元：TradingView MCP（Claude Code 内・15分以上遅延あり）／GMOコイン公開API（Python から直接・無料・キー不要）。試作は CSV と GMO。5分足の速報は遅延の小さい GMO を第一候補
- ライン描画：**Python で投稿画像を生成**。Pine Script は TradingView 上で同じラインを見るための表示専用（STEP 3 で線のルールが固まってから作る）
- 実行場所：SHO の Windows PC（X速報bot と同じ）。クラウド側は設計・コード・レビュー
- X 投稿：既存の [[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot]] の投稿部分を共通化して使う（画像アップロードを追加）。**本番投稿 ON は SHO 確認後。最初は必ず DRY RUN**

## フォルダ

```
03_PROJECTS/USDJPY_Auto_Analysis/
  PROJECT_OVERVIEW.md   このノート
  README.md             動かし方
  docs/                 STEP1 報告・ANALYSIS_RULES（線の引き方）
  config/analysis.yaml  設定値（Pivot期間・ATR・ライン本数など。コードに埋め込まない）
  src/usdjpy_analysis/  Python 本体（market_data / indicators / swings / levels / trend / trendlines / chart / commentary / pipeline）
  run_4h.py             4時間足の実行入口（DRY RUN）
  tests/                動作テストと架空データ
  data/                 ローソク足 CSV（TradingView MCP から書き出す）
  output/               生成した PNG・解説 md・JSON
  pine/                 TradingView 表示用（STEP 3 以降）
```

## SHO の手順：本物のデータで画像を作る

1. SHO の PC の Claude Code（`claude`）に、次を貼る（TradingView MCP が接続済みであること）

   ```
   mcp-tradingview の mcp-tv-get-ohlcv で OANDA:USDJPY のローソク足を取得して CSV に保存して。
   ・4時間足：interval 4h、count 1000 → C:\Users\user\Dropbox\HIRATA\Obsidian\Almighty-AI-Brain\03_PROJECTS\USDJPY_Auto_Analysis\data\USDJPY_4H.csv
   ・日足：interval 1D、count 400 → 同じフォルダの USDJPY_1D.csv
   CSV の列は t,o,h,l,c,v（t は UTC の Unix 秒）。ヘッダー行あり、古い順。同名ファイルがあれば上書きしてよい。
   保存したら、それぞれの行数と最初・最後の日時（日本時間）を教えて。
   ```

2. 「保存した」とクラウド側の Claude に伝える → Dropbox 経由で読み、画像と解説を作って見せる
3. SHO が「線の引き方が自分の考えと合っているか」を見る（**STEP 3・ここが一番大事**）。直したい点を言葉で伝えれば `config/analysis.yaml` と `docs/ANALYSIS_RULES.md` を直す
4. 線のルールが固まるまで、1時間足・5分足には広げない

## 開発の順番（引き継ぎメモより）

1. ~~TradingView MCP 接続とツール確認~~ 完了
2. ~~4時間足だけで試作（データ取得・高安・サポレジ・トレンド・トレンドライン・画像・解説）~~ 架空データで完了
3. **SHO が線の引き方を確認（今ここ）**
4. 1時間足へ展開（4時間足の方向を参照）
5. 5分足へ展開（4時間足・1時間足を上位足として参照）
6. 画像の仕上げ（SNS に載せられる状態）
7. X 投稿部分を X速報bot から再利用。DRY RUN で投稿文・画像・予定時刻を保存
8. SHO 確認後に X 本番投稿を有効化
9. 必要なら Instagram

## やること（AI が進められる）

- 本物のデータで `run_4h.py` を実行し、画像を SHO に見せる
- `00_HOME/00_START_HERE.md` にこのフォルダへのリンクを1行足す（Dropbox 連携からは既存ファイルを書き換えられないため、SHO の PC の Claude Code で行う）
- 線のルールが固まったら `pine/USDJPY_4H_Analyzer.pine` を作る
- GMOコイン klines の取得を SHO の PC で実際に試す（`python run_4h.py --gmo`）

## 関連

- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/STEP1_報告_2026-10-03|STEP 1 報告（棚卸し・MCP確認）]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/ANALYSIS_RULES|ANALYSIS_RULES（線の引き方・解説文のルール）]]
- [[03_PROJECTS/FX_PhoenixConfluence/PROJECT_OVERVIEW|FX_PhoenixConfluence（売買ストラテジー研究・別案件）]]
- [[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot（投稿部分を流用）]]
- [[05_SKILLS/fx-morning-report/SKILL|fx-morning-report（ラインの優先順位の出典）]]
- [[09_INBOX/TradingView_MCP_ツール一覧_2026-10-03|TradingView MCP ツール一覧]]
- [[01_MEMORY/start-simplest-verify-tools|最短手段で確認する]]
