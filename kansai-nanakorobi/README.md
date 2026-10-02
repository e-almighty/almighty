# 七転び八起会（日本営業協会 関西支部）ホームページ

日本営業協会（https://j-sa.jp/ ）の関西支部「七転び八起会」の公式ページです。
HTML・CSS・JS だけで動く 1 ページ構成なので、サーバーもビルドも要りません。

## フォルダの中身

| ファイル | 役割 |
|---|---|
| `index.html` | ページの骨組み（章の並び） |
| `site-data.js` | **文章・連絡先・会員・予定・版数** ← 直すのはほぼここだけ |
| `assets/css/style.css` | 見た目（色・文字・余白） |
| `assets/js/main.js` | site-data.js の内容を画面に流し込む仕組み |
| `assets/images/` | だるま・しるし（SVG） |
| `CHANGELOG.md` | 版ごとの変更の記録 |

## 直し方（版を上げる手順）

1. `site-data.js` を開いて文章や連絡先を直す
2. 同じファイルの `version` の数字を 1 つ上げ `updated` に日付を入れる
3. `CHANGELOG.md` に 1 行足す
4. git でコミット（例 `git commit -am "版5：会員を2社追加"`）してタグを打つ（例 `git tag nanakorobi-v5`）

画面の右下に「版 N」と出るので、どの版を見ているかすぐ分かります。
前の版に戻したいときは `git checkout nanakorobi-v3 -- kansai-nanakorobi/` のようにタグから戻せます。

## まだ決まっていないこと（「（仮）」の項目）

- 会費（site-data.js の `join.fee`）… 月額5,000円は打ち合わせでの話。要確認
- 事務局の名前・住所・電話（`contact`）… いまはオールマイティ本店を入れています
- 発足日（`org.founded`）… 本部イベント一覧の「2025年1月11日 関西支部発足＆交流会」を入れています
- 目標会員数 12名（`stats`）
- 10月・11月・2月の予定（`events`）… 会場・日付
- 支部長・会長の名前と挨拶文 … まだ章を作っていません（決まったら足します）
- 公式LINE・メールアドレス（`contact.line` / `contact.email`）… 入れると自動で表示されます
- お問い合わせフォームの送信先 … いまは「本文をコピー」方式。相談ナビと同じ Google スプレッドシート窓口にもつなげられます
- 本部（会長）への独自ホームページの承認

## 公開のしかた

- GitHub Pages：このリポジトリで Pages を有効にして `/almighty/kansai-nanakorobi/` を開く
- 独自ドメイン（年間1,500円ほど）を取ったら Pages のカスタムドメインに設定
- 公開が決まったら `index.html` の `<meta name="robots" content="noindex,nofollow">` の行を消す
