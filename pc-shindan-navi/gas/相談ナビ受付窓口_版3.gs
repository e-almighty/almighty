/**
 * パソコン相談ナビ 集計の受付窓口（Google Apps Script）
 *
 * 役割：複数台のiPad（2026-09-20時点で4台）から届いた回答を このスプレッドシートの「回答」シートに1行ずつ書き込む
 *       同じお客様（同じID）の記録がもう一度届いたら 行を増やさず上書きする
 *       「集計」シートに 質問ごとの はい／いいえ の件数を自動で出す
 *       版3から：パソコン診断ナビの受付も同じ窓口で受け取り 「診断ナビ」シートに書き込む（受付1件＝基本診断費2,200円）
 *
 * 使い方（くわしくは PROJECT_OVERVIEW.md の「集計の受付窓口を作る手順」）
 *   1. Googleスプレッドシートを新規作成する
 *   2. 拡張機能 → Apps Script を開き このファイルの中身をすべて貼り付ける
 *   3. 合言葉は別ファイル「合言葉.gs」に書く（gas/合言葉.gs のひな形を貼って書き換える）
 *      このファイル（コード.gs）には合言葉を書かないので あとで入れ替えても合言葉は消えない
 *   4. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *      実行するユーザー「自分」 アクセスできるユーザー「全員」でデプロイする
 *   5. 表示されたURL（https://script.google.com/macros/s/…/exec）と合言葉を
 *      各iPadの裏メニュー「このiPadの設定」に入力する（診断ナビのiPadにも同じURLと合言葉を入れる）
 *
 * 注意：個人を特定する情報は送られてこない（はい／いいえ と日時とiPadの名前 成約の結果だけ）
 *
 * 版2（2026-09-21）：「成約」「成約したパック」の列を追加／合言葉を別ファイルに分離
 * 版3（2026-09-24）：診断ナビの受付を「診断ナビ」シートに書き込む／「診断ナビ集計」シートを追加
 * プログラムを入れ替えたあとは デプロイ → デプロイを管理 → 鉛筆 → 新バージョン → デプロイ（URLは変わらない）
 */

const SHEET_ANSWERS = '回答';
const SHEET_SUMMARY = '集計';
const SHEET_SHINDAN = '診断ナビ';
const SHEET_SHINDAN_SUMMARY = '診断ナビ集計';
const QUESTION_COUNT = 10;
const SHINDAN_FEE = 2200; // 基本診断費（診断ナビの記録に金額が付いていないときに使う）

const HEAD = ['ID', '日時', 'iPad']
  .concat(Array.from({ length: QUESTION_COUNT }, (_, i) => (i + 1) + '問目'))
  .concat(['3問目の種類', 'おすすめパック', '最後の選択', '受信日時', '成約', '成約したパック']);

const HEAD_SHINDAN = ['ID', '日時', 'iPad', '残したいデータ', 'Windowsのパスワード', '心当たり', 'お困りの症状', '基本診断費', '受信日時'];

/** 合言葉は別ファイル「合言葉.gs」の PASSPHRASE から読む */
function passphrase_() {
  return (typeof PASSPHRASE === 'undefined') ? '' : String(PASSPHRASE);
}

function doGet() {
  return json_({ ok: true, message: 'パソコン相談ナビ・診断ナビの受付窓口です' });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const body = JSON.parse(e.postData.contents);
    const pass = passphrase_();
    if (!pass || pass === 'ここを自分の合言葉に変える') return json_({ ok: false, error: '受付窓口の合言葉がまだ設定されていません' });
    if (body.pass !== pass) return json_({ ok: false, error: '合言葉が違います' });
    const r = body.record;
    if (!r || !r.id) return json_({ ok: false, error: '記録の形が正しくありません' });

    // 診断ナビからの記録は「診断ナビ」シートへ
    if (r.app === '診断ナビ') {
      lock.waitLock(20000);
      saveShindan_(r);
      return json_({ ok: true });
    }

    if (!Array.isArray(r.answers)) return json_({ ok: false, error: '記録の形が正しくありません' });
    lock.waitLock(20000);
    const sheet = prepare_();
    const row = [String(r.id), String(r.at || ''), String(r.device || '')]
      .concat(Array.from({ length: QUESTION_COUNT }, (_, i) => String(r.answers[i] || '')))
      .concat([String(r.q3 || ''), String(r.pack || ''), String(r.consult || ''), new Date(), String(r.outcome || '未記入'), String(r.outcomePack || '')]);
    writeRow_(sheet, r.id, row);
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    try { lock.releaseLock(); } catch (ignore) {}
  }
}

