# almighty — 共通ルール

このリポジトリは、株式会社オールマイティ（代表 SHO）の AI 共通頭脳「Almighty-AI-Brain」の Git 側の写しです。
正本は Obsidian Vault（Dropbox の `/HIRATA/Obsidian/Almighty-AI-Brain`）。
このファイルは、Vault が手元に無い環境（claude.ai/code のクラウド環境など）でも頭脳につながるための入口です。

## 必ず日本語で答える

## 頭脳（Almighty-AI-Brain）に最初につなぐ

仕事の話が始まったら、作業の前に次の2つを読む。

- `CLAUDE.md`（Vault 直下。作業ルール）
- `01_MEMORY/MEMORY.md`（会社情報と長期記憶の索引）

関係しそうな個別ノート（`01_MEMORY/` の中）があれば、それも読む。

### 読み方（上から順に試す）

1. **Vault がディスク上にある**（パソコン上の Claude Code、または Remote Control でそのフォルダを開いている）→ そのファイルを直接読む
2. **ディスク上に無い**（claude.ai/code のクラウド環境。このリポジトリだけがクローンされている）→ Dropbox コネクタで `/HIRATA/Obsidian/Almighty-AI-Brain/` の下のファイルを読む
3. **どちらもできない** → 最初にそう伝える。頭脳を読まずに推測で答えない

### 動作確認

「会社の代表者の呼称は？」と聞かれて **SHO** と答えられれば、頭脳につながっている。

## 保管庫（作ったものの目次）

- アプリ・スライド・PDF・画像・動画を探す・開く・続きをするよう頼まれたら、フォルダを探し回る前に `00_HOME/保管庫/保管庫_入口.md` を読む
- 合言葉（保管庫を見せて／保管庫の○○を開いて／セーブして／反映して／保管庫に載せて など）の意味は `00_HOME/保管庫/AIへの頼み方カード.md` にある
- 「玄関開いて」「玄関出して」→ 保管庫の玄関 `00_HOME/保管庫/アプリ玄関.html` を開く。クラウド環境では Dropbox コネクタでこのファイルを探し、「Dropboxで開く」リンクを出す。claude.ai の Artifact「アプリ玄関」（名刺金庫とプロンプト工房だけのページ）とは別物
- 完成したものは `00_HOME/保管庫/保管庫の玄関_載せ方.md` の手順で玄関へ載せる。ファイルを直接書けない環境では「保管庫に載せますか」と聞き、手順を伝える

## 記憶と成果物の置き場

- 正本は常に Vault。チャットのメモリ、Claude Code の自動メモリ、このリポジトリに記憶を溜めない
- 覚えておくべき新しい事実・決定は `09_INBOX/YYYY-MM-DD_内容.md` に新しいノートとして保存する。先頭に type / status / tags / created / updated のプロパティを付ける（規約は `02_RULES/OBSIDIAN_NOTE_RULES.md`）
- Dropbox コネクタは既存ファイルを書き換えられない。既存ノートの修正が必要なときは「パソコンの Claude Code で直してください」と SHO に伝える
- 成果物を作ったら、チャットの中だけに置かず、Vault に入れるかを SHO に聞く
- 頭脳の内容とチャット側の記憶が食い違ったら、頭脳が正しい
- パスワード・APIキー・カード情報は保存しない

## 保管庫（Obsidian Vault）の場所は1つだけ

Almighty-AI-Brain の正本は Dropbox の **`/HIRATA/Obsidian/Almighty-AI-Brain`** のみ。
スキル・メモリ・ルールを保存するときは必ずこの配下に置く。
`/AIフォルダ/Almighty-AI-Brain` など別の場所に新しく作らない
（2026-10-10 に別の AI が `/AIフォルダ/` に作ってしまい、10-13 に統合済み）。

## スキル

- `.claude/skills/` と `.agents/skills/` は Vault の `05_SKILLS/` の写し。正本は Vault
- 「スキル作って」と言われたら `.claude/skills/universal-skill-builder/SKILL.md`（どこでもスキル工房）の手順に従う

## Cloudflare（Web 公開）の準備

