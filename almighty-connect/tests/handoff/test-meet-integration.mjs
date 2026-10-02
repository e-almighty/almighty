import assert from 'node:assert/strict';
const base='http://127.0.0.1:5173';
const store={role:'store',slot:'A'},staff=Array.from({length:5},(_,i)=>({role:'staff',slot:String(i+1)}));
async function post(device,action){const r=await fetch(base+'/api/desk',{method:'POST',headers:{'Content-Type':'application/json',Origin:base,Cookie:'__sites_local_auth=1'},body:JSON.stringify({device,...action})});return {status:r.status,data:await r.json()};}
async function state(d){const r=await fetch(base+'/api/desk?role='+d.role+'&slot='+d.slot,{headers:{Cookie:'__sites_local_auth=1'}});assert.equal(r.status,200);return r.json();}
let id;
try{
 for(const s of (await state(store)).sessions)await post(store,{action:'end',id:s.id,outcome:'cancelled'});
 for(const d of staff)assert.equal((await post(d,{action:'heartbeat',ready:true})).status,200);
 const called=await post(store,{action:'call',requestId:crypto.randomUUID()});assert.equal(called.status,200);id=called.data.id;
 for(const d of staff)assert.equal((await state(d)).sessions.filter(s=>s.status==='waiting').length,1);
 const claims=await Promise.all(staff.map(d=>post(d,{action:'claim',id})));
 assert.equal(claims.filter(r=>r.status===200).length,1);assert.equal(claims.filter(r=>r.status===409).length,4);
 const winner=staff[claims.findIndex(r=>r.status===200)];
 for(const d of staff)assert.equal((await state(d)).sessions.filter(s=>s.status==='waiting').length,0);
 const video=await post(winner,{action:'video',id});assert.equal(video.status,200);assert.equal(video.data.url,'https://meet.google.com/hom-rzvi-dbm');assert.equal(video.data.provider,'google-meet');assert.equal(video.data.token,undefined);
 const loser=staff.find(d=>d!==winner);assert.equal((await post(loser,{action:'video',id})).status,403);
 assert.equal((await post({role:'store',slot:'B'},{action:'call',requestId:crypto.randomUUID()})).status,503);
 const ended=await post(winner,{action:'end',id,outcome:'completed'});assert.equal(ended.status,200);assert.equal(ended.data.videoClosed,false);
 assert.equal((await state(store)).sessions.length,0);
 console.log('PASS: all 5 receivers see call; one claim wins; other queues clear; Meet URL; unauthorized denial; unconfigured store denial; honest manual Meet end; cleanup.');
}finally{
 if(id){await post(store,{action:'end',id,outcome:'cancelled'});}
 for(const d of staff)await post(d,{action:'heartbeat',ready:false});
}