/** 同じIDの行があれば上書き 無ければ末尾に追加 */
function writeRow_(sheet, id, row) {
  const last = sheet.getLastRow();
  let target = last + 1;
  if (last >= 2) {
    const ids = sheet.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < ids.length; i++) {
      if (String(ids[i][0]) === String(id)) { target = i + 2; break; }
    }
  }
  sheet.getRange(target, 1, 1, row.length).setValues([row]);
}

/** 診断ナビの記録を「診断ナビ」シートに書く（引き継ぎ画面まで進んだ1件＝基本診断費1回分） */
function saveShindan_(r) {
  const sheet = prepareShindan_();
  const fee = Number(r.fee) > 0 ? Number(r.fee) : SHINDAN_FEE;
  const row = [String(r.id), String(r.at || ''), String(r.device || ''), String(r.data || ''), String(r.pcpass || ''), String(r.change || ''), String(r.symptom || ''), fee, new Date()];
  writeRow_(sheet, r.id, row);
}

/** 「回答」「集計」シートが無ければ作る */
function prepare_() {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  let answers = book.getSheetByName(SHEET_ANSWERS);
  if (!answers) {
    answers = book.insertSheet(SHEET_ANSWERS);
    answers.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold');
    answers.setFrozenRows(1);
    answers.getRange('A:B').setNumberFormat('@');
  }
  // 見出しは毎回そろえる（あとから列を足したときも自動で見出しが入る）
  answers.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold');
  if (!book.getSheetByName(SHEET_SUMMARY)) {
    const summary = book.insertSheet(SHEET_SUMMARY);
    const rows = [['問', 'はい（1問目はご自身）', 'いいえ（1問目はスタッフ）', '回答数', 'はいの割合']];
    for (let i = 0; i < QUESTION_COUNT; i++) {
      const col = columnLetter_(4 + i); // 1問目はD列
      const yes = i === 0 ? 'ご自身' : 'はい';
      const no = i === 0 ? 'スタッフ' : 'いいえ';
      const n = i + 2;
      rows.push([
        (i + 1) + '問目',
        '=COUNTIF(' + SHEET_ANSWERS + '!' + col + ':' + col + ',"' + yes + '")',
        '=COUNTIF(' + SHEET_ANSWERS + '!' + col + ':' + col + ',"' + no + '")',
        '=B' + n + '+C' + n,
        '=IF(D' + n + '=0,"",B' + n + '/D' + n + ')'
      ]);
    }
    summary.getRange(1, 1, rows.length, 5).setValues(rows);
    summary.getRange(1, 1, 1, 5).setFontWeight('bold');
    summary.getRange(2, 5, QUESTION_COUNT, 1).setNumberFormat('0%');

    const packCol = columnLetter_(4 + QUESTION_COUNT + 1);
    const consultCol = columnLetter_(4 + QUESTION_COUNT + 2);
    const extra = [
      ['おすすめパック', '件数'],
      ['安心訪問バックアップパック', '=COUNTIF(' + SHEET_ANSWERS + '!' + packCol + ':' + packCol + ',A' + (QUESTION_COUNT + 5) + ')'],
      ['安心バックアップパック', '=COUNTIF(' + SHEET_ANSWERS + '!' + packCol + ':' + packCol + ',A' + (QUESTION_COUNT + 6) + ')'],
      ['スタンダードパック', '=COUNTIF(' + SHEET_ANSWERS + '!' + packCol + ':' + packCol + ',A' + (QUESTION_COUNT + 7) + ')'],
      ['', ''],
      ['最後の選択', '件数'],
      ['相談したい', '=COUNTIF(' + SHEET_ANSWERS + '!' + consultCol + ':' + consultCol + ',A' + (QUESTION_COUNT + 10) + ')'],
      ['保留', '=COUNTIF(' + SHEET_ANSWERS + '!' + consultCol + ':' + consultCol + ',A' + (QUESTION_COUNT + 11) + ')'],
      ['未選択', '=COUNTIF(' + SHEET_ANSWERS + '!' + consultCol + ':' + consultCol + ',A' + (QUESTION_COUNT + 12) + ')']
    ];
    summary.getRange(QUESTION_COUNT + 4, 1, extra.length, 2).setValues(extra);
    summary.getRange(QUESTION_COUNT + 4, 1, 1, 2).setFontWeight('bold');
    summary.getRange(QUESTION_COUNT + 9, 1, 1, 2).setFontWeight('bold');
    summary.setColumnWidth(1, 220);
  }
  return answers;
}

