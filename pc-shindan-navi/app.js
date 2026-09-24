'use strict';
// パソコン診断ナビ（パソコン相談ナビと同じ画面構成・同じ操作）
// 役割：お持ち込みのパソコンを技術スタッフにつなぐまでの受付画面　細かな診断や解決はここではしない
// 文面のルール：句読点は使わず全角スペースで区切る／お客様に負担を突きつけず店側から申し出る聞き方にする
// 質問文 lead・title・help は「文節の配列」で書く（画面では文節の切れ目でだけ改行される）
// help は行ごとの配列  [[1行目の文節…],[2行目の文節…]]   強調したい所は <strong class="warn">…</strong>
// 流れ：最初の画面で基本診断費を案内 → はい／いいえの3問（データ・パスワード・心当たり）→ 8つのボタンから症状を1つ選ぶ → 担当者に見せる引き継ぎ画面
// 引き継ぎ画面まで進んだお客様はすべて「受付」として数える（スタッフの記入はない）
// short：集計やCSVで使う短い呼び名　summary：集計や回答一覧に出す一文（無ければ title をつなげる）
const FEE='2,200円'; // 基本診断費（最初の画面と引き継ぎ画面に表示する）
const QUESTIONS = {
 data:{label:'まず最初に',short:'残したいデータ',title:['残したい','写真や書類などの','データは','入っていますか？'],summary:'残したい写真や書類などのデータは入っていますか？',help:[['作業の前に','データを守る方法を考えるための','確認です'],['わからない場合は','「はい」で大丈夫です']],yes:'残したいデータがある',no:'特にない',next:'pcpass'},
 pcpass:{label:'パスワードの確認',short:'Windowsのパスワード',lead:['お預かりして確認するときに','必要になります'],title:['Windowsに入るときの','パスワード（PIN）は','わかりますか？'],summary:'Windowsに入るときのパスワード（PIN）はわかりますか？',help:[['受付のときに','技術スタッフへお伝えいただきます'],['わからない場合は','別の方法をご案内します']],yes:'わかる',no:'わからない・設定していない',next:'change'},
 change:{label:'心当たりの確認',short:'心当たり',title:['症状が出る少し前に','心当たりは','ありますか？'],summary:'症状が出る少し前に心当たりはありますか？',help:[['落とした・水がかかった・','Windowsの更新をした・'],['新しいソフトや機器をつないだ など']],yes:'心当たりがある',no:'特にない・わからない',next:'symptom'}
};
const QUESTION_IDS=Object.keys(QUESTIONS);
const QUESTION_MAX=QUESTION_IDS.length+1; // はい／いいえ3問 ＋ 症状の選択
const FIRST=QUESTION_IDS[0];
const phr=parts=>parts.map(p=>'<span class="ph">'+p+'</span>').join('');
const plain=parts=>parts.join('').replace(/<[^>]+>/g,'');
const titleText=q=>q.summary || plain(q.title);

// 4 お困りの症状（8つのボタンから1つ選ぶ）　label：ボタンの文字　sub：ボタンの小さな説明
const SYMPTOMS = {
 power:{label:'電源が入らない',sub:'ランプも点かない・音もしない'},
 boot:{label:'Windowsが起動しない',sub:'ロゴのまま進まない・青い画面・回復キー'},
 internet:{label:'インターネットにつながらない',sub:'ホームページが開かない・Wi-Fiが切れる'},
 mail:{label:'メールができない',sub:'送れない・届かない・パスワードを聞かれる'},
 error:{label:'Windowsでエラーが出る',sub:'「問題が発生しました」・固まる・再起動する'},
 virus:{label:'ウイルス感染・警告画面',sub:'警告や電話番号が出た・音が鳴った'},
 slow:{label:'動作が遅い・固まる',sub:'起動に何分もかかる・途中で止まる'},
 other:{label:'その他のご相談',sub:'画面・キーボード・プリンター・使い方など'}
};
const SYMPTOM_ORDER=Object.keys(SYMPTOMS);
const answerOf=id=>history.find(h=>h.id===id)?.answer;
const symKey=()=>SYMPTOMS[answerOf('symptom')]?answerOf('symptom'):'other';

