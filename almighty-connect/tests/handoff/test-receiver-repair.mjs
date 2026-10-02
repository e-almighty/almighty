import assert from 'node:assert/strict';
import {resumeAudio} from '../../lib/audio-unlock.ts';
import {deskRequest} from '../../lib/desk-request.ts';
const originalFetch=globalThis.fetch;
// An audio permission promise that never settles must not hang indefinitely.
await assert.rejects(resumeAudio({resume:()=>new Promise(()=>{}),state:'suspended'},20));
globalThis.fetch=async()=>new Response(JSON.stringify({ok:true}),{headers:{'Content-Type':'application/json'}});
assert.deepEqual(await deskRequest('/test'),{ok:true});
globalThis.fetch=(_,options)=>new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted'))));
await assert.rejects(deskRequest('/test',{},20),/通信が遅れています/);
globalThis.fetch=originalFetch;
const base='http://127.0.0.1:5173';
const staff={role:'staff',slot:'1'},store={role:'store',slot:'A'};
async function post(device,action){const r=await fetch(base+'/api/desk',{method:'POST',headers:{'Content-Type':'application/json',Origin:base,Cookie:'__sites_local_auth=1'},body:JSON.stringify({device,...action})});return {status:r.status,data:await r.json()};}
async function state(){return (await fetch(base+'/api/desk?role=store&slot=A',{headers:{Cookie:'__sites_local_auth=1'}})).json();}
const receiver=crypto.randomUUID(),idle=crypto.randomUUID();let id;
try{
 assert.equal((await post(staff,{action:'heartbeat',ready:true,clientId:receiver})).status,200);
 assert.equal((await post(staff,{action:'heartbeat',ready:false,clientId:idle})).status,200);
 assert.equal((await state()).available,1,'second idle receiver must not disable first');
 await post(staff,{action:'heartbeat',ready:false});
 assert.equal((await state()).available,1,'older idle page must not disable receiver');
 await post(staff,{action:'heartbeat',ready:false,clientId:receiver});
 const call=await post(store,{action:'call',requestId:crypto.randomUUID()});assert.equal(call.status,200);id=call.data.id;
 assert.equal((await post(staff,{action:'claim',id})).status,200,'answer must work without audio/ready registration');
 assert.equal((await post({role:'staff',slot:'2'},{action:'claim',id})).status,409,'second receiver must not steal call');
 console.log('PASS: stalled audio is bounded; compatible request timeout; independent receivers; stale page isolation; answer without readiness; first answer wins.');
}finally{
 if(id)await post(store,{action:'end',id,outcome:'cancelled'});
 await post(staff,{action:'heartbeat',ready:false,clientId:receiver});
}