/** 「診断ナビ」「診断ナビ集計」シートが無ければ作る */
function prepareShindan_() {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = book.getSheetByName(SHEET_SHINDAN);
  if (!sheet) {
    sheet = book.insertSheet(SHEET_SHINDAN);
    sheet.setFrozenRows(1);
    sheet.getRange('A:B').setNumberFormat('@');
    sheet.getRange('H:H').setNumberFormat('#,##0');
  }
  sheet.getRange(1, 1, 1, HEAD_SHINDAN.length).setValues([HEAD_SHINDAN]).setFontWeight('bold');
  if (!book.getSheetByName(SHEET_SHINDAN_SUMMARY)) {
    const s = book.insertSheet(SHEET_SHINDAN_SUMMARY);
    const S = SHEET_SHINDAN;
    const rows = [
      ['診断ナビの受付', ''],
      ['受付件数（累計）', '=COUNTA(' + S + '!A2:A)'],
      ['基本診断費の合計（累計）', '=SUM(' + S + '!H2:H)'],
      ['今月の受付件数', '=COUNTIFS(' + S + '!B2:B,">="&TEXT(EOMONTH(TODAY(),-1)+1,"yyyy/mm/dd"))'],
      ['今月の基本診断費', '=B4*' + SHINDAN_FEE],
      ['', ''],
      ['お困りの症状', '件数'],
      ['電源が入らない', '=COUNTIF(' + S + '!G:G,A8)'],
      ['Windowsが起動しない', '=COUNTIF(' + S + '!G:G,A9)'],
      ['インターネットにつながらない', '=COUNTIF(' + S + '!G:G,A10)'],
      ['メールができない', '=COUNTIF(' + S + '!G:G,A11)'],
      ['Windowsでエラーが出る', '=COUNTIF(' + S + '!G:G,A12)'],
      ['ウイルス感染・警告画面', '=COUNTIF(' + S + '!G:G,A13)'],
      ['動作が遅い・固まる', '=COUNTIF(' + S + '!G:G,A14)'],
      ['その他のご相談', '=COUNTIF(' + S + '!G:G,A15)'],
      ['', ''],
      ['質問', 'はい'],
      ['残したいデータ', '=COUNTIF(' + S + '!D:D,"はい")'],
      ['Windowsのパスワード', '=COUNTIF(' + S + '!E:E,"はい")'],
      ['心当たり', '=COUNTIF(' + S + '!F:F,"はい")']
    ];
    s.getRange(1, 1, rows.length, 2).setValues(rows);
    [1, 7, 17].forEach(n => s.getRange(n, 1, 1, 2).setFontWeight('bold'));
    s.getRange('B3').setNumberFormat('#,##0"円"');
    s.getRange('B5').setNumberFormat('#,##0"円"');
    s.setColumnWidth(1, 240);
  }
  return sheet;
}

function columnLetter_(n) {
  let s = '';
  while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = (n - m - 1) / 26; }
  return s;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
