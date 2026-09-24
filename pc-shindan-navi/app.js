'use strict';
// パソコン診断ナビ（パソコン相談ナビと同じ画面構成・同じ操作）
// 文面のルール：句読点は使わず全角スペースで区切る／お客様に負担を突きつけず店側から申し出る聞き方にする
// 質問文 lead・title・help は「文節の配列」で書く（画面では文節の切れ目でだけ改行される）
// help は行ごとの配列  [[1行目の文節…],[2行目の文節…]]   強調したい所は <strong class="warn">…</strong>
// 質問の流れ：はい／いいえの3問（データ・パスワード・心当たり）のあと 8つのボタンからお困りの症状を1つ選ぶ（全4問）
// note：答えによって結果ページの「ご回答から見えたこと」に足す一文
// short：集計やCSVで使う短い呼び名　summary：集計や回答一覧に出す一文（無ければ title をつなげる）
const QUESTIONS = {
 // 1〜3 はい／いいえ（受付に必要なこと）
 data:{label:'まず最初に',short:'残したいデータ',title:['残したい','写真や書類などの','データは','入っていますか？'],summary:'残したい写真や書類などのデータは入っていますか？',help:[['作業の前に','データを守る方法を考えるための','確認です'],['わからない場合は','「はい」で大丈夫です']],yes:'残したいデータがある',no:'特にない',note:{yes:'残したいデータがあるため 作業の前にデータを守る方法をご案内します',no:'残したいデータは特にないとのことです'},next:{yes:'pcpass',no:'pcpass'}},
 pcpass:{label:'パスワードの確認',short:'Windowsのパスワード',lead:['お預かりして確認するときに','必要になります'],title:['Windowsに入るときの','パスワード（PIN）は','わかりますか？'],summary:'Windowsに入るときのパスワード（PIN）はわかりますか？',help:[['受付のときに','担当者へお伝えいただきます'],['わからない場合は','別の方法をご案内します']],yes:'わかる',no:'わからない・設定していない',note:{no:'Windowsのパスワードがわからないため 作業の前に確認が必要です'},next:{yes:'change',no:'change'}},
 change:{label:'心当たりの確認',short:'心当たり',title:['症状が出る少し前に','心当たりは','ありますか？'],summary:'症状が出る少し前に心当たりはありますか？',help:[['落とした・水がかかった・','Windowsの更新をした・'],['新しいソフトや機器をつないだ など']],yes:'心当たりがある',no:'特にない・わからない',note:{yes:'症状が出る前に心当たりがあるとのことです　担当者に詳しくお聞かせください'},next:{yes:'symptom',no:'symptom'}}
};
const QUESTION_IDS=Object.keys(QUESTIONS);
const QUESTION_MAX=QUESTION_IDS.length+1; // はい／いいえ3問 ＋ 症状の選択
const phr=parts=>parts.map(p=>'<span class="ph">'+p+'</span>').join('');
const plain=parts=>parts.join('').replace(/<[^>]+>/g,'');
const titleText=q=>q.summary || plain(q.title);

