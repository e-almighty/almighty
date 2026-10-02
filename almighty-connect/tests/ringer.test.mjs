import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Ringer } from '../lib/ringer.ts';

function audio() {
 const nodes=[];
 return {state:'running',currentTime:0,destination:{},nodes,
 createOscillator(){const n={frequency:{setValueAtTime(){}},stopped:[],connect(){},disconnect(){},start(){},stop(at){this.stopped.push(at)}};nodes.push(n);return n},
 createGain(){return {gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}}}};
}
test('all four ringtones stop an in-progress tone when the shared call is answered',t=>{
 t.mock.timers.enable({apis:['setInterval']});
 const contexts=Array.from({length:4},audio);const rings=contexts.map(c=>new Ringer(c));
 rings.forEach(r=>r.start());assert.ok(contexts.every(c=>c.nodes.length===1));
 t.mock.timers.tick(4000);assert.ok(contexts.every(c=>c.nodes.length===2));
 rings.forEach(r=>r.stop());assert.ok(contexts.every(c=>c.nodes.every(n=>n.stopped.includes(undefined))));
 t.mock.timers.tick(20000);assert.ok(contexts.every(c=>c.nodes.length===2));
});
test('duplicate start does not double ring, and a later call can ring again',t=>{
 t.mock.timers.enable({apis:['setInterval']});const c=audio(),r=new Ringer(c);
 r.start();r.start();t.mock.timers.tick(4000);assert.equal(c.nodes.length,2);
 r.stop();r.start();assert.equal(c.nodes.length,3);r.stop();
});
test('a suspended audio context does not pretend to play',t=>{
 t.mock.timers.enable({apis:['setInterval']});const c=audio();c.state='suspended';const r=new Ringer(c);
 r.start();t.mock.timers.tick(8000);assert.equal(c.nodes.length,0);r.stop();
});
