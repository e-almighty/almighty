# オールマイティ Connect — 店舗間遠隔サポート（Google Meet連携 検証版）

店舗に置いたiPadから三宮の常駐スタッフを呼び出し、映像・音声はGoogle Meetで通話します。Daily等の通話APIは使いません。

- 店舗用（呼び出し側）: `/` — 主ボタンは「三宮を呼び出す」ひとつ
- 三宮用（受信側）: `/reception` — 着信時の主ボタンは「応答する」ひとつ
- 端末の識別は初回の端末設定だけ（`/settings/store`、`/settings/staff`）。三宮は iPad 1〜4 と業務端末 5 の番号を1台ずつ別に設定する

受信側は `/reception` を開くだけで受信待機と生存通知（heartbeat）が自動で始まります。「着信音を有効にする」は音だけの操作で、押す前でも着信表示と「応答する」は出ます。5台の受信端末すべてに着信し、先に「応答する」を押した1台が担当になり、他端末の着信は2秒以内に止まります。

## 画面の見かた（2026-10-02b 版）

画面上部に次の1行が常に出ます。実機で動かないときは、まずこの行を読んでください。

- `ログイン: xxx@example.com` — 呼び出し側と受付側で **同じアカウント** が出ていなければ、お互いを見つけられません（受付データはログインアカウントごとに分かれます）。
- `接続OK 10:23:45` — 2秒ごとの受信確認が成功した最終時刻。`接続エラー` のときは通信かログイン切れです。
- 受付側のみ `受付中の端末 1,2` — いま受信待機している三宮端末の番号。呼び出し側で「三宮で受付中です」が出るのは、この数が1以上のときです。

画面が真っ白にならないよう、表示に失敗した場合は「画面を表示できませんでした」とエラー文・ブラウザ名を出します。その文を三宮に伝えてもらってください。

## iPadでの使い方（短い手順）

1. どちらのiPadも **Safari** で開く。ホーム画面に追加したアイコンから開いてもSafariで開きます（ログインを共有するため、単独アプリ形式は使いません）。
2. 両方のiPadで、同じ検証用ChatGPTアカウントでログインする。所有者のパスワードをスタッフやお客様に配らないでください。
3. 受付iPad: `/reception` を開いたままにする。設定 > 画面表示と明るさ > 自動ロック を「なし」にし、Safariを前面に置く。最初に一度「着信音を有効にする」を押す。
4. 店舗iPad: `/` を開き「三宮を呼び出す」を押す。Google Meetのタブが開くので「参加」。カメラ・マイクの初回許可が必要。
5. 受付iPad: 「店舗から呼び出しです」と「応答する」が出たら押す。Meetのタブが開くので「参加」。入室許可を求められたら許可する。
6. 入力画面・料金・案内はこの受付画面のタブで送受信する。Meetのタブと切り替えて使う。
7. 終わったら双方でMeetから退出し、受付画面の「相談を終了」で内容を消去する。

iPadの画面ロック中や他アプリの使用中は着信を受けられません。Meetの参加状況や通話終了をアプリは検知しません。

## 対応するiPad

iPadOS 13〜15.3 のSafariには `crypto.randomUUID` 等がなく、以前の版では受付画面が真っ白のまま一切反応しませんでした（再現と修正済み。`lib/compat.ts`、`app/layout.tsx` のインライン互換スクリプト、ビルド対象の引き下げ）。iPadOS 12 以前は未対応です。画面装飾（Tailwind）はiPadOS 16.4未満で一部崩れる可能性がありますが機能は動きます。

## 開発と検証

Node.js 22.13以上、npm。

```bash
npm run install:ci
npm run build
# 空のローカルDBに1回だけ適用する（2回目以降は不要）
node node_modules/wrangler/bin/wrangler.js d1 execute DB --local --persist-to .wrangler/state --config dist/server/wrangler.json --file drizzle/0000_gifted_scrambler.sql
node node_modules/wrangler/bin/wrangler.js d1 execute DB --local --persist-to .wrangler/state --config dist/server/wrangler.json --file drizzle/0001_spooky_taskmaster.sql
npm run dev   # http://127.0.0.1:5173 （ローカル検証用。iPadから使う公開URLではない）
```

別ターミナルで、開発サーバーに対する検証:

```bash
node node_modules/typescript/bin/tsc --noEmit
node --test tests/ringer.test.mjs                                 # 着信音の停止・重複防止
node tests/handoff/test-meet-integration.mjs                       # 5台着信・先着1台・他端末解除・Meet URL・担当外拒否
node --experimental-strip-types tests/handoff/test-receiver-repair.mjs  # 音声待ちの打ち切り・通信タイムアウト・応答に音声許可不要
node tests/ring-group.mjs                                          # 業務端末5の応答で iPad1〜4 の着信解除
node tests/e2e-browser.mjs                                         # Chromiumで 呼び出し→両受信機に着信→先着応答→他端末停止→メッセージ→入力→終了
node tests/e2e-browser.mjs --legacy-ipad                           # 同上を crypto.randomUUID の無い古いiPad相当で
```

これらは 127.0.0.1 の検証DBだけを対象にし、架空の相談を作成・終了します。ブラウザ通しテストは meet.google.com への遷移先URLを確認し、Meetの入室そのものは行いません。

## 公開（OpenAI Sites）

公開先は既存のSitesプロジェクト（`.openai/hosting.json` の project_id）で、所有者のみの非公開設定のままにします。手順は `docs/引き継ぎ-2026-10-02.md` の第12節のとおり: このリポジトリのコミットから `npm run build` し、`dist` 全体（`dist/.openai/hosting.json` と `dist/.openai/drizzle/` を含む）を保存して公開します。D1マイグレーション 0000/0001 は適用済みのため書き換えません。`.wrangler` や `.env` は含めません。

## 未実装（本番配布前に必要）

会社共通の受付（アカウントをまたぐ共有）、スタッフ招待、店舗端末の登録・失効、相談ごとのMeetリンク発行、バックグラウンド着信通知、監査・定期削除。Microsoftのパスワード・認証コードは受け取りません。相談は作成2時間で期限切れとなり次回API呼び出し時に削除、受付終了で入力とメッセージを消去します。
