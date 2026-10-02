import assert from 'node:assert/strict';
const base='http://127.0.0.1:5173';
const staff=n=>({role:'staff',slot:String(n)}),store={role:'store',slot:'A'};
const headers={Origin:base,'Content-Type':'application/json',Cookie:'__sites_local_auth=1'};
async function post(device,action){const r=await fetch(base+'/api/desk',{method:'POST',headers,body:JSON.stringify({...action,device})});return {status:r.status,data:await r.json()}}
async function read(device){const r=await fetch(base+'/api/desk?role='+device.role+'&slot='+device.slot,{headers});assert.equal(r.status,200);return r.json()}
for(const s of (await read(store)).sessions)await post(store,{action:'end',id:s.id,outcome:'cancelled'});
for(let n=1;n<=5;n++)assert.equal((await post(staff(n),{action:'heartbeat',ready:true})).status,200);
const response=await post(store,{action:'call',requestId:crypto.randomUUID()});assert.equal(response.status,200);const id=response.data.id;
const before=await Promise.all([1,2,3,4,5].map(n=>read(staff(n))));assert.ok(before.every(s=>s.sessions.some(c=>c.id===id&&c.status==='waiting')));
console.log('PASS one store call is visible as incoming on all five reception endpoints');
assert.equal((await post(staff(5),{action:'claim',id})).status,200);
const after=await Promise.all([1,2,3,4,5].map(n=>read(staff(n))));assert.ok(after.every(s=>!s.sessions.some(c=>c.id===id&&c.status==='waiting')));assert.ok(after.every(s=>s.sessions.find(c=>c.id===id).staff==='5'));
console.log('PASS business endpoint answer clears incoming state for all four iPads');
assert.equal((await post(staff(2),{action:'claim',id})).status,409);console.log('PASS a late answer cannot take over the call');
assert.equal((await post(staff(5),{action:'end',id,outcome:'completed'})).status,200);
for(let n=1;n<=5;n++)await post(staff(n),{action:'heartbeat',ready:false});
console.log('3 ring-group API checks passed; physical device audio remains untested.');

