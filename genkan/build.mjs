// 保管庫の玄関（インターネット版）を 玄関データ.json から作る
// 使い方：このフォルダで  node build.mjs   → public/index.html ができる
// 元は Vault の 00_HOME/保管庫/玄関を作る.mjs。見た目と並びは同じにしてある
// 違うところ：
//   ・パソコンの中のファイル（file）は Dropbox の画面で開くボタンにする（会社の Dropbox アカウントでログインが要る）
//   ・ただし public/files/ の中に同じ場所のファイルがあれば そちらを直接開く（パソコンの Claude Code で本体を写したとき用）
//   ・表紙（thumb）も public/files/ にあるときだけ出す
//   ・ダウンロード（ZIP）は 本体を写したときだけ出す
// 中身の正本は Vault の 00_HOME/保管庫/玄関データ.json。ここにあるのはその写し
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const pub = path.join(here, 'public');
const filesDir = path.join(pub, 'files');
const data = JSON.parse(fs.readFileSync(path.join(here, '玄関データ.json'), 'utf8'));
const VAULT_IN_DROPBOX = '/HIRATA/Obsidian/Almighty-AI-Brain/';
const TABS = [['app', 'アプリ'], ['slide', 'スライド'], ['pdf', 'PDF'], ['image', '画像'], ['video', '動画']];
const ICONS = { app: '▦', slide: '▭', pdf: '▤', image: '◩', video: '▶', all: '☰' };
const KINDS = [
  ['url', 'インターネットで開く', 'パソコン・iPad・スマホのどれからでも開けます'],
  ['file', 'Dropbox で開く', '保管庫（Dropbox）に入っているファイルを開きます　会社の Dropbox アカウントでログインしている端末で使えます'],
  ['run', 'AIに起動を頼む', 'パソコンの中で動かすアプリです　パソコンで下の言葉をAIに言ってください'],
];

for (const it of data.items) if (!TABS.some(t => t[0] === it.tab)) { console.error(`${it.name}：tab が正しくない（${it.tab}）`); process.exit(1); }

const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const hasLocal = p => fs.existsSync(path.join(filesDir, p));
const localUrl = p => 'files/' + p.split('/').map(encodeURIComponent).join('/');
const dropboxUrl = p => 'https://www.dropbox.com/preview' + (VAULT_IN_DROPBOX + p).split('/').map(encodeURIComponent).join('/');
const fileUrl = p => hasLocal(p) ? localUrl(p) : dropboxUrl(p);
const isHtml = p => /\.html?$/i.test(p);
const kindOf = it => { const opens = it.open || []; return it.say ? 'run' : (opens.length > 0 && opens.every(o => o.file)) ? 'file' : 'url'; };
// Dropbox の画面では HTML は文字しか出ないので HTML のボタンは後ろへ回し 一言そえる
function orderOpens(opens) {
  const weak = o => o.file && isHtml(o.file) && !hasLocal(o.file);
  return [...opens.filter(o => !weak(o)), ...opens.filter(weak)];
}
const label = o => o.file && isHtml(o.file) && !hasLocal(o.file) ? `${o.label}（Dropboxでは文字のみ）` : o.label;

// QRコード（インターネットのアドレスから作る）
const require = createRequire(import.meta.url);
const qrcode = require('qrcode-generator');
function qrSvg(text) {
  const qr = qrcode(0, 'M');
  qr.addData(text, 'Byte');
  qr.make();
  const n = qr.getModuleCount(), quiet = 4, size = n + quiet * 2;
  let d = '';
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (qr.isDark(r, c)) d += `M${c + quiet} ${r + quiet}h1v1h-1z`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" shape-rendering="crispEdges" role="img" aria-label="QRコード"><rect width="${size}" height="${size}" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
}

