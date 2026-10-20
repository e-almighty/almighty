---
type: project
status: active
tags:
  - 勉強会
  - セミナー
  - スライド
  - 日本営業協会
created: 2026-10-19
updated: 2026-10-20
開催日: 2026-10-21
---

# AI勉強会（2026-10-21）— 日本営業協会 勉強会 第一部 AI「GPT-6 Astra」

## これは何か

2026-10-21（水）18:30 中央区役所。日本営業協会の勉強会（第8回AIセミナー兼・夜の勉強会は初回）。第一部 AI・第二部 マーケティング。無料、食事代実費 2,000 円。参加者は営業協会の会員が中心で、60〜70 代も含む。
第一部の題材は **GPT-6 Astra**（いかに有効に使うか、生まれた概念、できること、活用法）と **Claude Code（Fable 5.1）との対比**。スライドは 40 枚（明るい地・水色×濃紺）。

経緯は [[04_KNOWLEDGE/会社運営/AI勉強会・セミナーの収益化と事業の尖らせ方|AI勉強会・セミナーの収益化]]（第 8 回は 10/21、今年いっぱい無料・来年から有料化）と [[01_MEMORY/ai-benkyokai-202608|AI勉強会シリーズの記憶ノート]]。

## 中身と開き方

| もの | 場所 | 状態 |
|---|---|---|
| **スライド（発表用・1 ファイル HTML）** | `納品/第一部AI_Astraを味方にする夜_2026-10-21.html` — ブラウザで開き、矢印キーで送る | 2026-10-20 完成（40 枚） |
| **スライド（ブラウザ用ページ・claude.ai）** | https://claude.ai/artifact/2nXrEX4QhtbjQacZkQJuXR — スマホでもタップ・スワイプで送れる。非公開（SHO のアカウントで開く。人に見せるときはページの共有メニューから） | 2026-10-20 公開 |
| **スライド（PDF・配布用）** | `納品/第一部AI_Astraを味方にする夜_2026-10-21.pdf`（40 ページ・16:9・6 MB） | 2026-10-20 完成 |
| **Codex版38枚（写真・図解入り、別版）** | `Codex版_38枚/納品/` — HTML・PDF・編集用PowerPoint・話者ノート・リサーチ・画像素材。既存40枚版は上書きしていない | 2026-10-20 完成・保存 |
| 話者ノート | `speaker-notes.md` | 完成 |
| リサーチ要約（正体・概念・できること・使い方・任せ方・注意点・6.1 Astra 中止・Fable 5.1 との対比・構成案・要確認リスト・出典） | [[03_PROJECTS/AI勉強会_20261021/リサーチ_GPT-6Astra_活用と対比|リサーチ_GPT-6Astra_活用と対比]] | 2026-10-19 完成 |
| 編集元 | `slides/index.html`（＋`css07/` `js07/` `img/`）。中身の定義は `build_deck.py`、後工程は `deck_tools.py` | — |
| 設計書類・制作記録 | `brief.md` `questions.md` `story-plan.md` `source-map.md` `review-notes.md` | 完成 |
| 全ページの画面写真 | `screenshots/final/`（40 枚）、俯瞰 `screenshots/overview/` | 完成 |

### 直し方（AI 向け）

1. 文言・図解は `build_deck.py` の該当スライドを直す（40 枚は `add(...)` の順）
2. `python3 build_deck.py` → `python3 deck_tools.py all`（撮影 → 一覧 → 1 ファイル化 → PDF）
3. `screenshots/overview/sheet_1.png` `sheet_2.png` で崩れを確認し、`review-notes.md` に記録
4. 見た目の正本 `css07/deck07.css` `js07/deck07.js` は触らない。明るい地は `css07/deck07-bright.css`

## 次の一歩

1. **SHO が PDF を通しで確認**（デザイン・自己紹介の文言・10 分版の要否）
2. 任意：17・18 枚目に SHO の ChatGPT 画面写真を差し込む／40 枚目にアンケート QR を入れる（前回の QR が有効か要確認）
3. 当日までに大きな発表があれば 5・16・33 枚目の数字を見直す（数字は 2026-10-19 時点）
4. 開催後：参加人数・反応・次回テーマを [[04_KNOWLEDGE/会社運営/AI勉強会・セミナーの収益化と事業の尖らせ方|収益化のノート]] と [[01_MEMORY/ai-benkyokai-202608|記憶ノート]] に追記

## 最新のセーブポイント（2026-10-20 深夜）

追記（2026-10-20）：Codexで写真4点・イラスト2点・図解10ページを加えた**別版38枚**を制作。`Codex版_38枚/納品/2026-10-20_Astra勉強会_Codex版38枚_セーブポイント.md` に現在地と検証結果を記録。既存の40枚版とは混同・上書きしない。

