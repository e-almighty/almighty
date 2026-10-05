---
type: project
status: active
tags:
  - FX
  - USDJPY
  - 自動分析
  - X投稿
created: 2026-10-03
updated: 2026-10-05
通貨ペア: USDJPY
次の一手: X投稿部分（DRY RUN。本体→返信2投、夜は朝の投稿を引用）を作る（APIキーはSHOが取得）。画像のタイトル帯・日足2枚目。プロフィール文は再相談。1時間足へ展開
---

# USDJPY 自動テクニカル分析・チャート投稿システム

ドル円に限定して、「数値解析 → ライン描画 → 画像生成 → 日本語解説 →（後で）X投稿」を自動化する。
**自動売買ではない。** 売買注文を出す機能は作らない。

依頼者：SHO ／ 引き継ぎメモ：2026-10-03 ／ 作業：Claude Code

## 現在の状態（2026-10-04・第2ステージ 4時間足を仕上げた時点）

- **STEP 1 完了**：既存資産の棚卸しと TradingView 公式 MCP の確認 → [[03_PROJECTS/USDJPY_Auto_Analysis/docs/STEP1_報告_2026-10-03|STEP 1 報告]]
- **STEP 2 完了**：4時間足のパイプライン（データ → スイング → サポレジ → 相場環境 → チャネル → PNG → 解説）。本物のドル円 CSV で実行し SHO に提示済み → [[03_PROJECTS/USDJPY_Auto_Analysis/output/USDJPY_4h_2026-10-03_初回|初回結果]]
- **STEP 3 進行中**：SHO ヒアリングで決まったこと（EMA 20/50/200・平行チャネル＋中央線・サポート赤／レジスタンス緑・フィボ必須・RSI ダイバージェンス・SQZMOM は文章のみ・1 日 2 回 10:05／20:05）を反映。**第2ステージ（2026-10-04）**：確定足の一元管理、主要スイングとダウ理論（押し安値）、フィボナッチ、RSI サブパネルとダイバージェンス、SQZMOM・ATR の文章、注目価格帯（根拠の重なり）、シナリオ表、朝のプラン／中間報告、台帳、表現の安全弁 → [[03_PROJECTS/USDJPY_Auto_Analysis/output/USDJPY_4h_2026-10-04_第2ステージ_朝のプラン|第2ステージの出力例]]。ルールは [[03_PROJECTS/USDJPY_Auto_Analysis/docs/ANALYSIS_RULES|ANALYSIS_RULES]] 8〜15 節
- **解析の追加提案**（4 視点の案出し → 査読 → 統合）→ [[03_PROJECTS/USDJPY_Auto_Analysis/docs/解析の追加提案_2026-10-04|解析の追加提案]]。A 群（すぐ入れる）は第2ステージで実装済み、B 群（ブレイク判定・ADX・EMA 乖離・レンジ処理・ローソク足パターン）と C 群（1H・5M・MTF・セッション・答え合わせの集計）は未着手
- **有名トレーダーの手法調査**（小次郎講師・神藤さん・維新の介さん・石井信介さん・国内外）：完了 → [[03_PROJECTS/USDJPY_Auto_Analysis/docs/有名トレーダーの手法調査_2026-10-04|有名トレーダーの手法調査]]。人物 3 名を特定（石井信介さんは未特定）、手法 92 件中 72 件を裏取り。次は 4-2 の優先順で解説文に反映
- **X 自動投稿**：平日 10:05（朝のプラン）と 20:05（中間報告）の 1 日 2 回で決定。投稿文は「タイトル【今日のドル円】→ チャート → 説明」。**SHO 決定（2026-10-05）：第 1 案 thread（短い本体＋返信 2 投）・ハッシュタグ 2 個・10:05／20:05・夜は ✅ 答え合わせ＋朝の投稿を引用**（ANALYSIS_RULES 16 節。個人名は出さない）。出し方のリサーチと提案 → [[03_PROJECTS/USDJPY_Auto_Analysis/docs/X発信リサーチ_2026-10-04|X 発信リサーチ]]（2026-10-05）。進め方は [[03_PROJECTS/USDJPY_Auto_Analysis/docs/X自動投稿の進め方|X自動投稿の進め方]]。SHO は X の API キーをまだ持っていない（取得待ち）。投稿プログラムは DRY RUN から
- 作業の詳細 → [[03_PROJECTS/USDJPY_Auto_Analysis/docs/作業ログ_2026-10-03|作業ログ 2026-10-03]]／[[03_PROJECTS/USDJPY_Auto_Analysis/docs/作業ログ_2026-10-04|作業ログ 2026-10-04]]

