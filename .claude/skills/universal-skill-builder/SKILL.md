---
name: universal-skill-builder
description: 「スキル作って」「スキルを作成して」「〇〇をスキルにして」と言われたときに必ず使うスキル。どこでもスキル工房。ChatGPTのチャット・Codex・Claudeのチャット・Cowork・Claude Codeの5つ全部で同じように動くスキルを作り、Obsidian共通Vault（Almighty-AI-Brain）へ自動保存し、Git（e-almighty/almighty）にも反映する。スキルの新規作成・作り直し・全環境対応化の依頼はすべてここから始める。
---

# どこでもスキル工房（universal-skill-builder）

ユーザーが「スキル作って」と言ったら、**5つの環境すべてで使えるスキル**を作り、**Obsidianへ保存**し、**Gitへ反映**するところまで一気に進める。
いまどの環境で動いているか（Claude Code／Codex／Claudeのチャット／Cowork／ChatGPTのチャット）に関係なく、できあがるものは同じにする。

## できあがるもの（毎回この形）

スキル名は半角英小文字とハイフン（例 `customer-reply`）。1スキル＝1フォルダ。

```
<スキル名>/
├── SKILL.md            … 本体（5環境共通。これだけで動く）
├── agents/openai.yaml  … Codex用の表示名・呼び出し設定
└── CHATGPT.md          … ChatGPTに貼り付ける指示文（1,500文字以内）
```

置き場所：

| どこ | 置くもの | 役目 |
|---|---|---|
| Obsidian `05_SKILLS/<スキル名>/` | 3ファイル全部 | **正本**（ここを直したら他もそろえる） |
| Obsidian `.claude/skills/<スキル名>/SKILL.md` | SKILL.md と同じ中身 | Claude Code がVaultを開いたとき自動で使う |
| Obsidian `.agents/skills/<スキル名>/` | SKILL.md と agents/openai.yaml | Codex がVaultを開いたとき自動で使う |
| Obsidian `05_SKILLS/SKILLS_INDEX.md` | 1件追記 | 目次 |
| Git `e-almighty/almighty` の `.claude/skills/<スキル名>/` と `.agents/skills/<スキル名>/` | 上と同じ | リポジトリを開いたClaude Code・Codexでも使える |

Vault のルート：Dropbox の `/HIRATA/Obsidian/Almighty-AI-Brain/`（ローカルで開いているときはそのフォルダ）。
保存の細かな決まりは `05_SKILLS/00_SYSTEM/obsidian-skill-publisher/SKILL.md` に従う（上書き禁止・目次登録・UTF-8 など）。

## 手順

### 1. 聞き取り（短く）

足りないものだけ聞く。1回にまとめて聞き、わかっていることは聞き直さない。

- どんなときに使うか（ユーザーが何と言ったら動くか）
- 何をするか（手順）
- 何ができあがればよいか（ファイル・文章・リンクなど）
- 守る決まり・やってはいけないこと

### 2. 中身を作る

- **skill-creator が使える環境ではそれを使う**（Claude の `skill-creator`、Codex の `$skill-creator` など）。使えないときはこの手順のまま作る。
- 既存スキルと役目がかぶらないか `05_SKILLS/SKILLS_INDEX.md` で確認する。かぶるなら新規ではなく既存の改良を提案する。

### 3. 5環境で動く書き方にする（いちばん大事）

SKILL.md は次の決まりで書く。これを守れば Claude（チャット・Cowork・Code）と Codex がそのまま読め、ChatGPT にも移せる。

1. 先頭は次の2項目だけ（他の項目を足さない）
   ```
   ---
   name: <スキル名>
   description: <いつ使うか＋何をするか。ユーザーが言いそうな言葉を「」で3つ以上入れる。1,024文字以内>
   ---
   ```
2. 本文は日本語。**それだけ読めば動く**ように書く（「上の会話のとおり」など、その場の会話を前提にしない）
3. 特定の環境だけの道具名（Bash、Read、MCPのツール名など）に頼らない。書くなら「ファイルを直接書ける環境では〜／書けない環境では〜」と両方書く
4. パソコン固有の絶対パス（`C:\Users\...` など）を書かない。Vault内は相対パス
5. 本文は500行以内。長い資料は `references/` に分けて「必要なときに読む」と書く
6. 本文に必ず入れる見出し：目的／使う場面／手順／できあがるもの／確認すること／やってはいけないこと

`agents/openai.yaml` はこの形：
```yaml
interface:
  display_name: "<日本語の名前>"
  short_description: "<一言説明>"
  default_prompt: "$<スキル名> を使って、<何をするか>してください。"

policy:
  allow_implicit_invocation: true
```

