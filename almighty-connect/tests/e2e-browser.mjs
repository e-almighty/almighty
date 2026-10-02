// Browser end-to-end check with headless Chromium (Playwright).
// Caller "/" -> receivers "/reception" and "/staff/2" -> incoming shown on both
// -> first answer wins -> other receiver's incoming stops -> end -> back to idle.
// Run: npm run dev (port 5173) then: node tests/e2e-browser.mjs
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
let chromium;
try{({chromium}=require('playwright'));}catch{({chromium}=require('/opt/node22/lib/node_modules/playwright'));}
const base=process.env.BASE_URL??'http://127.0.0.1:5173';
const legacy=process.argv.includes('--legacy-ipad');// emulate an iPad without crypto.randomUUID / AbortSignal.timeout
const browser=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
async function open(path,slot){
 const context=await browser.newContext({viewport:{width:1024,height:768},userAgent:'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'});
 await context.addCookies([{name:'__sites_local_auth',value:'1',url:base}]);
 // This sandbox cannot reach Google; serve a stub so the navigation target can be asserted.
 await context.route('https://meet.google.com/**',route=>route.fulfill({contentType:'text/html',body:'<title>meet stub</title>Google Meet stub'}));
 if(legacy)await context.addInitScript(()=>{delete Crypto.prototype.randomUUID;delete AbortSignal.timeout;});
 const page=await context.newPage();
 page.on('pageerror',e=>console.log('  [pageerror '+path+']',e.message));
 if(slot)await page.addInitScript(([k,v])=>localStorage.setItem(k,v),['almighty-staff-slot',slot]);
 await page.goto(base+path,{waitUntil:'domcontentloaded'});
 return {context,page};
}
const t0=Date.now();const log=m=>console.log(((Date.now()-t0)/1000).toFixed(1)+'s '+m);
// clean any open store A consultation left by earlier runs (local verification DB only)
{const h={'Content-Type':'application/json',Origin:base,Cookie:'__sites_local_auth=1'};const st=await (await fetch(base+'/api/desk?role=store&slot=A',{headers:h})).json();for(const s of st.sessions)await fetch(base+'/api/desk',{method:'POST',headers:h,body:JSON.stringify({action:'end',id:s.id,outcome:'cancelled',device:{role:'store',slot:'A'}})});}
const caller=await open('/'),r1=await open('/reception','1'),r2=await open('/staff/2');
try{
 await caller.page.getByRole('button',{name:'三宮を呼び出す'}).waitFor({timeout:20000});
 for(const r of [r1,r2])await r.page.getByText('着信をお待ちしています').waitFor({timeout:20000});
 for(const r of [caller,r1,r2])await r.page.getByText('ログイン: seedy@sites.test').first().waitFor({timeout:10000});
 log('both receivers idle; caller ready; same account shown on all three screens');
 // receiver 1 enables the ringtone (sound-only step)
 await r1.page.getByRole('button',{name:'着信音を有効にする'}).click();
 await r1.page.getByText('着信音を有効にしました').waitFor({timeout:5000});
 log('receiver 1 ringtone enabled');
 // caller presses the single main button; a Meet tab is prepared
 const popup=caller.context.waitForEvent('page',{timeout:10000}).catch(()=>null);
 await caller.page.getByRole('button',{name:'三宮を呼び出す'}).click();
 await caller.page.getByText('三宮のスタッフを呼び出しています').waitFor({timeout:15000});
 const callerPopup=await popup;log('caller is calling; popup='+(callerPopup?'yes':'no'));
 if(callerPopup){await callerPopup.waitForURL(/meet\.google\.com/,{timeout:15000}).catch(()=>{});log('caller popup url='+callerPopup.url());assert.match(callerPopup.url(),/meet\.google\.com\/hom-rzvi-dbm/);}
 // both receivers show the incoming call
 for(const r of [r1,r2]){await r.page.getByText('店舗から呼び出しです').waitFor({timeout:10000});await r.page.getByRole('button',{name:'応答する'}).waitFor({timeout:5000});}
 log('incoming shown on receiver 1 and receiver 2');
 const ringing=await r1.page.locator('.welcome-icon.ringing').count();assert.ok(ringing,'ringing indicator');
 // receiver 2 answers first
 const popup2=r2.context.waitForEvent('page',{timeout:10000}).catch(()=>null);
 await r2.page.getByRole('button',{name:'応答する'}).click();
 await r2.page.getByText('店舗 A のお客様').waitFor({timeout:15000});
 const p2=await popup2;if(p2){await p2.waitForURL(/meet\.google\.com/,{timeout:15000}).catch(()=>{});assert.match(p2.url(),/meet\.google\.com/);}
 log('receiver 2 answered; Meet tab='+(p2?p2.url():'none'));
 // receiver 1 incoming stops
 await r1.page.getByText('着信をお待ちしています').waitFor({timeout:10000});
 assert.equal(await r1.page.getByRole('button',{name:'応答する'}).count(),0);
 log('receiver 1 incoming stopped');
 // caller sees the assigned staff
 await caller.page.getByText('三宮 受付 2 がご案内します').waitFor({timeout:10000});
 // message both ways
 await r2.page.getByRole('textbox',{name:'メッセージ'}).fill('こんにちは、三宮です');await r2.page.getByLabel('メッセージを送信').click();
 await caller.page.getByText('こんにちは、三宮です').waitFor({timeout:10000});
 await caller.page.getByRole('button',{name:'料金を知りたいです'}).click();
 await r2.page.getByText('料金を知りたいです').waitFor({timeout:10000});
 log('messages delivered both ways');
 // staff sends the contact form; customer answers
 await r2.page.getByRole('button',{name:'お客様の画面に表示する'}).click();
 await caller.page.getByText('ご相談について教えてください').waitFor({timeout:10000});
 await caller.page.getByPlaceholder('例：テスト 太郎').fill('テスト 太郎');
 await caller.page.getByText('パソコンの初期設定',{exact:true}).click();
 await caller.page.locator('label.consent').click();
 await caller.page.getByRole('button',{name:'三宮スタッフに送信する'}).click();
 await r2.page.getByText('回答を受け取りました').waitFor({timeout:10000});
 log('form sent and answered');
 // end
 await r2.page.getByRole('button',{name:'相談を終了'}).click();
 await r2.page.getByRole('button',{name:'終了して内容を消去'}).click();
 await r2.page.getByText('着信をお待ちしています').waitFor({timeout:10000});
 await caller.page.getByText('ご相談ありがとうございました').waitFor({timeout:10000});
 log('ended; both back to idle');
 console.log('PASS e2e: call -> incoming on 2 receivers -> first answer wins -> other stops -> messages/form -> end'+(legacy?' (legacy iPad emulation)':''));
}catch(e){
 console.log('FAIL',e.message);
 for(const [n,r] of [['caller',caller],['r1',r1],['r2',r2]]){await r.page.screenshot({path:process.env.SHOT_DIR?process.env.SHOT_DIR+'/'+n+'.png':'/tmp/e2e-'+n+'.png'}).catch(()=>{});console.log('  '+n+': '+(await r.page.locator('main').innerText().catch(()=>'')).replace(/\s+/g,' ').slice(0,300));}
 process.exitCode=1;
}finally{await browser.close();}