## 役割分担（決定事項）

| 時間足 | 役割 | 投稿 |
|---|---|---|
| 4時間足 | 定期の相場解説 | **平日 10:05（朝のプラン）と 20:05（中間報告）の 1 日 2 回**（SHO 決定 2026-10-04） |
| 1時間足 | 中間アップデート | 設定ファイルで時刻指定（後で） |
| 5分足 | 変化・速報（イベント駆動） | 条件成立時のみ（後で） |

- データ元：TradingView MCP（Claude Code 内・15分以上遅延あり）／GMOコイン公開API（Python から直接・無料・キー不要）。定時実行は GMO を第一候補（PC での動作確認はまだ）。5分足の速報も遅延の小さい GMO
- ライン描画：**Python で投稿画像を生成**。Pine Script は TradingView 上で同じラインを見るための表示専用（線のルールが固まってから作る）
- 実行場所：SHO の Windows PC（X速報bot と同じ）。クラウド側は設計・コード・レビュー。クラウドの作業部屋は市場データ元に通信できない
- X 投稿：[[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot]] の投稿部分を共通化し、画像アップロードを足す。**本番投稿 ON は SHO 確認後。最初は必ず DRY RUN**

## フォルダ

```
03_PROJECTS/USDJPY_Auto_Analysis/
  PROJECT_OVERVIEW.md   このノート
  README.md             動かし方
  docs/                 STEP1_報告・ANALYSIS_RULES（線の引き方）・X自動投稿の進め方・作業ログ
  config/analysis.yaml  設定値（Pivot期間・ATR・ライン本数など。コードに埋め込まない）
  src/usdjpy_analysis/  Python 本体（market_data / indicators / swings / levels / trend / trendlines / channels / bars / structure / fibonacci / divergence / momentum / zones / safety / ledger / chart / commentary / pipeline）
  run_4h.py             4時間足の実行入口（DRY RUN）
  tests/                動作テストと架空データ
  data/                 ローソク足 CSV（USDJPY_4H.csv 1000本・USDJPY_1D.csv 400本。2026-10-03 TradingView から書き出し）
  output/               解説 md（画像 PNG は PC で実行すると同じ場所にできる）
  pine/                 TradingView 表示用（STEP 3 以降・まだ空）
```

## SHO の手順：データを最新にして画像を作り直す

1. PC の Claude Code（`claude`）に貼る（TradingView MCP が接続済みであること）

   ```
   mcp-tradingview の mcp-tv-get-ohlcv で OANDA:USDJPY のローソク足を取得して CSV に保存して。
   ・4時間足：interval 4h、count 1000 → C:\Users\user\Dropbox\HIRATA\Obsidian\Almighty-AI-Brain\03_PROJECTS\USDJPY_Auto_Analysis\data\USDJPY_4H.csv
   ・日足：interval 1D、count 400 → 同じフォルダの USDJPY_1D.csv
   CSV の列は t,o,h,l,c,v（t は UTC の Unix 秒）。ヘッダー行あり、古い順。同名ファイルがあれば上書きしてよい。
   保存したら、それぞれの行数と最初・最後の日時（日本時間）を教えて。
   ```

2. 「保存した」とクラウド側の Claude に伝える → Dropbox 経由で読み、画像と解説を作って見せる
3. PC で自分で作る場合：このフォルダで `pip install -r requirements.txt` のあと `python run_4h.py --csv data/USDJPY_4H.csv --daily data/USDJPY_1D.csv`

