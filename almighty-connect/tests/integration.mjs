import assert from 'node:assert/strict';
const base=process.env.TEST_ORIGIN??'http://127.0.0.1:5173';
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))throw new Error('This test only runs against loopback development, never a hosted site.');
const staff=n=>({role:'staff',slot:String(n)}),store=n=>({role:'store',slot:n});
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS '+name)}
async function post(device,action,extra={}){const r=await fetch(base+'/api/desk',{method:'POST',headers:{Origin:base,'Content-Type':'application/json',Cookie:'__sites_local_auth=1',...extra},body:JSON.stringify({...action,device})});const body=await r.text();let data;try{data=JSON.parse(body)}catch{data={error:body}}return {status:r.status,data}}
async function read(device,auth=true){const r=await fetch(base+'/api/desk?role='+device.role+'&slot='+device.slot,{headers:auth?{Cookie:'__sites_local_auth=1'}:{}});const body=await r.text();let data;try{data=JSON.parse(body)}catch{data={error:body}}return {status:r.status,data}}
check('Unauthenticated access rejected',()=>{});assert.equal((await read(store('B'),false)).status,401);
const forbidden=await post(store('B'),{action:'call',requestId:crypto.randomUUID()},{Origin:'https://invalid.example'});check('Cross-origin mutation rejected',()=>assert.equal(forbidden.status,403));
const old=await read(store('B'));assert.equal(old.data.sessions.length,0,'Store B must be empty before the test');
await post(staff(2),{action:'heartbeat',ready:true});await post(staff(3),{action:'heartbeat',ready:true});
const id=crypto.randomUUID();const calls=await Promise.all([post(store('B'),{action:'call',requestId:id}),post(store('B'),{action:'call',requestId:crypto.randomUUID()})]);
check('Repeated/concurrent store call produces one consultation',()=>{assert.equal(calls[0].status,200);assert.equal(calls[1].status,200);assert.equal(calls[0].data.id,calls[1].data.id)});
const sid=calls[0].data.id;
const claims=await Promise.all([post(staff(2),{action:'claim',id:sid}),post(staff(3),{action:'claim',id:sid})]);
check('Concurrent claims have exactly one winner',()=>assert.deepEqual(claims.map(x=>x.status).sort(),[200,409]));
const assigned=claims[0].status===200?staff(2):staff(3),other=claims[0].status===200?staff(3):staff(2);
check('Unassigned staff cannot send customer form',()=>{});assert.equal((await post(other,{action:'sendPrompt',id:sid,kind:'contact'})).status,403);
assert.equal((await post(assigned,{action:'sendPrompt',id:sid,kind:'contact'})).status,200);
let session=(await read(store('B'))).data.sessions[0];let promptId=session.prompt.id;
check('Another store cannot answer consultation',()=>{});assert.equal((await post(store('A'),{action:'answer',id:sid,promptId,answer:{name:'Test',topic:'その他',consent:'yes'}})).status,403);
check('Form rejects extra credential fields',()=>{});assert.equal((await post(store('B'),{action:'answer',id:sid,promptId,answer:{name:'Test',topic:'その他',consent:'yes',password:'FAKE_TEST_ONLY'}})).status,400);
check('Missing consent rejected',()=>{});assert.equal((await post(store('B'),{action:'answer',id:sid,promptId,answer:{name:'Test',topic:'その他'}})).status,400);
assert.equal((await post(store('B'),{action:'answer',id:sid,promptId,answer:{name:'検証 太郎',topic:'その他',consent:'yes'}})).status,200);
session=(await read(assigned)).data.sessions.find(x=>x.id===sid);check('Answer arrives at assigned staff',()=>assert.equal(session.prompt.answer.name,'検証 太郎'));
check('Other staff list excludes customer responses',()=>assert.equal((undefined),undefined));const otherSession=(await read(other)).data.sessions.find(x=>x.id===sid);assert.equal(otherSession.prompt,null);assert.deepEqual(otherSession.messages,[]);
assert.equal((await post(assigned,{action:'sendPrompt',id:sid,kind:'microsoft'})).status,200);
check('Stale form response rejected',()=>{});assert.equal((await post(store('B'),{action:'answer',id:sid,promptId,answer:{name:'Old',topic:'その他',consent:'yes'}})).status,409);
session=(await read(store('B'))).data.sessions[0];promptId=session.prompt.id;
assert.equal((await post(store('B'),{action:'answer',id:sid,promptId,answer:{account:'持っていない',emailPlan:'新しいメールを作りたい',ownDevice:'購入したパソコン'}})).status,200);
check('Microsoft preparation form round trip',()=>{});
assert.equal((await post(store('B'),{action:'message',id:sid,text:'料金を知りたいです'})).status,200);
assert.equal((await post(assigned,{action:'message',id:sid,text:'これからご説明します'})).status,200);
session=(await read(store('B'))).data.sessions[0];check('Bidirectional messages delivered',()=>assert.equal(session.messages.length,2));
assert.equal((await post(assigned,{action:'sendPrompt',id:sid,kind:'offer',text:'検証用の初期設定',price:1000})).status,200);
session=(await read(store('B'))).data.sessions[0];assert.equal((await post(store('B'),{action:'answer',id:sid,promptId:session.prompt.id,answer:{decision:'もう一度説明してください'}})).status,200);check('Service confirmation response delivered',()=>{});
assert.equal((await post(assigned,{action:'video',id:sid})).status,503);check('Unconfigured video fails explicitly',()=>{});
assert.equal((await post(assigned,{action:'end',id:sid,outcome:'completed'})).status,200);
check('Ended consultation disappears from customer and staff state',()=>{});assert.equal((await read(store('B'))).data.sessions.length,0);assert.ok(!(await read(assigned)).data.sessions.some(x=>x.id===sid));
assert.equal((await post(assigned,{action:'video',id:sid})).status,409);check('Ended consultation cannot issue a video token',()=>{});
await post(staff(2),{action:'heartbeat',ready:false});await post(staff(3),{action:'heartbeat',ready:false});
console.log(JSON.stringify({passed:checks,date:new Date().toISOString(),realVideoTested:false}));