| 項目 | 状態 |
|---|---|
| リサーチ要約 | 完成（2026-10-19 時点の数字・出典付き） |
| スライド 40 枚（明るい地） | 完成。1 ファイル HTML と PDF を `納品/` に出力。**SHO の通し確認待ち** |
| ブラウザ用ページ | https://claude.ai/artifact/2nXrEX4QhtbjQacZkQJuXR（非公開。SHO のアカウントで開く） |
| 配布用コピー | デスクトップ `AI勉強会10月度分`（このPCのみ） |
| GitHub（履歴用・非公開） | `e-almighty/almighty` ブランチ `claude/ai-benkyokai-20261021`、フォルダ `ai-benkyokai-20261021/`。最初のコミット `5262ac4`（64 ファイル・約 23 MB）。ローカルの複製は `C:/Users/user/20260530/almighty`（このPCのみ・Dropbox の外） |
| 次の一歩 | ① SHO が PDF を通しで確認 ② 直しがあれば `build_deck.py` → `deck_tools.py all` ③ 任意で画面写真・アンケート QR ④ 開催後に結果を記録 |
| 読む順 | `PROJECT_OVERVIEW.md` → `作業ログ_2026-10-20.md` → `review-notes.md` → リサーチ要約 |

正本は Vault（Dropbox で全 PC に同期）。GitHub は「セーブして」と言われた時点の写し。Vault を直したら、次の「セーブして」で GitHub も追いつかせる。

## 呼び出し方（どの PC・どの AI でも同じ）

再開の一言：

```
Astra の勉強会の続き。Vault の 03_PROJECTS/AI勉強会_20261021/PROJECT_OVERVIEW.md と一番新しい作業ログを読んで、今の状況と次の一歩を報告して。
```

AI はこれを受けたら ①このノート ②一番新しい `作業ログ_*.md` を読み、現在地と SHO 待ちを 5 行以内で報告して指示を待つ。勝手にスライドを作り直さない。

| SHO が言う言葉 | AI がやること |
|---|---|
| **Astra の勉強会の続き**／**営業協会の勉強会（10/21）の続き** | 上の再開の一言と同じ |
| **Astra スライドを直して：〇枚目を△△に** | `build_deck.py` の該当スライドを直す → `python3 build_deck.py` → `python3 deck_tools.py all` → `screenshots/overview/` で崩れを確認 → `review-notes.md` に記録 → 納品物を見せる |
| **Astra スライドを開いて** | `納品/第一部AI_Astraを味方にする夜_2026-10-21.html` を開く。URL が要るときはブラウザ用ページを出す |
| **セーブして** | ①Vault に最新ファイル ②GitHub の上記ブランチへコミット＋push（複製が無い PC では `git clone` → `git checkout claude/ai-benkyokai-20261021` から） ③作業ログに 1 行 ④この表を更新 |

### 別の PC で続きをやる手順

1. Dropbox の同期が終わっているか確認（`納品/` に PDF と HTML が見えれば最新）
2. Claude Code を Vault（または `03_PROJECTS/AI勉強会_20261021`）で開き、上の「再開の一言」を貼る
3. スライドを作り直す場合に要るもの：Python 3（Pillow・img2pdf）と Google Chrome。無ければ PDF と HTML をそのまま使う
4. Dropbox が使えないときだけ GitHub から：`git clone https://github.com/e-almighty/almighty.git` → `git checkout claude/ai-benkyokai-20261021` → `ai-benkyokai-20261021/`

## 判断メモ

- 「アストラ2」（9/25 の会話）は GPT-6.1 Astra を指していたと思われるが、9/28 に公開中止。勉強会で扱うのは現行の GPT-6 Astra。中止の件は第 5 章で 1 枚（28 枚目）
- 「AIスライド社員」の指名は HTML 版か画像版か曖昧だったため SHO に確認し、**AI HTMLスライド社員・明るい地** に確定（2026-10-20）
- 07 セミナー様式の CSS は無改変。明るい地は上書き CSS で実現（詳細は `review-notes.md` 判断①）
- 数字はすべて 2026-10-19 時点。公式と第三者を区別し、各スライド下部に出典行。架空の実績数字は入れない

## 関連

- [[03_PROJECTS/AI勉強会_20260826/PROJECT_OVERVIEW|AI勉強会（2026-08-26）]]（前回の 3 部構成の資料）
- [[03_PROJECTS/七転び八起き会HP/PROJECT_OVERVIEW|七転び八起き会HP]]（日本営業協会 関西支部）
- [[00_HOME/保管庫/保管庫_スライド|スライドの保管庫]] ／ [[00_HOME/保管庫/やりかけ一覧|やりかけ一覧]]
