// Lock-screen alert flow against the local dev server: a reception endpoint subscribes with real
// keys, a store calls, and a local stand-in for the push service receives an encrypted, VAPID-signed
// push that decrypts to the call notification. Then a repeat alert arrives while still unanswered,
// and no alert goes to a receiver that is already busy.
// Run: npm run dev, then: node --experimental-strip-types tests/push-flow.mjs
import assert from 'node:assert/strict';
import http from 'node:http';
import {makeSubscription,decryptPayload} from './webpush.test.mjs';
import {fromB64u} from '../lib/webpush-crypto.ts';
const base='http://127.0.0.1:5173';
const H={'Content-Type':'application/json',Origin:base,Cookie:'__sites_local_auth=1'};
const store={role:'store',slot:'A'},staff1={role:'staff',slot:'1'},staff2={role:'staff',slot:'2'};
const post=async(device,action)=>{const r=await fetch(base+'/api/desk',{method:'POST',headers:H,body:JSON.stringify({device,...action})});return {status:r.status,data:await r.json()};};
const state=async(d)=>(await fetch(base+'/api/desk?role='+d.role+'&slot='+d.slot,{headers:H})).json();
const wait=ms=>new Promise(r=>setTimeout(r,ms));

const received=[];
const server=http.createServer((req,res)=>{const chunks=[];req.on('data',c=>chunks.push(c));req.on('end',()=>{received.push({path:req.url,headers:req.headers,body:new Uint8Array(Buffer.concat(chunks))});res.statusCode=201;res.end();});});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const pushBase='http://127.0.0.1:'+server.address().port;
let id;
try{
 for(const s of (await state(store)).sessions)await post(store,{action:'end',id:s.id,outcome:'cancelled'});
 const key=(await state(staff1)).pushPublicKey;assert.ok(key,'staff state carries the VAPID public key');assert.equal(fromB64u(key).length,65);
 const sub1=await makeSubscription(pushBase+'/push/slot1'),sub2=await makeSubscription(pushBase+'/push/slot2');
 assert.equal((await post(staff1,{action:'subscribe',subscription:sub1.json})).status,200);
 assert.equal((await post(staff2,{action:'subscribe',subscription:sub2.json})).status,200);
 assert.equal((await post(store,{action:'subscribe',subscription:sub1.json})).status,403,'store devices cannot subscribe as receivers');
 const call=await post(store,{action:'call',requestId:crypto.randomUUID()});assert.equal(call.status,200);id=call.data.id;
 await wait(500);
 assert.equal(received.length,2,'both receivers get the first alert at the call');
 const first=received.find(r=>r.path==='/push/slot1');
 assert.match(first.headers.authorization,/^vapid t=.+, k=/);assert.equal(first.headers['content-encoding'],'aes128gcm');assert.equal(first.headers.urgency,'high');
 const text=JSON.parse(await decryptPayload(sub1.receiver,sub1.authSecret,first.body));
 assert.equal(text.title,'店舗 A から呼び出しです');assert.equal(text.url,'/reception');
 console.log('PASS first lock-screen alert: encrypted + VAPID-signed push received by both receivers and decrypts to the call');
 // the caller keeps polling; no repeat before the interval
 await state(store);await wait(300);assert.equal(received.length,2,'no repeat inside the interval');
 console.log('waiting 26s for the repeat alert...');await wait(26000);await state(store);await wait(500);
 assert.equal(received.length,4,'repeat alert sent to both receivers while still unanswered');
 console.log('PASS repeat alert while unanswered');
 // receiver 2 answers: no further alerts
 assert.equal((await post(staff2,{action:'claim',id})).status,200);
 await state(store);await wait(300);assert.equal(received.length,4,'no alert after the call was answered');
 console.log('PASS alerts stop once answered');
 assert.equal((await post(staff2,{action:'end',id,outcome:'completed'})).status,200);id=null;
 // after the previous call ended, a new call alerts both receivers again
 const callB=await post(store,{action:'call',requestId:crypto.randomUUID()});id=callB.data.id;await wait(500);
 assert.equal(received.filter(r=>r.path==='/push/slot1').length,3);assert.equal(received.filter(r=>r.path==='/push/slot2').length,3);
 await post(store,{action:'end',id,outcome:'cancelled'});id=null;
 // unsubscribe removes the endpoint
 assert.equal((await post(staff1,{action:'unsubscribe',endpoint:sub1.json.endpoint})).status,200);
 assert.equal((await post(staff2,{action:'unsubscribe',endpoint:sub2.json.endpoint})).status,200);
 const callC=await post(store,{action:'call',requestId:crypto.randomUUID()});id=callC.data.id;await wait(500);
 assert.equal(received.length,6,'no push after unsubscribe');
 console.log('PASS unsubscribe stops alerts. Lock-screen alert flow verified end to end (local push stand-in).');
}finally{
 if(id)await post(store,{action:'end',id,outcome:'cancelled'});
 server.close();
}