## 開発の順番（引き継ぎメモより）

1. ~~TradingView MCP 接続とツール確認~~ 完了（2026-10-03）
2. ~~4時間足だけで試作~~ 完了・本物データで実行済み（2026-10-03）
3. **SHO が線の引き方を確認（今ここ）** — 第2ステージの 4時間足（ダウ理論・フィボ・RSI・注目帯・2 回投稿の型）まで実装済み
4. 1時間足へ展開（4時間足の方向を参照）
5. 5分足へ展開（4時間足・1時間足を上位足として参照）
6. 画像の仕上げ（SNS に載せられる状態）
7. X 投稿部分を X速報bot から再利用。DRY RUN で投稿文・画像・予定時刻を保存 ← SHO の希望により、3 と並行して準備を始める
8. SHO 確認後に X 本番投稿を有効化
9. 必要なら Instagram

## やること（AI が進められる）

- SHO の感想を受けて線のルールと設定を調整し、作り直す
- 有名トレーダー手法の調査結果を docs に保存し、解説文の言い回し・判定に反映する
- 解析の追加提案の B 群（ブレイク・ダマシ・リテストの 6 区分、ADX、EMA 乖離、レンジ専用処理、ローソク足パターン）
- `social/x_publisher.py`・`config/social.yaml`・定時実行バッチ・タスク スケジューラ手順（DRY RUN）
- PC で `python run_4h.py --gmo` が動くか確認（GMOコイン klines は未検証）
- 線のルール確定後に `pine/USDJPY_4H_Analyzer.pine`
- 前日高値・安値をラインに加える案（ANALYSIS_RULES の「確認したいこと」）

## セーブの約束

「セーブして」と言われたら、①Vault に最新ファイル ②GitHub にコミット＋push ③その日の作業ログを `docs/` に 1 本、の 3 点セット。
Vault が正本（Dropbox で全 PC に同期）。GitHub は履歴用：`e-almighty/almighty` のブランチ `claude/nice-sagan-kgqry5` の `usdjpy-auto-analysis/`。
クラウド側の Claude は Dropbox 連携から既存ノートを書き換えられないので、`MEMORY.md`・`00_START_HERE.md`・`やりかけ一覧.md` への登録は PC 側の Claude Code に頼む（手順は作業ログの末尾）。

## 関連

- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/作業ログ_2026-10-03|作業ログ 2026-10-03]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/作業ログ_2026-10-04|作業ログ 2026-10-04]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/解析の追加提案_2026-10-04|解析の追加提案 2026-10-04]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/有名トレーダーの手法調査_2026-10-04|有名トレーダーの手法調査 2026-10-04]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/X発信リサーチ_2026-10-04|X 発信リサーチと出し方の提案 2026-10-04]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/再開のしかた_合言葉|再開のしかた（合言葉）]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/output/USDJPY_4h_2026-10-04_第2ステージ_朝のプラン|第2ステージの出力例（2026-10-04）]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/STEP1_報告_2026-10-03|STEP 1 報告（棚卸し・MCP確認）]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/ANALYSIS_RULES|ANALYSIS_RULES（線の引き方・解説文のルール）]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/docs/X自動投稿の進め方|X自動投稿の進め方]]
- [[03_PROJECTS/USDJPY_Auto_Analysis/output/USDJPY_4h_2026-10-03_初回|初回結果（2026-10-03）]]
- [[01_MEMORY/usdjpy-auto-analysis|記憶ノート]]
- [[03_PROJECTS/FX_PhoenixConfluence/PROJECT_OVERVIEW|FX_PhoenixConfluence（売買ストラテジー研究・別案件）]]
- [[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot（投稿部分を流用）]]
- [[05_SKILLS/fx-morning-report/SKILL|fx-morning-report（ラインの優先順位の出典）]]
- [[09_INBOX/TradingView_MCP_ツール一覧_2026-10-03|TradingView MCP ツール一覧]]
- [[01_MEMORY/start-simplest-verify-tools|最短手段で確認する]]
