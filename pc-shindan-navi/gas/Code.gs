// パソコン診断ナビ 受付窓口（Google Apps Script）
// iPadから送られてくる回答を Googleスプレッドシートに1人1行で集める
//
// 用意のしかた
// 1. Googleスプレッドシートを新しく作る（名前は「パソコン診断ナビ 集計」など）
// 2. 拡張機能 → Apps Script を開き このファイルの中身をすべて貼り付ける
// 3. 下の PASS を お店で決めた合言葉に書き換えて保存する
// 4. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
//      次のユーザーとして実行：自分　　アクセスできるユーザー：全員
// 5. 表示された「ウェブアプリのURL」（…/exec で終わる）を iPadの裏メニューの「送信先URL」に入れ 合言葉も入れて保存する
//    （app.js の DEFAULT_URL に入れておくと iPadごとの入力がいらない）
// 合言葉が合わない送信はすべて断る　同じお客様（同じID）の記録は上書きされる

const PASS = 'ここに合言葉を入れる';
const HEADER = ['ID', '日時', 'iPad', 'お困りの内容', '次のステップ', '残したいデータ', '控え', 'Windowsのパスワード', '心当たり', '回答の記録', '最後の選択', '受付', '受付した次のステップ', '受信日時'];

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    const body = JSON.parse(e.postData.contents);
    if (!PASS || body.pass !== PASS) return reply({ ok: false, error: '合言葉が違います' });
    const r = body.record || {};
    if (!r.id) return reply({ ok: false, error: '記録のIDがありません' });
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    if (sheet.getLastRow() === 0) sheet.appendRow(HEADER);
    const row = [r.id, r.at, r.device, r.cat, r.next, r.data, r.backup, r.pcpass, r.change, r.answers, r.consult, r.outcome, r.outcomeNext, new Date()].map(v => v == null ? '' : String(v));
    const last = sheet.getLastRow();
    const ids = last > 1 ? sheet.getRange(2, 1, last - 1, 1).getValues().map(v => String(v[0])) : [];
    const i = ids.indexOf(String(r.id));
    if (i >= 0) sheet.getRange(i + 2, 1, 1, row.length).setValues([row]);
    else sheet.appendRow(row);
    return reply({ ok: true });
  } catch (err) {
    return reply({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// 動作確認用：ブラウザでURLを開くと「受付窓口は動いています」と出る
function doGet() {
  return ContentService.createTextOutput('パソコン診断ナビの受付窓口は動いています');
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