// 集計（裏メニュー）
// 回答はこのiPadの中だけに保存する（外部には送らない）　個人を特定する情報は記録しない
// 開き方：右上の「約2分・全4問」を続けて5回タップ
const STORE_KEY='pcshindan.records.v3';
const SETTINGS_KEY='pcshindan.settings.v1';
let sessionId=null,syncing=false,syncNote='';
const loadRecords=()=>{try{return JSON.parse(localStorage.getItem(STORE_KEY))||[];}catch(e){return [];}};
const saveRecords=list=>{try{localStorage.setItem(STORE_KEY,JSON.stringify(list));return true;}catch(e){return false;}};
// 送信先（Googleスプレッドシートの受付窓口）　診断ナビ用の窓口（gas/Code.gs）を用意したら ここに入れておくと iPadごとの入力がいらない
// 合言葉はプログラムの中には書かない　iPadごとに裏メニューで入力する　合言葉が合わない送信は受付窓口がすべて断る
const DEFAULT_URL='';
const loadSettings=()=>{let s={};try{s=JSON.parse(localStorage.getItem(SETTINGS_KEY))||{};}catch(e){}return {device:s.device||'',url:s.url||DEFAULT_URL,pass:s.pass||''};};
const saveSettings=s=>{try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(s));}catch(e){}};
function recordSession(){
 if(!sessionId)sessionId=Date.now().toString(36)+Math.random().toString(36).slice(2,6);
 const list=loadRecords(),i=list.findIndex(r=>r.id===sessionId);
 const rec={id:sessionId,at:i>=0?list[i].at:new Date().toISOString(),device:loadSettings().device,answers:history.map(h=>({q:h.id,a:h.answer})),symptom:symKey(),sent:false};
 if(i>=0)list[i]=rec;else list.push(rec);
 saveRecords(list);
 syncRecords();
}
const answerLabel=(q,a)=>q==='symptom'?(SYMPTOMS[a]?SYMPTOMS[a].label:a):a==='yes'?'はい':'いいえ';
const ansOf=(r,id)=>{const x=r.answers.find(v=>v.q===id);return x?answerLabel(id,x.a):'';};
const symptomName=r=>SYMPTOMS[r.symptom]?SYMPTOMS[r.symptom].label:'';
const when=iso=>{const d=new Date(iso),p=n=>String(n).padStart(2,'0');return d.getFullYear()+'/'+p(d.getMonth()+1)+'/'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());};
// 未送信の記録を1件ずつ受付窓口へ送る　同じお客様の記録は上書きされる　電波がないときは次の機会に送る
function toRow(r){
 return {id:r.id,at:when(r.at),device:r.device || loadSettings().device,data:ansOf(r,'data'),pcpass:ansOf(r,'pcpass'),change:ansOf(r,'change'),symptom:symptomName(r)};
}
async function syncRecords(){
 const s=loadSettings();
 if(!s.url||!s.pass||syncing)return;
 syncing=true;
 try{
  for(const r of loadRecords().filter(v=>!v.sent)){
   const res=await fetch(s.url,{method:'POST',body:JSON.stringify({pass:s.pass,record:toRow(r)})});
   const out=await res.json();
   if(!out.ok)throw new Error(out.error || '受付窓口がエラーを返しました');
   const list=loadRecords(),i=list.findIndex(v=>v.id===r.id);
   if(i>=0&&JSON.stringify(list[i].answers)===JSON.stringify(r.answers)){list[i].sent=true;saveRecords(list);}
  }
  syncNote='送信できました（'+when(new Date().toISOString())+'）';
 }catch(e){syncNote='送信できませんでした：'+e.message;}
 syncing=false;
 if(screen==='admin'&&!(document.activeElement&&document.activeElement.matches('input')))render(false);
}
window.addEventListener('online',syncRecords);
function adminView(){
 const list=loadRecords(),total=list.length,set=loadSettings(),unsent=list.filter(r=>!r.sent).length;
 const esc=t=>String(t).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
 const pct=(n,d)=>d?Math.round(n/d*100):0;
 const rows=QUESTION_IDS.map((id,i)=>{
  let yes=0,no=0;
  for(const r of list)for(const x of r.answers)if(x.q===id){if(x.a==='yes')yes++;else no++;}
  const q=QUESTIONS[id],n=yes+no;
  return `<tr><th>${i+1}</th><td class="q">${titleText(q)}</td><td class="num">${n}</td><td class="num yes">はい ${yes}<small>${pct(yes,n)}%</small></td><td class="num no">いいえ ${no}<small>${pct(no,n)}%</small></td><td class="bar"><span style="width:${pct(yes,n)}%"></span></td></tr>`;
 }).join('');
 const symptoms=SYMPTOM_ORDER.map(k=>[k,list.filter(r=>r.symptom===k).length]).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<tr><td class="q">${SYMPTOMS[k].label}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`).join('');
 const people=list.slice().reverse().slice(0,300).map(r=>{
  const cells=QUESTION_IDS.map(id=>{const x=r.answers.find(v=>v.q===id);return x?`<td class="${x.a}">${answerLabel(id,x.a)}</td>`:'<td>-</td>';}).join('');
  return `<tr><td class="when">${when(r.at)}</td>${cells}<td class="q">${symptomName(r) || '-'}</td></tr>`;
 }).join('');
 return `<section class="admin"><div class="admin-head"><div><span class="tag">スタッフ専用</span><h1>回答の集計</h1><p>このiPadで受付したお客様 <b>${total}</b> 人（症状を選んで引き継ぎ画面まで進んだ人数）　${set.url&&set.pass?`未送信 <b>${unsent}</b> 件`:'送信先か合言葉が未設定のためこのiPadの中だけに保存しています'}</p></div><div class="admin-actions"><button class="admin-button" data-action="admin-csv" ${total?'':'disabled'}>CSVで書き出す</button><button class="admin-button danger" data-action="admin-clear" ${total?'':'disabled'}>記録をすべて消す</button><button class="admin-button primary" data-action="admin-close">お客様の画面に戻る</button></div></div>
 <h2>このiPadの設定</h2><div class="admin-settings"><label>iPadの名前<input id="set-device" value="${esc(set.device)}" placeholder="例 iPad 1号機"></label><label>送信先URL（診断ナビ用の受付窓口を用意したら入力）<input id="set-url" value="${esc(set.url)}" placeholder="https://script.google.com/macros/s/…/exec" inputmode="url" autocapitalize="off" autocorrect="off"></label><label>合言葉<span class="pass-row"><input id="set-pass" type="password" value="${esc(set.pass)}" autocomplete="off" autocapitalize="off" autocorrect="off"><button type="button" class="admin-button small" data-action="admin-peek">見る</button></span></label><div class="admin-actions"><button class="admin-button primary" data-action="admin-save">設定を保存</button><button class="admin-button" data-action="admin-sync" ${set.url&&set.pass&&unsent?'':'disabled'}>未送信を今すぐ送る</button></div><p class="admin-note">${syncNote || 'すべてのiPadの集計はGoogleスプレッドシートに集まります　この画面の集計はこのiPadの分だけです'}</p></div>
 <h2>お困りの症状（多い順）</h2><table class="admin-table"><tbody>${symptoms}</tbody></table>
 <h2>質問ごとの集計（このiPadの分）</h2><div class="admin-scroll"><table class="admin-table"><thead><tr><th>問</th><th>質問</th><th>回答数</th><th>はい</th><th>いいえ</th><th>はいの割合</th></tr></thead><tbody>${rows}</tbody></table></div>
 <h2>お客様ごとの回答（新しい順）</h2><div class="admin-scroll"><table class="admin-table people"><thead><tr><th>日時</th>${QUESTION_IDS.map(id=>`<th>${QUESTIONS[id].short}</th>`).join('')}<th>お困りの症状</th></tr></thead><tbody>${people || `<tr><td colspan="${QUESTION_IDS.length+2}">まだ記録がありません</td></tr>`}</tbody></table></div></section>`;
}
function exportCsv(){
 const head=['日時','iPad',...QUESTION_IDS.map(id=>QUESTIONS[id].short),'お困りの症状'];
 const lines=loadRecords().map(r=>[when(r.at),r.device||'',...QUESTION_IDS.map(id=>ansOf(r,id)),symptomName(r)]);
 const csv='﻿'+[head,...lines].map(row=>row.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const d=new Date(),p=n=>String(n).padStart(2,'0'),name='pc-shindan-navi-'+d.getFullYear()+p(d.getMonth()+1)+p(d.getDate())+'.csv';
 const file=new File([csv],name,{type:'text/csv'});
 if(navigator.canShare&&navigator.canShare({files:[file]})){navigator.share({files:[file],title:name}).catch(()=>{});return;}
 const a=document.createElement('a');a.href=URL.createObjectURL(file);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

const main=document.getElementById('main');
let history=[],screen=FIRST;
const tick='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const cross='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" stroke-linecap="round"/></svg>';
function aside(stage){return `<aside class="sidebar"><div class="eyebrow">PC TROUBLE CHECK</div><h2>お困りの症状を<br>技術スタッフに<br>つなぐ　</h2><div class="steps">${['質問に答える','症状を選ぶ','技術スタッフへ'].map((t,i)=>`<div class="step ${stage===i?'current':stage>i?'complete':''}" ${stage===i?'aria-current="step"':''}><span class="step-index">${stage>i?'✓':i+1}</span><span>${t}</span></div>`).join('')}</div><div class="side-bottom"><strong class="reassurance"><span>わからないときは</span><span>だいたいで大丈夫</span></strong><br>近いと思うほうを<br>選んでください　</div></aside>`;}
function choice(answer,label,sub){return `<button class="choice ${answer==='no'?'no':''}" data-answer="${answer}"><span class="choice-label">${answer==='yes'?tick:cross}${label}</span><small>${sub}</small></button>`;}
function topline(label,n){return `<div class="topline"><span class="tag">${label}</span><span class="count"><b>${String(n).padStart(2,'0')}</b> / ${QUESTION_MAX}</span></div><div class="progress" aria-label="全${QUESTION_MAX}問中${n}問目">${Array.from({length:QUESTION_MAX},(_,i)=>i+1).map(i=>`<span class="${i<=n?'on':''}"></span>`).join('')}</div>`;}
// 基本診断費の案内（最初の画面でいちばん大きく見せる）
// 3行に分けて見せる：「パソコン診断には」「基本診断費 2,200円」「がかかります」
const feeBanner=()=>`<div class="fee-banner" role="note"><span class="fee-lead">パソコン診断には</span><span class="fee-amount"><span class="fee-name">基本診断費</span><span class="fee-price">${FEE}</span></span><span class="fee-tail">がかかります　</span></div>`;
function render(focus=true){
 let html,stage=0;
 if(screen==='admin'){main.innerHTML=`<div class="stage admin-stage">${adminView()}</div>`;window.scrollTo({top:0,behavior:'instant'});return;}
 if(QUESTIONS[screen]){
  const q=QUESTIONS[screen],n=history.length+1,first=screen===FIRST;
  html=`<section class="content fade-in ${first?'welcome':''}">${topline(q.label,n)}<div class="question-area">${first?feeBanner():''}${q.lead?`<p class="question-lead">${phr(q.lead)}</p>`:''}<h1>${phr(q.title)}</h1><p class="helper">${q.help.map(phr).join('<br>')}</p></div><div class="choices">${choice('yes','はい',q.yes)}${choice('no','いいえ',q.no)}</div><div class="navrow"><button class="text-button" data-action="back" ${history.length?'':'disabled'}>← ひとつ戻る</button><span class="navhint">どちらかをタップしてください</span></div></section>`;
 }else if(screen==='symptom'){
  stage=1;const n=history.length+1;
  html=`<section class="content fade-in">${topline('お困りの症状',n)}<div class="question-area"><h1>${phr(['いちばん近い','お困りの症状を','ひとつ選んでください'])}</h1><p class="helper">${phr(['当てはまるものが複数あるときは','いちばん困っているものを','選んでください'])}<br>${phr(['詳しいことは','このあと技術スタッフがお伺いします'])}</p></div><div class="choices symptoms">${SYMPTOM_ORDER.map(k=>`<button class="choice" data-answer="${k}"><span class="choice-label ${SYMPTOMS[k].label.length>=11?'long':''}">${SYMPTOMS[k].label}</span><small>${SYMPTOMS[k].sub}</small></button>`).join('')}</div><div class="navrow"><button class="text-button" data-action="back">← ひとつ戻る</button><span class="navhint">どれかをタップしてください</span></div></section>`;
 }else{
  stage=2;
  html=`<section class="content handoff fade-in"><span class="tag">受付内容の確認</span><h1>${phr(['この画面を','技術スタッフに','お見せください　'])}</h1><p class="handoff-note">ただいまより 技術スタッフがお伺いします　</p><p class="helper">ご回答をもとに 技術スタッフがパソコンを拝見します　基本診断費は${FEE}です　</p><div class="recommendation is-pack"><span class="eyebrow">お困りの症状</span><h2>${SYMPTOMS[symKey()].label}</h2></div><ul class="answer-list">${history.filter(h=>QUESTIONS[h.id]).map(h=>`<li><span>${titleText(QUESTIONS[h.id])}</span><b>${answerLabel(h.id,h.answer)}</b></li>`).join('')}</ul><p class="micro">この画面では申込や予約は行われません　お預かりの手続きや料金は技術スタッフがご案内します　</p><div class="navrow"><button class="text-button" data-action="back">← 症状を選び直す</button><button class="text-button" data-action="restart">最初の質問へ</button></div></section>`;
 }
 const photo=screen===FIRST||screen==='handoff'?'support-consultation':'laptop-setup';
 main.innerHTML=`<div class="stage photo-${photo}">${aside(stage)}${html}</div>`;
 if(focus){main.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
}
main.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b||b.disabled)return;
 if(b.dataset.answer){
  const a=b.dataset.answer;
  if(QUESTIONS[screen]){history.push({id:screen,answer:a});screen=QUESTIONS[screen].next;}
  else if(screen==='symptom'){if(!SYMPTOMS[a])return;history.push({id:'symptom',answer:a});screen='handoff';recordSession();}
 }else if(b.dataset.action==='back'){const prev=history.pop();if(prev)screen=prev.id;}
 else if(b.dataset.action==='restart'){history=[];screen=FIRST;sessionId=null;}
 else if(b.dataset.action==='admin-close'){history=[];screen=FIRST;sessionId=null;}
 else if(b.dataset.action==='admin-csv'){exportCsv();return;}
 else if(b.dataset.action==='admin-peek'){const i=document.getElementById('set-pass');i.type=i.type==='password'?'text':'password';b.textContent=i.type==='password'?'見る':'隠す';return;}
 else if(b.dataset.action==='admin-save'){const v=id=>document.getElementById(id).value.trim();saveSettings({device:v('set-device'),url:v('set-url'),pass:v('set-pass')});syncNote='設定を保存しました';syncRecords();}
 else if(b.dataset.action==='admin-sync'){syncNote='送信しています';syncRecords();}
 else if(b.dataset.action==='admin-clear'){if(!window.confirm('記録をすべて消します　元に戻せません　よろしいですか？'))return;saveRecords([]);}
 render();
});
for(const file of ['laptop-setup','support-consultation']){const img=new Image();img.src='photos/'+file+'.png';}
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();history=[];screen=FIRST;sessionId=null;render();});
// 裏メニュー：右上の「約2分・全4問」を3秒以内に5回タップ
let secretTaps=[];
document.querySelector('.header-note').addEventListener('click',()=>{const now=Date.now();secretTaps=secretTaps.filter(t=>now-t<3000);secretTaps.push(now);if(secretTaps.length>=5){secretTaps=[];screen='admin';syncNote='';render();syncRecords();}});
// アプリ化：オフラインでも動くようにする（https または localhost のときだけ）
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('sw.js').catch(()=>{});
render(false);
