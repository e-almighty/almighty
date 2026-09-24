// 相談ナビの受付窓口（Apps Script）に 診断ナビの記録も受け取らせるための追加分
// 使い方：相談ナビの窓口の doPost の いちばん最初（合言葉の確認のすぐあと）に 次の3行を足す
//
//   const r = body.record || {};
//   if (r.app === '診断ナビ') return saveShindan(r);
//
// そして下の関数をファイルの末尾に貼り付ける　診断ナビのiPadの裏メニューには 相談ナビと同じURLと合言葉を入れる
// 「診断ナビ」シートが無ければ自動で作る　同じお客様（同じID）は上書き　売上の列は 受付1件＝基本診断費（2,200円）

const SHINDAN_HEADER = ['ID', '日時', 'iPad', '残したいデータ', 'Windowsのパスワード', '心当たり', 'お困りの症状', '基本診断費', '受信日時'];

function saveShindan(r) {
  if (!r.id) return reply({ ok: false, error: '記録のIDがありません' });
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('診断ナビ');
  if (!sheet) { sheet = ss.insertSheet('診断ナビ'); sheet.appendRow(SHINDAN_HEADER); }
  const row = [r.id, r.at, r.device, r.data, r.pcpass, r.change, r.symptom, r.fee || 2200, new Date()].map(v => v == null ? '' : String(v));
  const last = sheet.getLastRow();
  const ids = last > 1 ? sheet.getRange(2, 1, last - 1, 1).getValues().map(v => String(v[0])) : [];
  const i = ids.indexOf(String(r.id));
  if (i >= 0) sheet.getRange(i + 2, 1, 1, row.length).setValues([row]);
  else sheet.appendRow(row);
  return reply({ ok: true });
}

// 集計の例（スプレッドシートのセルに書く）
//   受付件数： =COUNTA('診断ナビ'!A2:A)
//   基本診断費の合計： =SUM('診断ナビ'!H2:H)
//   今月の件数： =COUNTIFS('診断ナビ'!B2:B,">="&TEXT(EOMONTH(TODAY(),-1)+1,"yyyy/mm/dd"))