// 4 お困りの症状（8つのボタンから1つ選ぶ）
//   label：ボタンの文字　sub：ボタンの小さな説明　headline：結果ページの見出し　check：当店で確認すること
//   next：次のステップ（counter 店頭チェック／takein お預かり診断）
const SYMPTOMS = {
 power:{label:'電源が入らない',sub:'ランプも点かない・音もしない',headline:['お困りの内容は','「電源が入らない」','トラブルのようです'],check:'ACアダプターとバッテリー 本体の電源まわりを確認します',next:'takein'},
 boot:{label:'Windowsが起動しない',sub:'ロゴのまま進まない・青い画面・回復キー',headline:['お困りの内容は','「Windowsが起動しない」','トラブルのようです'],check:'Windowsの修復と 記憶装置（SSD・HDD）の状態を確認します　回復キーの画面が出ている場合は保管先を一緒に探します',next:'takein'},
 internet:{label:'インターネットにつながらない',sub:'ホームページが開かない・Wi-Fiが切れる',headline:['お困りの内容は','「インターネットにつながらない」','トラブルのようです'],check:'Wi-Fiの設定とつなぎ方 ルーターや回線側の状態を確認します',next:'counter'},
 mail:{label:'メールができない',sub:'送れない・届かない・パスワードを聞かれる',headline:['お困りの内容は','「メールができない」','トラブルのようです'],check:'メールの設定とパスワード 容量やプロバイダー側の状態を確認します　プロバイダーの書類があればお持ちください',next:'counter'},
 error:{label:'Windowsでエラーが出る',sub:'「問題が発生しました」・固まる・再起動する',headline:['お困りの内容は','「エラーが出る」','トラブルのようです'],check:'エラーの内容を確かめ Windowsやソフトの修復が必要かを確認します',next:'takein'},
 virus:{label:'ウイルス感染・警告画面',sub:'警告や電話番号が出た・音が鳴った',headline:['お困りの内容は','「ウイルス感染・警告画面」の','トラブルのようです'],check:'警告の正体を確かめ 不審なソフトが残っていないかを確認します　表示された番号に電話や操作をした場合は パスワードの変更やカード会社への連絡もご案内します',next:'takein'},
 slow:{label:'動作が遅い・固まる',sub:'起動に何分もかかる・途中で止まる',headline:['お困りの内容は','「動作が遅い・固まる」','トラブルのようです'],check:'記憶装置とメモリーの状態 ソフトの入りすぎや更新の状況を確認します',next:'takein'},
 other:{label:'その他のご相談',sub:'画面・キーボード・プリンター・使い方など',headline:['お困りの内容を','担当者が','直接お伺いします'],check:'画面やキーボードなど機器の不調 プリンターのつなぎ方 使い方やデータの移し替えなど ご相談の内容を担当者が直接お伺いします',next:'counter'}
};
const SYMPTOM_ORDER=Object.keys(SYMPTOMS);
// 次のステップ（2つのうち必ずどちらかを提案する）　名前や説明はお店の受付メニューに合わせて直す
const NEXT = {
 counter:{name:'店頭チェック',parts:['店頭','チェック'],badge:'その場で確認',desc:'その場でパソコンを見せていただき 設定やつなぎ方を確認します　短い時間で解決が見込めるときにご案内します'},
 takein:{name:'お預かり診断',parts:['お預かり','診断'],badge:'詳しく調べる',desc:'パソコンをお預かりして 電源や起動 エラーの原因を詳しく調べます　結果とお見積りをご連絡してから作業に進みます'}
};
const NEXT_ORDER=['counter','takein'];
// 基本診断費（最初の画面と結果に表示する）
const FEE='2,200円';
const answerOf=id=>history.find(h=>h.id===id)?.answer;
const symKey=()=>SYMPTOMS[answerOf('symptom')]?answerOf('symptom'):'other';
const nextKey=()=>SYMPTOMS[symKey()].next;
function recommendation(){
 const ck=symKey(),cat=SYMPTOMS[ck],key=nextKey(),step=NEXT[key],reasons=[cat.check];
 for(const h of history){const n=QUESTIONS[h.id]&&QUESTIONS[h.id].note;if(n&&n[h.answer])reasons.push(n[h.answer]);}
 return {key,step,ck,cat,reasons};
}

