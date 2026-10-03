---
type: plan
status: draft
tags:
  - FX
  - USDJPY
  - X投稿
created: 2026-10-03
updated: 2026-10-03
---

# X 自動投稿の進め方（SHO の希望：毎日自動投稿）

2026-10-03 に SHO から「このチャートと解説を X に毎日自動投稿したい」と要望。進め方を整理した。
一言で言うと：**SHO が X の投稿用のカギを取る → Claude が投稿プログラムとスケジュールを作る → まず「投稿したつもり」（DRY RUN）で数日動かす → SHO が OK を出したら本番 ON**。

## 全体のしくみ（4つの部品）

| 部品 | 内容 | 担当 |
|---|---|---|
| X の投稿用のカギ（API キー） | プログラムからの投稿を X に許可する鍵。本人の X アカウントで取る | SHO |
| 決まった時刻に動くパソコン | 最初は SHO の Windows PC。タスク スケジューラに「毎朝 9:00 に実行」と登録。その時刻にスリープしていると動かない。安定したら VPS へ | SHO（PC）／Claude（手順） |
| 投稿プログラム | [[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot]] の投稿部分（鍵の扱い・DRY RUN・重複防止・1日の上限・ログ）を流用し、画像アップロードを足す | Claude |
| 安全弁 | 最初は必ず DRY RUN。1日の投稿上限、二重投稿防止、「必ず」「絶対」を使わない、投資助言ではない旨の一文 | Claude（プログラムに固定） |

## SHO にやっていただくこと（カギの取得）

X速報bot のノートの手順と同じ。**X速報bot 用に取ってあれば同じカギを使えるので飛ばせる。**

1. https://developer.x.com に、投稿したい X アカウントでサインイン
2. プロジェクトとアプリを作る
3. **先に** アプリの「User authentication settings」で権限を **Read and Write** にする（後回しにすると読み取り専用のカギになり、投稿できない。その場合は再生成）
4. 4つのカギを控える：API Key／API Key Secret／Access Token／Access Token Secret
5. 投稿は1件ごとの従量課金。クレジットをチャージする（X速報bot の記録では最低 5 ドル、新規は 10 ドル分の券あり。金額は変わるので画面で確認）
6. 4つのカギは **Dropbox の外**（X速報bot と同じ `C:\Users\user\.x-sokuho-bot\` のような場所）の設定ファイルに貼る。Obsidian・GitHub・保管庫には絶対に置かない。貼る場所と書き方は Claude がそのとき案内する

## Claude が作るもの

- `src/usdjpy_analysis/social/x_publisher.py`：X速報bot の `XPoster`／`State`／`clip_tweet` を共通化し、画像アップロード（media upload → tweet に添付）を追加
- `config/social.yaml`：投稿時刻、1日の上限、`dry_run` の ON/OFF、ハッシュタグ、免責の一文
- 1回で「データ取得 → 解析 → 画像 → 文章 → 投稿（またはログ）」まで通る実行ファイルと、タスク スケジューラへの登録手順
- 定時実行のデータ元はログイン不要の GMOコイン公開API を第一候補（TradingView MCP は Claude Code の中でしか使えないため）。SHO の PC で一度、取れることを確認する

## 進める順番（安全のため）

1. SHO：カギを取る。並行して Claude が投稿プログラムを作る
2. SHO の PC で DRY RUN を数日動かし、「投稿される予定だった文章と画像」をログで確認する
3. SHO が線の引き方と文章に納得したら、本番 ON（`config/social.yaml` の `dry_run` を false にするだけ）
4. 最初は 1日1回（朝 9:00）から始め、慣れたら 13:00・17:00・21:00 を足す

## SHO に決めてもらうこと（2026-10-03 時点・未回答）

1. X のカギは、すでに X速報bot 用に取ってあるか。これから取るか
2. 投稿回数は、まず 1日1回（朝 9:00）でよいか。引き継ぎメモは 4時間ごと（9・13・17・21時）

## 注意（引き継ぎメモと共通ルールより）

- 外部への投稿・送信は、本番を有効にする前に SHO へ確認する。最初は必ず DRY RUN
- 秘密鍵・API キー・アクセストークンは Vault へ保存しない
- 既存アカウントに流すので、大量投稿・同一文面の連投はスパム判定のリスク。上限とクールダウンは外さない

## 関連

- [[03_PROJECTS/USDJPY_Auto_Analysis/PROJECT_OVERVIEW|USDJPY自動分析 プロジェクト]]
- [[03_PROJECTS/X速報bot/PROJECT_OVERVIEW|X速報bot（投稿部分の流用元・カギの取り方）]]
- [[01_MEMORY/x-sokuho-bot|X速報bot の記憶ノート]]