let localCount = 0, dropboxCount = 0;
function card(it, withThumb) {
  const opens = orderOpens(it.open || []);
  const autoQr = opens[0] && opens[0].url;
  const text = [it.name, it.tag, it.desc, it.words || '', it.manual ? 'マニュアル ガイド 使い方' : '', (it.qr || autoQr) ? 'qr' : ''].join(' ').toLowerCase();
  const thumbOk = it.thumb && hasLocal(it.thumb);
  const thumb = thumbOk ? `<div class="thumb"><img src="${esc(localUrl(it.thumb))}" alt="" loading="lazy"></div>` : withThumb ? `<div class="thumb blank" aria-hidden="true">${ICONS[it.tab]}</div>` : '<div class="no-thumb"></div>';
  const target = o => { if (o.file) { hasLocal(o.file) ? localCount++ : dropboxCount++; return fileUrl(o.file); } return o.url; };
  const buttons = it.say
    ? `<div class="say">「${esc(it.say)}」<small>と パソコンでAIに言ってください</small></div>`
    : `<div class="buttons">${opens.map((o, i) => `<a class="open${i ? ' sub' : ''}${o.file && !hasLocal(o.file) ? ' is-dbx' : ''}" href="${esc(target(o))}" target="_blank" rel="noopener">${esc(label(o))}</a>`).join('')}</div>`;
  const tools = [];
  for (const m of it.manual || []) tools.push(`<a class="tool t-manual" href="${esc(m.file ? fileUrl(m.file) : m.url)}" target="_blank" rel="noopener"><span aria-hidden="true">▤</span>${esc(m.file && isHtml(m.file) && !hasLocal(m.file) ? m.label + '（文字のみ）' : m.label)}</a>`);
  const dl = ((it.download && it.download.files) || []).map(f => typeof f === 'string' ? f : f.file).filter(hasLocal);
  for (const f of dl) tools.push(`<a class="tool t-dl" href="${esc(localUrl(f))}" download><span aria-hidden="true">⬇</span>${esc(path.basename(f))}</a>`);
  if (autoQr || it.qr) {
    const login = autoQr && /claude\.ai/.test(opens[0].url);
    const pics = [autoQr ? `<figure>${qrSvg(opens[0].url)}<figcaption>${login ? '平田さんのアカウントでログインしているスマホ・iPadで開けます' : 'スマホやiPadのカメラで読み取ると開きます'}</figcaption></figure>` : '',
      ...(it.qr || []).map(q => hasLocal(q.file)
        ? `<figure><img src="${esc(localUrl(q.file))}" alt="${esc(q.label)}のQRコード" loading="lazy"><figcaption>${esc(q.label)}</figcaption></figure>`
        : `<figure class="qr-link"><a href="${esc(dropboxUrl(q.file))}" target="_blank" rel="noopener">${esc(q.label)}のQRを Dropbox で開く</a></figure>`)].join('');
    tools.push(`<details class="qr"><summary class="tool t-qr"><span aria-hidden="true">▣</span>QRコード</summary><div class="qr-pics">${pics}</div></details>`);
  }
  const toolRow = `<div class="tools">${tools.join('')}</div>`;
  const note = `<div class="note">${it.note ? esc(it.note) : ''}</div>`;
  return `        <div class="item kind-${kindOf(it)}" data-tab="${it.tab}" data-text="${esc(text)}">${thumb}<div class="tag">${esc(it.tag)}</div><h3>${esc(it.name)}</h3><p>${esc(it.desc)}</p>${note}${buttons}${toolRow}</div>`;
}
const counts = Object.fromEntries(TABS.map(([k]) => [k, data.items.filter(i => i.tab === k).length]));
function section([k, tabLabel]) {
  const items = data.items.filter(i => i.tab === k);
  const thumbs = list => list.some(x => x.thumb && hasLocal(x.thumb));
  let body;
  if (!items.length) body = '      <p class="empty">まだありません</p>';
  else if (k === 'app') {
    body = KINDS.map(([kind, title, note]) => {
      const list = items.filter(i => kindOf(i) === kind);
      return list.length ? `      <div class="group" data-kind="${kind}">\n        <h3 class="group-title">${title}<small>${note}</small></h3>\n        <div class="grid">\n${list.map(i => card(i, thumbs(list))).join('\n')}\n        </div>\n      </div>` : '';
    }).join('\n');
  } else body = `      <div class="grid">\n${items.map(i => card(i, thumbs(items))).join('\n')}\n      </div>`;
  return `    <section class="tabpage" id="tab-${k}" data-tab="${k}">\n      <h2>${tabLabel}<span class="count">${counts[k]}件</span></h2>\n${body}\n    </section>`;
}

