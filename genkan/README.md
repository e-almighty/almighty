# 保管庫の玄関（インターネット版）

Vault の `00_HOME/保管庫/アプリ玄関.html` を、Cloudflare Workers（Static Assets）でインターネットに出すためのフォルダです。
どの端末からでも、ボタン・QR コード・検索が動く形で開けます。

- 公開 URL（予定）：https://almighty-genkan.amkobe0730.workers.dev
- 検索サイトには載せない（`noindex`・`robots.txt`・`X-Robots-Tag`）。URL を知っている人は開ける
- 中身の正本は Vault の `00_HOME/保管庫/玄関データ.json`。ここにある `玄関データ.json` はその写し

## しくみ

| ファイル | 役割 |
|---|---|
| `玄関データ.json` | 玄関に並べる中身（Vault からの写し） |
| `build.mjs` | `玄関データ.json` から `public/index.html` を作る |
| `public/` | 公開されるもの（Cloudflare はこの中だけを出す） |
| `wrangler.jsonc` | Cloudflare の設定（名前 `almighty-genkan`、公開フォルダ `public`） |

- パソコンの中のファイル（スライド・PDF・画像・動画）は、**Dropbox の画面で開くボタン** になる。会社の Dropbox アカウントでログインしている端末だけが開ける。ファイルの中身はインターネットに出ない（出るのは名前と説明だけ）
- HTML のスライドは Dropbox の画面では文字しか出ないので、PDF や PowerPoint のボタンを先に並べている
- `public/files/` に Vault と同じ場所のファイルを置くと、そのボタンは Dropbox ではなく直接開くようになり、表紙の画像も出る（下の「完全版にする」）

## 中身を更新する（玄関に何か載せたあと）

1. Vault の `00_HOME/保管庫/玄関データ.json` を、このフォルダの `玄関データ.json` に写す（クラウドの Claude Code なら Dropbox 連携で読んで書く）
2. このフォルダで `npm install`（初回だけ）→ `node build.mjs`
3. 変更を GitHub に保存して PR を作る → SHO が「Merge pull request」→「Confirm merge」
4. Cloudflare が自動で公開し直す（1〜2分）

## 完全版にする（パソコンの Claude Code で。未実施）

クラウド環境からは Dropbox のファイル本体を取り出せないため、最初の版は Dropbox で開く形にした。
パソコンなら Vault がディスク上にあるので、本体を `public/files/` に写せる。

- 写すのは `玄関データ.json` の `file`・`thumb`・`download` に出てくるものだけ。Vault と同じ相対パスで置く（例 `public/files/10_OUTPUTS/SLIDES/PC.pptx`）
- Cloudflare の無料プランは 1ファイル 25MB まで。超えるものは Dropbox のままにする
- **社内向けの資料（損益計算書・実績報告・会議の要約など）は、写すとインターネットに出る。** 写す前に SHO に選んでもらうか、Cloudflare Access（メールでログインした人だけ見られる仕組み）を先に付ける

## Cloudflare 側の設定（最初の1回だけ・SHO の画面で）

Workers & Pages →「アプリケーションを作成」→「リポジトリをインポート」（Import a repository）で `e-almighty/almighty` を選び、次のように入れる。

| 項目 | 入れる値 |
|---|---|
| プロジェクト名（Project name） | `almighty-genkan` |
| ビルドコマンド（Build command） | 空のまま |
| デプロイコマンド（Deploy command） | `npx wrangler deploy` |
| ルートディレクトリ（Root directory、詳細設定の中） | `/genkan` |

本線ブランチ（いまは `claude/dazzling-keller-t5or5n`）に保存されるたびに自動で公開し直される。パソコン診断ナビ（`pc-shindan-navi/`）と同じつなぎ方。