- Cloudflare に関わる作業（Web ページの公開、Pages、Workers、DNS など）が始まったら、クラウド環境（claude.ai/code）では最初に次の2つを Bash で実行して、Cloudflare 公式プラグイン（スキル19本＋MCPサーバー1つ）を入れる。クラウドの作業場は会話ごとに消えるので、毎回入れ直す。SHO に操作を頼まない
  - `claude plugin marketplace add cloudflare/skills`
  - `claude plugin install cloudflare@cloudflare`
  - 確認：`claude plugin list` に `cloudflare@cloudflare` が `enabled` で出る
- クラウド環境では `/plugin` のスラッシュコマンドは使えない（Claude Code 公式ドキュメントで確認済み・2026-10-30）。SHO に `/plugin …` を貼り付けるよう頼まない。黒い画面（ターミナル）の操作も頼まない
- MCPサーバー（`https://mcp.cloudflare.com/mcp`）はクラウド環境ではネットワーク制限で接続できず、ブラウザでのログインもできない。Cloudflare の操作は Workers（Static Assets）の GitHub 連携（Workers Builds。本線ブランチに push すると自動公開）を基本にする。公開済み：パソコン診断ナビ `pc-shindan-navi/` → https://pc-shindan-navi.amkobe0730.workers.dev（2026-10-30。Root directory `/pc-shindan-navi`、Deploy command `npx wrangler deploy`）。API トークンが必要になったら環境のシークレットに入れてもらい、チャットには貼らせない
- お金がかかる操作、有料プランへの変更、DNS の変更、何かの削除が要るときは、その前に止まって SHO に確認する

## SHO と進めるときの決まり

- SHO は音声入力で話すので誤変換が混じる。意味を推定したら「こう理解しました」と返してから進める
- 設定や環境づくりは1回に1つの操作だけ案内し、押す場所は画面の場所で言う
- 事実と推測を分け、確かめていないことは「未確認」と書く

## モデル案内ルール（最優先）

ユーザーはモデル（Fable / Opus / Sonnet / Haiku）の使い分けが分からない。
Claude が先回りして案内する。

### いつ案内するか
1. **会話の最初の返答**で必ず1回。
2. **作業の種類が変わったとき**（例：雑談・相談 → ホームページ制作 / アプリ開発 / スライド作成 / スキル作成、またはその逆）に必ず1回。
3. 同じ種類の作業が続いている間は繰り返さない。

### 案内の書き方
返答の**冒頭**に、次の形式の1〜2行を置く。本文より前に出す。

> 💡 **モデル案内**：この作業（○○）は **Opus 5.5** がおすすめです。今は Fable 5.1 なので `/model claude-opus-5-5` で切り替えると、速くて利用枠も節約できます。

- 今のモデルが既に最適なら「今の ○○ のままで大丈夫です」と一言だけ。
- 切り替えの操作方法を必ず添える（Claude Code なら `/model <モデルID>`、claude.ai チャットなら画面上部のモデル選択）。
- Claude 自身はモデルを切り替えられない。切り替えるのはユーザー。

### 使い分けの基準

| 作業の種類 | おすすめ | モデルID |
|---|---|---|
| 会話・相談・質問・雑談・要約・メール文・Obsidianメモ整理 | **Sonnet 5.5**（軽い話）／ **Opus 5.5**（判断が要る相談） | `claude-sonnet-5-5` / `claude-opus-5-5` |
| ホームページ制作・アプリ開発・スライド作成・スキル作成・AI社員の本業 | **Opus 5.5** | `claude-opus-5-5` |
| 既にできた物の細かい修正（文言、色、小さなバグ） | **Sonnet 5.5** | `claude-sonnet-5-5` |
| 大量の仕分け・分類・定型処理 | **Haiku 5.5** | `claude-haiku-5-5` |
| 事業戦略の判断・複雑なシステム全体設計・難しい不具合の原因究明 | **Fable 5.1**（ここ一番だけ。終わったら Opus に戻すよう案内） | `claude-fable-5-1` |

迷ったら **Opus 5.5**。Fable 5.1 は時間がかかり利用枠の消費も大きいので、
チャットや普段の制作作業で Fable が選ばれていたら、必ず Opus への切り替えを提案する。
固定の消費倍率でプラン使用量を断定しない（2026-10-13 の長期記憶の方針）。

### サブエージェント（部下）を使うとき
Claude Code で Agent を起動する場合は、上の表に従って `model` を指定する
（分類・集計は `haiku`、下書き・小修正は `sonnet`、設計・制作は `opus`、難しい判断だけ `fable`）。
ユーザーの切り替えを待たず、Claude 側で自動的に振り分ける。