const now = new Date(Date.now() + 9 * 3600 * 1000);   // 日本時間
const ymd = now.toISOString().slice(0, 10);
const navButton = (k, l, n) => `      <label class="nav" for="cat-${k}" data-tab="${k}"><span class="ico" aria-hidden="true">${ICONS[k]}</span><span class="nav-label">${l}</span><span class="nav-count">${n}</span></label>`;
const ALL = [...TABS.map(t => t[0]), 'all'];
const sections = TABS.map(section).join('\n\n');
const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#22303F">
<title>保管庫の玄関</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%2322303F'/%3E%3Cpath d='M18 50V24l14-10 14 10v26H37V36H27v14z' fill='%23F2C14E'/%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="icon.svg">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@700;900&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
:root{--bg:#F5F3EE;--card:#FFFFFF;--side:#22303F;--side-ink:#E9E6DD;--side-sub:#A9B4C2;--ink:#25282F;--sub:#6F6A5C;--line:#E2DCCD;--a1:#2E4E75;--a2:#166B4E;--a3:#8A5A14;--hi:#F2C14E;--dbx:#0061FE;--shadow:0 8px 24px rgba(37,40,47,.09)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15181F;--card:#1E232D;--side:#0F1319;--ink:#E9E6DD;--sub:#A29D89;--line:#2D3442;--a1:#8FB3DC;--a2:#4FA987;--a3:#D9A658;--dbx:#6FA1FF;--shadow:0 8px 24px rgba(0,0,0,.4)}}
:root[data-theme="dark"]{--bg:#15181F;--card:#1E232D;--side:#0F1319;--ink:#E9E6DD;--sub:#A29D89;--line:#2D3442;--a1:#8FB3DC;--a2:#4FA987;--a3:#D9A658;--dbx:#6FA1FF;--shadow:0 8px 24px rgba(0,0,0,.4)}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
html,body{background:var(--bg);color:var(--ink)}
body{font-family:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}
.layout{display:grid;grid-template-columns:232px minmax(0,1fr);min-height:100vh}
.side{background:var(--side);color:var(--side-ink);padding:24px 14px;position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;gap:6px}
.side h1{font-family:"Zen Maru Gothic",sans-serif;font-weight:900;font-size:22px;letter-spacing:.04em;padding:0 10px}
.side .lede{font-size:12px;color:var(--side-sub);padding:0 10px 14px;line-height:1.6}
.nav{display:flex;align-items:center;gap:10px;padding:12px 12px;border-radius:12px;color:var(--side-ink);text-decoration:none;font-weight:700;font-size:16px;border:1px solid transparent;cursor:pointer}
.nav:hover{background:rgba(255,255,255,.07)}
.nav .ico{width:22px;text-align:center;opacity:.85}
.nav-label{flex:1}
.nav-count{font-size:12px;font-weight:700;padding:1px 9px;border-radius:999px;background:rgba(255,255,255,.14)}
.nav-sep{height:1px;background:rgba(255,255,255,.14);margin:8px 10px}
.side-foot{margin-top:auto;font-size:11.5px;color:var(--side-sub);padding:12px 10px 0;line-height:1.6}
.nav:focus-visible,.search:focus-visible,.open:focus-visible{outline:2px solid var(--hi);outline-offset:2px}
.main{padding:24px 24px 56px;min-width:0}
.search{width:100%;max-width:720px;padding:13px 16px;border:1px solid var(--line);border-radius:14px;background:var(--card);color:var(--ink);font:inherit;font-size:16px}
.search-note{font-size:13px;color:var(--sub);margin-top:6px;min-height:1.4em}
h2{font-family:"Zen Maru Gothic",sans-serif;font-size:24px;margin:18px 0 14px}
.count{font-size:13px;font-weight:400;color:var(--sub);margin-left:10px}
.group{margin-bottom:26px}
.group-title{font-family:"Zen Maru Gothic",sans-serif;font-size:16px;margin:0 0 10px;padding-left:10px;border-left:4px solid var(--a1)}
.group[data-kind="file"] .group-title{border-color:var(--dbx)}.group[data-kind="run"] .group-title{border-color:var(--a3)}
.group-title small{display:block;font-family:"Zen Kaku Gothic New",sans-serif;font-weight:400;font-size:12.5px;color:var(--sub)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(264px,1fr));gap:14px}
.item{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:var(--shadow);display:flex;flex-direction:column}
.thumb{margin:-16px -16px 12px;border-radius:18px 18px 0 0;overflow:hidden;background:var(--bg);aspect-ratio:16/9;border-bottom:1px solid var(--line)}
.thumb img{display:block;width:100%;height:100%;object-fit:cover;object-position:top}
.item[data-tab="image"] .thumb img,.item[data-tab="pdf"] .thumb img{object-fit:contain;object-position:center}
.thumb.blank{display:grid;place-items:center;font-size:44px;color:var(--line)}
.tag{font-size:12px;letter-spacing:.06em;font-weight:700;color:var(--a1)}
.kind-file .tag{color:var(--dbx)}.kind-run .tag{color:var(--a3)}
.item h3{font-family:"Zen Maru Gothic",sans-serif;font-weight:700;font-size:18px;line-height:1.45;margin-top:2px}
.item p{font-size:13.5px;color:var(--sub);margin:6px 0 0;flex:1}
.buttons{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;align-content:start}
.open{flex:1 1 auto;text-align:center;text-decoration:none;border-radius:999px;padding:11px 16px;font-size:14.5px;font-weight:700;color:#fff;background:var(--a1)}
.open.is-dbx{background:var(--dbx)}
.open.sub{background:transparent;color:var(--ink);border:1px solid var(--line)}
.open.sub.is-dbx{color:var(--dbx);border-color:var(--dbx)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .open{color:#15181F}}
.tools{display:flex;flex-wrap:wrap;align-items:flex-start;align-content:flex-start;gap:6px;margin-top:10px;padding-top:10px;border-top:1px dashed var(--line)}
.tool{display:inline-flex;align-items:center;gap:4px;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:5px 9px;cursor:pointer;list-style:none;white-space:nowrap}
.tool::-webkit-details-marker{display:none}
.tool:hover{border-color:var(--a1)}
.tool span{color:var(--a1);font-size:12px}
.t-dl span{color:var(--a2)}.t-qr span{color:var(--a3)}
.tool:focus-visible{outline:2px solid var(--hi);outline-offset:2px}
.qr[open]{flex-basis:100%}
.qr[open] .t-qr{border-color:var(--a3)}
.qr-pics{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.qr-pics figure{flex:1 1 120px;max-width:200px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px;text-align:center}
.qr-pics svg,.qr-pics img{display:block;width:100%;height:auto}
.qr-pics figcaption{font-size:11.5px;line-height:1.5;color:#55514a;margin-top:4px}
.qr-pics .qr-link{display:grid;place-items:center;font-size:12.5px;font-weight:700}
.qr-pics .qr-link a{color:#0061FE}
.note{font-size:12.5px;line-height:1.6;color:var(--a3);background:var(--bg);border-radius:10px;padding:8px 10px;margin-top:10px}
.note:empty,.tools:empty{padding:0;margin:0;border:0;background:transparent}
@supports (grid-template-rows:subgrid){.item{display:grid;grid-row:span 7;grid-template-rows:subgrid;row-gap:0;align-content:start}.grid{row-gap:0}.item{margin-bottom:14px}}
.say{margin-top:14px;background:var(--bg);border:1px dashed var(--line);border-radius:12px;padding:10px 12px;font-size:14px;font-weight:700;text-align:center}
.say small{display:block;font-weight:400;color:var(--sub);font-size:12px}
.empty{color:var(--sub);font-size:14px}
.box{margin-top:30px;max-width:900px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px 20px}
.box h3{font-family:"Zen Maru Gothic",sans-serif;font-size:16px;margin-bottom:6px}
.box li,.box p{font-size:14px;color:var(--sub)}
.box ul{padding-left:1.2em}
.box b{color:var(--ink)}
.hidden{display:none!important}
.cat{position:absolute;opacity:0;pointer-events:none;width:1px;height:1px}
.tabpage{display:none}
${TABS.map(([k]) => `#cat-${k}:checked~.layout #tab-${k}`).join(',')},#cat-all:checked~.layout .tabpage,body.searching .tabpage{display:block}
${ALL.map(k => `#cat-${k}:checked~.layout .nav[data-tab="${k}"]`).join(',')}{background:var(--hi);color:#22303F}
${ALL.map(k => `#cat-${k}:checked~.layout .nav[data-tab="${k}"] .nav-count`).join(',')}{background:rgba(34,48,63,.16)}
body.searching .nav{background:transparent!important;color:var(--side-ink)!important}
${ALL.map(k => `#cat-${k}:focus-visible~.layout .nav[data-tab="${k}"]`).join(',')}{outline:2px solid var(--hi);outline-offset:2px}
@media (prefers-reduced-motion:no-preference){.tabpage.pop{animation:pop .22s ease-out}}
@keyframes pop{from{opacity:0;transform:translateX(18px)}to{opacity:1;transform:none}}
@media (max-width:820px){
  .layout{grid-template-columns:1fr}
  .side{position:sticky;top:0;z-index:5;height:auto;flex-direction:row;flex-wrap:wrap;align-items:center;padding:10px 10px;gap:6px}
  .side h1{font-size:17px;width:100%;padding:0 4px}
  .side .lede,.side-foot,.nav-sep{display:none}
  .nav{padding:8px 12px;font-size:14px;gap:6px}
  .nav .ico{display:none}
  .main{padding:16px 16px 48px}
  .grid{grid-template-columns:1fr}
  h2{font-size:21px}
}
</style>
</head>
<body>
${ALL.map((k, i) => `<input class="cat" type="radio" name="cat" id="cat-${k}" value="${k}"${i === 0 ? ' checked' : ''} aria-label="${k === 'all' ? 'すべて' : TABS.find(t => t[0] === k)[1]}">`).join('\n')}
<div class="layout">
  <nav class="side" aria-label="カテゴリー">
    <h1>保管庫の玄関</h1>
    <p class="lede">株式会社オールマイティで作ったものの入口です</p>
${TABS.map(([k, l]) => navButton(k, l, counts[k])).join('\n')}
    <div class="nav-sep"></div>
${navButton('all', 'すべて', data.items.length)}
    <p class="side-foot">左のカテゴリーを選ぶと 右にその中身が出ます<br>${ymd} 更新</p>
  </nav>

  <main class="main" id="top">
    <input class="search" id="q" type="search" placeholder="名前や用途で探す（例　ルーター　名刺　ワード　勉強会）" aria-label="探す">
    <p class="search-note" id="search-note"></p>

${sections}

    <div class="box">
      <h3>このページについて</h3>
      <ul>
        <li><b>青いボタン</b> はインターネットのページを開きます　どの端末からでも開けます</li>
        <li><b>明るい青のボタン</b> は 保管庫（Dropbox）のファイルを Dropbox の画面で開きます　<b>会社の Dropbox アカウント</b>でログインしている端末で使えます　別のアカウントだと「フォルダは存在しません」と出ます</li>
        <li>「ブラウザで発表する」などの HTML のスライドは Dropbox の画面では文字しか出ません　PDF か PowerPoint のボタンを使ってください</li>
        <li>claude.ai のアドレスのアプリは ログインを求められたら いつものアカウントでログインしてください</li>
        <li>中身の正本は 保管庫の <b>00_HOME → 保管庫 → 玄関データ.json</b> です　新しく載せたいものができたら AIに「保管庫に載せて」と言ってください</li>
      </ul>
    </div>
  </main>
</div>

<script>
'use strict';
// このページは genkan/build.mjs が作る　直接は書き換えない
const q = document.getElementById('q');
const note = document.getElementById('search-note');
function show() {
  const words = q.value.toLowerCase().split(/\\s+/).filter(Boolean);
  const searching = words.length > 0;
  document.body.classList.toggle('searching', searching);
  let shown = 0;
  for (const el of document.querySelectorAll('.item')) {
    const ok = words.every(w => el.dataset.text.includes(w));
    el.classList.toggle('hidden', !ok);
    if (ok) shown++;
  }
  for (const g of document.querySelectorAll('.group')) g.classList.toggle('hidden', !g.querySelector('.item:not(.hidden)'));
  for (const sec of document.querySelectorAll('.tabpage')) sec.classList.toggle('hidden', searching && !sec.querySelector('.item:not(.hidden)'));
  note.textContent = searching ? (shown ? '全部の種類から探しています　' + shown + '件' : '見つかりませんでした') : '';
}
for (const r of document.querySelectorAll('.cat')) r.addEventListener('change', () => {
  q.value = '';
  show();
  try { localStorage.setItem('genkan.cat', r.value); } catch (err) {}
  const sec = document.getElementById('tab-' + r.value);
  if (sec) { sec.classList.remove('pop'); void sec.offsetWidth; sec.classList.add('pop'); }
  window.scrollTo({ top: 0, behavior: 'instant' });
});
q.addEventListener('input', show);
try { const saved = localStorage.getItem('genkan.cat'); const r = saved && saved !== 'all' && document.getElementById('cat-' + saved); if (r) r.checked = true; } catch (err) {}
show();
</script>
</body>
</html>
`;
fs.mkdirSync(pub, { recursive: true });
fs.writeFileSync(path.join(pub, 'index.html'), html);
console.log(`保管庫の玄関（インターネット版）を作りました：${data.items.length}件（${TABS.map(([k, l]) => l + ' ' + counts[k]).join('／')}）`);
console.log(`ファイルのボタン：直接開く ${localCount}／Dropbox で開く ${dropboxCount}`);