// 集計（裏メニュー）
// 回答はこのiPadの中だけに保存する（外部には送らない）　個人を特定する情報は記録しない
// 開き方：右上の「約2分・全4問」を続けて5回タップ
const STORE_KEY='pcshindan.records.v2';
const SETTINGS_KEY='pcshindan.settings.v1';
let sessionId=null,syncing=false,syncNote='';
const loadRecords=()=>{try{return JSON.parse(localStorage.getItem(STORE_KEY))||[];}catch(e){return [];}};
const saveRecords=list=>{try{localStorage.setItem(STORE_KEY,JSON.stringify(list));return true;}catch(e){return false;}};
// 送信先（Googleスプレッドシートの受付窓口）　診断ナビ用の窓口（gas/Code.gs）を用意したら ここに入れておくと iPadごとの入力がいらない
// 合言葉はプログラムの中には書かない　iPadごとに裏メニューで入力する　合言葉が合わない送信は受付窓口がすべて断る
const DEFAULT_URL='';
const loadSettings=()=>{let s={};try{s=JSON.parse(localStorage.getItem(SETTINGS_KEY))||{};}catch(e){}return {device:s.device||'',url:s.url||DEFAULT_URL,pass:s.pass||''};};
const saveSettings=s=>{try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(s));}catch(e){}};
function recordSession(consult){
 if(!sessionId)sessionId=Date.now().toString(36)+Math.random().toString(36).slice(2,6);
 const list=loadRecords(),i=list.findIndex(r=>r.id===sessionId);
 const rec={id:sessionId,at:i>=0?list[i].at:new Date().toISOString(),device:loadSettings().device,answers:history.map(h=>({q:h.id,a:h.answer})),symptom:symKey(),next:nextKey(),consult:consult || (i>=0?list[i].consult:null),outcome:i>=0?(list[i].outcome||null):null,sent:false};
 if(i>=0)list[i]=rec;else list.push(rec);
 saveRecords(list);
 syncRecords();
}
// 受付の結果（スタッフが記録する）　値は counter / takein（そのステップで受付）・lost（見送り）・null（未記入）
function setOutcome(id,value){
 const list=loadRecords(),i=list.findIndex(r=>r.id===id);
 if(i<0)return;
 list[i].outcome=value || null;
 list[i].sent=false;
 saveRecords(list);
 syncRecords();
}
const outcomeLabel=v=>v==='lost'?'見送り':NEXT[v]?'受付':'未記入';
const outcomeNext=v=>NEXT[v]?NEXT[v].name:'';
const answerLabel=(q,a)=>q==='symptom'?(SYMPTOMS[a]?SYMPTOMS[a].label:a):a==='yes'?'はい':'いいえ';
const ansOf=(r,id)=>{const x=r.answers.find(v=>v.q===id);return x?answerLabel(id,x.a):'';};
const symptomName=r=>SYMPTOMS[r.symptom]?SYMPTOMS[r.symptom].label:'';
const consultLabel=c=>c==='yes'?'受付を進める':c==='no'?'保留':'未選択';
const when=iso=>{const d=new Date(iso),p=n=>String(n).padStart(2,'0');return d.getFullYear()+'/'+p(d.getMonth()+1)+'/'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());};
// 未送信の記録を1件ずつ受付窓口へ送る　同じお客様の記録は上書きされる　電波がないときは次の機会に送る
function toRow(r){
 return {id:r.id,at:when(r.at),device:r.device || loadSettings().device,symptom:symptomName(r),next:NEXT[r.next]?NEXT[r.next].name:'',data:ansOf(r,'data'),pcpass:ansOf(r,'pcpass'),change:ansOf(r,'change'),consult:consultLabel(r.consult),outcome:outcomeLabel(r.outcome),outcomeNext:outcomeNext(r.outcome)};
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
   // 送信中にお客様が最後の選択を変えた場合は未送信のままにして次に送り直す
   if(i>=0&&JSON.stringify(list[i].answers)===JSON.stringify(r.answers)&&list[i].consult===r.consult&&(list[i].outcome||null)===(r.outcome||null)){list[i].sent=true;saveRecords(list);}
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
 const steps=NEXT_ORDER.map(k=>{const n=list.filter(r=>r.next===k).length;return `<tr><td class="q">${NEXT[k].name}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`;}).join('');
 const consults=['yes','no',null].map(c=>{const n=list.filter(r=>(r.consult||null)===c).length;return `<tr><td class="q">${consultLabel(c)}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`;}).join('');
 const won=list.filter(r=>NEXT[r.outcome]).length,lost=list.filter(r=>r.outcome==='lost').length,blank=total-won-lost;
 const outcomes=[['受付',won],['見送り',lost],['未記入',blank]].map(v=>`<tr><td class="q">${v[0]}</td><td class="num">${v[1]}<small>${pct(v[1],total)}%</small></td></tr>`).join('')+`<tr><td class="q"><b>受付率</b>（受付 ÷ 受付と見送りの合計）</td><td class="num">${won+lost?pct(won,won+lost)+'%':'-'}</td></tr>`;
 const wonSteps=NEXT_ORDER.map(k=>{const n=list.filter(r=>r.outcome===k).length;return `<tr><td class="q">${NEXT[k].name}</td><td class="num">${n}<small>${pct(n,won)}%</small></td></tr>`;}).join('');
 const people=list.slice().reverse().slice(0,300).map(r=>{
  const cells=QUESTION_IDS.map(id=>{const x=r.answers.find(v=>v.q===id);return x?`<td class="${x.a}">${answerLabel(id,x.a)}</td>`:'<td>-</td>';}).join('');
  return `<tr><td class="when">${when(r.at)}</td>${cells}<td class="q">${symptomName(r) || '-'}</td><td class="q">${NEXT[r.next]?NEXT[r.next].name:'-'}</td><td>${consultLabel(r.consult)}</td><td><select class="admin-outcome" data-id="${r.id}"><option value="">未記入</option>${NEXT_ORDER.map(k=>`<option value="${k}" ${r.outcome===k?'selected':''}>受付 ${NEXT[k].name}</option>`).join('')}<option value="lost" ${r.outcome==='lost'?'selected':''}>見送り</option></select></td></tr>`;
 }).join('');
 return `<section class="admin"><div class="admin-head"><div><span class="tag">スタッフ専用</span><h1>回答の集計</h1><p>このiPadで記録されたお客様 <b>${total}</b> 人　${set.url&&set.pass?`未送信 <b>${unsent}</b> 件`:'送信先か合言葉が未設定のためこのiPadの中だけに保存しています'}</p></div><div class="admin-actions"><button class="admin-button" data-action="admin-csv" ${total?'':'disabled'}>CSVで書き出す</button><button class="admin-button danger" data-action="admin-clear" ${total?'':'disabled'}>記録をすべて消す</button><button class="admin-button primary" data-action="admin-close">お客様の画面に戻る</button></div></div>
 <h2>このiPadの設定</h2><div class="admin-settings"><label>iPadの名前<input id="set-device" value="${esc(set.device)}" placeholder="例 iPad 1号機"></label><label>送信先URL（診断ナビ用の受付窓口を用意したら入力）<input id="set-url" value="${esc(set.url)}" placeholder="https://script.google.com/macros/s/…/exec" inputmode="url" autocapitalize="off" autocorrect="off"></label><label>合言葉<span class="pass-row"><input id="set-pass" type="password" value="${esc(set.pass)}" autocomplete="off" autocapitalize="off" autocorrect="off"><button type="button" class="admin-button small" data-action="admin-peek">見る</button></span></label><div class="admin-actions"><button class="admin-button primary" data-action="admin-save">設定を保存</button><button class="admin-button" data-action="admin-sync" ${set.url&&set.pass&&unsent?'':'disabled'}>未送信を今すぐ送る</button></div><p class="admin-note">${syncNote || 'すべてのiPadの集計はGoogleスプレッドシートに集まります　この画面の集計はこのiPadの分だけです'}</p></div>
 <div class="admin-two"><div><h2>受付の結果</h2><table class="admin-table"><tbody>${outcomes}</tbody></table></div><div><h2>受付した次のステップ</h2><table class="admin-table"><tbody>${wonSteps}</tbody></table></div></div>
 <div class="admin-two"><div><h2>お困りの症状（多い順）</h2><table class="admin-table"><tbody>${symptoms}</tbody></table></div><div><h2>おすすめした次のステップ</h2><table class="admin-table"><tbody>${steps}</tbody></table><h2>最後の選択</h2><table class="admin-table"><tbody>${consults}</tbody></table></div></div>
 <h2>質問ごとの集計（このiPadの分）</h2><div class="admin-scroll"><table class="admin-table"><thead><tr><th>問</th><th>質問</th><th>回答数</th><th>はい</th><th>いいえ</th><th>はいの割合</th></tr></thead><tbody>${rows}</tbody></table></div>
 <h2>お客様ごとの回答（新しい順）</h2><div class="admin-scroll"><table class="admin-table people"><thead><tr><th>日時</th>${QUESTION_IDS.map(id=>`<th>${QUESTIONS[id].short}</th>`).join('')}<th>お困りの症状</th><th>次のステップ</th><th>最後の選択</th><th>受付の結果（ここで記録・修正できます）</th></tr></thead><tbody>${people || `<tr><td colspan="${QUESTION_IDS.length+5}">まだ記録がありません</td></tr>`}</tbody></table></div></section>`;
}
function exportCsv(){
 const head=['日時','iPad',...QUESTION_IDS.map(id=>QUESTIONS[id].short),'お困りの症状','次のステップ','最後の選択','受付','受付した次のステップ'];
 const lines=loadRecords().map(r=>[when(r.at),r.device||'',...QUESTION_IDS.map(id=>ansOf(r,id)),symptomName(r),NEXT[r.next]?NEXT[r.next].name:'',consultLabel(r.consult),outcomeLabel(r.outcome),outcomeNext(r.outcome)]);
 const csv='﻿'+[head,...lines].map(row=>row.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const d=new Date(),p=n=>String(n).padStart(2,'0'),name='pc-shindan-navi-'+d.getFullYear()+p(d.getMonth()+1)+p(d.getDate())+'.csv';
 const file=new File([csv],name,{type:'text/csv'});
 if(navigator.canShare&&navigator.canShare({files:[file]})){navigator.share({files:[file],title:name}).catch(()=>{});return;}
 const a=document.createElement('a');a.href=URL.createObjectURL(file);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

const main=document.getElementById('main');
const FIRST=QUESTION_IDS[0];
let history=[],screen=FIRST;
const tick='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const cross='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" stroke-linecap="round"/></svg>';
function aside(stage){return `<aside class="sidebar"><div class="eyebrow">PC TROUBLE CHECK</div><h2>お困りの症状を<br>いっしょに<br>確かめる　</h2><div class="steps">${['質問に答える','診断の結果を見る','受付につなぐ'].map((t,i)=>`<div class="step ${stage===i?'current':stage>i?'complete':''}" ${stage===i?'aria-current="step"':''}><span class="step-index">${stage>i?'✓':i+1}</span><span>${t}</span></div>`).join('')}</div><div class="side-bottom"><strong class="reassurance"><span>わからないときは</span><span>だいたいで大丈夫</span></strong><br>近いと思うほうを<br>選んでください　</div></aside>`;}
function choice(answer,label,sub){return `<button class="choice ${answer==='no'?'no':''}" data-answer="${answer}"><span class="choice-label">${answer==='yes'?tick:cross}${label}</span><small>${sub}</small></button>`;}
function topline(label,n){return `<div class="topline"><span class="tag">${label}</span><span class="count"><b>${String(n).padStart(2,'0')}</b> / ${QUESTION_MAX}</span></div><div class="progress" aria-label="全${QUESTION_MAX}問中${n}問目">${Array.from({length:QUESTION_MAX},(_,i)=>i+1).map(i=>`<span class="${i<=n?'on':''}"></span>`).join('')}</div>`;}
function stepCards(key){return `<div class="pack-cards two">${NEXT_ORDER.map(k=>`<div class="pack-card ${k===key?'is-recommended':''}">${k===key?'<span class="pack-flag">おすすめの次のステップ</span>':''}<span class="pack-badge">${NEXT[k].badge}</span><h3>${phr(NEXT[k].parts)}</h3><p>${NEXT[k].desc}</p></div>`).join('')}</div>`;}
function staffBox(){
 const rec=loadRecords().find(r=>r.id===sessionId);
 if(!rec)return '';
 const cur=rec.outcome || '';
 const btn=(v,label)=>`<button class="staff-button ${cur===v?'is-on':''}" data-action="outcome" data-value="${v}">${label}</button>`;
 return `<div class="staff-box"><span class="staff-tag">スタッフ記入欄</span><p>${cur?'記録しました　押し直すと変更できます':'受付の結果を押してください'}</p><div class="staff-buttons">${NEXT_ORDER.map(k=>btn(k,'受付　'+NEXT[k].name)).join('')}${btn('lost','見送り')}</div></div>`;
}
function render(focus=true){
 let html,stage=0;
 if(screen==='admin'){main.innerHTML=`<div class="stage admin-stage">${adminView()}</div>`;window.scrollTo({top:0,behavior:'instant'});return;}
 if(QUESTIONS[screen]){
  const q=QUESTIONS[screen],n=history.length+1,first=screen===FIRST;
  html=`<section class="content fade-in ${first?'welcome':''}">${topline(q.label,n)}<div class="question-area">${first?`<p class="welcome-thanks">お困りのパソコン<br>いっしょに確認します　</p><p class="question-lead">${phr(['パソコンの診断には','<strong class="warn">基本診断費 '+FEE+'</strong>が','かかります　'])}</p>`:''}${q.lead?`<p class="question-lead">${phr(q.lead)}</p>`:''}<h1>${phr(q.title)}</h1><p class="helper">${q.help.map(phr).join('<br>')}</p></div><div class="choices">${choice('yes',q.yesLabel || 'はい',q.yes)}${choice('no',q.noLabel || 'いいえ',q.no)}</div><div class="navrow"><button class="text-button" data-action="back" ${history.length?'':'disabled'}>← ひとつ戻る</button><span class="navhint">どちらかをタップしてください</span></div></section>`;
 }else if(screen==='symptom'){
  const n=history.length+1;
  html=`<section class="content fade-in">${topline('お困りの症状',n)}<div class="question-area"><h1>${phr(['いちばん近い','お困りの症状を','ひとつ選んでください'])}</h1><p class="helper">${phr(['当てはまるものが複数あるときは','いちばん困っているものを','選んでください'])}<br>${phr(['詳しいことは','あとで担当者がお伺いします'])}</p></div><div class="choices symptoms">${SYMPTOM_ORDER.map(k=>`<button class="choice" data-answer="${k}"><span class="choice-label">${SYMPTOMS[k].label}</span><small>${SYMPTOMS[k].sub}</small></button>`).join('')}</div><div class="navrow"><button class="text-button" data-action="back">← ひとつ戻る</button><span class="navhint">どれかをタップしてください</span></div></section>`;
 }else if(screen==='result'){
  stage=1;const r=recommendation();
  html=`<section class="content result fade-in"><div class="topline"><span class="tag">${history.length}問のご回答から</span><span class="count">診断の結果</span></div><h1 class="support-catchphrase">${phr(r.cat.headline)}</h1>${stepCards(r.key)}<div class="recommendation is-pack"><span class="eyebrow">ご回答から見えたこと</span><ul>${r.reasons.map(t=>`<li>${t}</li>`).join('')}</ul></div><p class="micro">基本診断費は${FEE}です　診断の内容と料金は担当者がご案内します　お預かりの場合は 作業の前にデータの扱いを一緒に確認します</p><p class="prompt">この内容で受付を進めますか？</p><div class="choices">${choice('yes','はい受付を進める','受付の内容を確認する')}${choice('no','いいえいったん保留','今回の回答を確認する')}</div><div class="navrow"><button class="text-button" data-action="back">← 回答を見直す</button><button class="text-button" data-action="restart">最初からやり直す</button></div></section>`;
 }else{
  stage=2;const r=recommendation(),interested=screen==='handoff';
  html=`<section class="content handoff fade-in"><span class="tag">${interested?'受付内容の確認':'今回の回答まとめ'}</span><h1>${interested?'この画面を担当者にお見せください　':'必要になったときにご相談ください　'}</h1><p class="helper">${interested?'お困りの内容と次のステップを確認し 担当者がご案内するための画面です　':'今回の回答から次のステップをご提案しました　今すぐ決めなくても大丈夫です　'}</p><div class="recommendation is-pack"><span class="eyebrow">${interested?'お困りの症状':'今回の診断'}</span><span class="pack-badge">${r.step.name}</span><h2>${r.cat.label}</h2></div>${staffBox()}<ul class="answer-list">${history.map(h=>`<li><span>${h.id==='symptom'?'お困りの症状':titleText(QUESTIONS[h.id])}</span><b>${answerLabel(h.id,h.answer)}</b></li>`).join('')}</ul><p class="micro">基本診断費は${FEE}です　この画面では申込や予約は行われません　お預かりの手続きは担当者がご案内します　</p><div class="navrow"><button class="text-button" data-action="result">← 診断の結果に戻る</button><button class="text-button" data-action="restart">最初の質問へ</button></div></section>`;
 }
 const photo=screen===FIRST?'support-consultation':(QUESTIONS[screen]||screen==='symptom')?'laptop-setup':'support-consultation';
 main.innerHTML=`<div class="stage photo-${photo}">${aside(stage)}${html}</div>`;
 if(focus){main.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
}
main.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b||b.disabled)return;
 if(b.dataset.answer){
  const a=b.dataset.answer;
  if(QUESTIONS[screen]){history.push({id:screen,answer:a});screen=QUESTIONS[screen].next[a];}
  else if(screen==='symptom'){if(!SYMPTOMS[a])return;history.push({id:'symptom',answer:a});screen='result';recordSession();}
  else if(screen==='result'){recordSession(a);screen=a==='yes'?'handoff':'summary';}
 }else if(b.dataset.action==='back'){const prev=history.pop();if(prev)screen=prev.id;}
 else if(b.dataset.action==='restart'){history=[];screen=FIRST;sessionId=null;}
 else if(b.dataset.action==='admin-close'){history=[];screen=FIRST;sessionId=null;}
 else if(b.dataset.action==='outcome'){const rec=loadRecords().find(r=>r.id===sessionId);const v=b.dataset.value;setOutcome(sessionId,rec&&rec.outcome===v?null:v);const y=window.scrollY;render(false);window.scrollTo({top:y,behavior:'instant'});return;}
 else if(b.dataset.action==='admin-csv'){exportCsv();return;}
 else if(b.dataset.action==='admin-peek'){const i=document.getElementById('set-pass');i.type=i.type==='password'?'text':'password';b.textContent=i.type==='password'?'見る':'隠す';return;}
 else if(b.dataset.action==='admin-save'){const v=id=>document.getElementById(id).value.trim();saveSettings({device:v('set-device'),url:v('set-url'),pass:v('set-pass')});syncNote='設定を保存しました';syncRecords();}
 else if(b.dataset.action==='admin-sync'){syncNote='送信しています';syncRecords();}
 else if(b.dataset.action==='admin-clear'){if(!window.confirm('記録をすべて消します　元に戻せません　よろしいですか？'))return;saveRecords([]);}
 else if(b.dataset.action==='result')screen='result';
 render();
});
main.addEventListener('change',e=>{const s=e.target.closest('select.admin-outcome');if(!s)return;setOutcome(s.dataset.id,s.value);const y=window.scrollY;render(false);window.scrollTo({top:y,behavior:'instant'});});
for(const file of ['laptop-setup','support-consultation']){const img=new Image();img.src='photos/'+file+'.png';}
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();history=[];screen=FIRST;sessionId=null;render();});
// 裏メニュー：右上の「約2分・全4問」を3秒以内に5回タップ
let secretTaps=[];
document.querySelector('.header-note').addEventListener('click',()=>{const now=Date.now();secretTaps=secretTaps.filter(t=>now-t<3000);secretTaps.push(now);if(secretTaps.length>=5){secretTaps=[];screen='admin';syncNote='';render();syncRecords();}});
// アプリ化：オフラインでも動くようにする（https または localhost のときだけ）
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('sw.js').catch(()=>{});
render(false);