`CHATGPT.md` は SKILL.md を **1,500文字以内** に縮めた指示文（ChatGPTのカスタム指示・プロジェクト指示の上限に合わせる）。冒頭に「ユーザーが『〇〇』と言ったら次の手順で進める」と書く。

### 4. Obsidianへ保存する

いまの環境でできる方法を上から順に選ぶ。

**A. ファイルを直接書ける（Claude Code・Codex でVaultかDropboxフォルダを開いている）**
1. 上の表のとおり全部の場所に書く
2. `05_SKILLS/SKILLS_INDEX.md` の「## 登録済みスキル」の最後に追記する（既存の書き方に合わせる）
   ```
   - [[05_SKILLS/<スキル名>/SKILL|<スキル名>（<日本語名>）]]
     - <一言説明>
     - 保存場所：`05_SKILLS/<スキル名>/SKILL.md`
     - Claude Code入口：`.claude/skills/<スキル名>/SKILL.md`
     - Codex入口：`.agents/skills/<スキル名>/SKILL.md`
     - 対応環境：Claude Code／Codex／Claudeチャット／Cowork／ChatGPT
     - 登録日：<YYYY-MM-DD>
   ```
3. 次の「目次待ち」があれば、それも目次に取り込んでから消す

**B. Dropbox コネクタだけ使える（Claudeのチャット・Cowork・ChatGPTのチャット）**
1. Dropbox のフォルダ作成・ファイル作成で上の表の場所に作る（パスは `/HIRATA/Obsidian/Almighty-AI-Brain/` から始める）
2. コネクタは既存ファイルの書き換えができないので、目次には直接書かない。代わりに
   `05_SKILLS/00_SYSTEM/universal-skill-builder/目次待ち/<YYYY-MM-DD>_<スキル名>.md`
   に、上の目次1件分の文を保存する（次に A の環境で動いたときに取り込まれる）
3. 同じ名前のファイルがすでにあったら作らずに止まり、ユーザーに確認する

**C. どちらもできない**
3ファイルの中身を、保存先のパス付きでチャットにそのまま出し「この場所に置いてください」と案内する。

### 5. Git へ反映する

- **Git が使える環境（Claude Code・Codex）**：`e-almighty/almighty` の `.claude/skills/<スキル名>/` と `.agents/skills/<スキル名>/` に同じファイルを置き、
  「スキル追加：<スキル名>（<日本語名>）」のようなメッセージでコミットして、作業ブランチへ push する（指定ブランチがあればそれに従う。勝手にプルリクエストは作らない）
- **GitHub コネクタだけ使える環境**：コネクタでファイルを作る
- **どちらもできない**：Git はやらずに、目次待ちファイルに「Git未反映」と1行書いておく（次に A の環境で動いたときに反映する）

### 6. Claude のチャット用 zip（作れる環境だけ）

ファイルを作れる環境では `<スキル名>.zip`（中身は `<スキル名>/SKILL.md` と `agents/`）も作り、ユーザーに渡す。
Claude のチャット・Cowork には、この zip を 設定 → 機能 → スキル からアップロードすると入る。
Dropbox コネクタは zip を保存できないので、zip はチャットで渡すだけでよい。

### 7. 報告（日本語で短く）

- スキル名と、何ができるか一言
- 保存した場所（Obsidian・Git それぞれ）。保存できなかったところは正直に書く
- 環境ごとの使い始め方（下の表から必要な行だけ）

| 環境 | 使い始め方 |
|---|---|
| Claude Code | Vault か almighty リポジトリを開けば自動で使える |
| Codex | Vault か almighty リポジトリを開けば自動で使える（`$<スキル名>` でも呼べる） |
| Claude のチャット・Cowork | zip を 設定 → 機能 → スキル でアップロード（1回だけ） |
| ChatGPT のチャット | `CHATGPT.md` の文を、使いたいプロジェクトの「指示」に貼る |

## 確認すること（報告の前に）

- [ ] SKILL.md の先頭が `name` と `description` の2項目だけ
- [ ] `name` がフォルダ名と同じ、半角英小文字とハイフンだけ
- [ ] description に、ユーザーが言いそうな言葉が入っている
- [ ] 本文がその場の会話を知らなくても読める
- [ ] CHATGPT.md が1,500文字以内
- [ ] 正本と入口（.claude・.agents・Git）の中身がそろっている
- [ ] 目次に登録した（または目次待ちに置いた）

## やってはいけないこと

- 同じ名前の既存スキルを確認なしで上書き・削除する
- 保存できていないのに「保存しました」と報告する
- 会話の貼り付けだけのスキルを作る
- パスワード・合言葉・個人情報をスキルに書く
- 1つのスキルに目的を詰め込みすぎる（分けたほうがよければ提案する）
