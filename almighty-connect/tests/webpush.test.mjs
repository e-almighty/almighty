// Verifies the Worker-side Web Push encryption and VAPID signing against an independent decryptor.
// Run: node --experimental-strip-types --test tests/webpush.test.mjs
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {encryptPayload,vapidAuthorization,generateVapidKeys,toB64u,fromB64u} from '../lib/webpush-crypto.ts';

const te=new TextEncoder(),td=new TextDecoder();
async function hkdf(salt,ikm,info,len){const k=await crypto.subtle.importKey('raw',ikm,'HKDF',false,['deriveBits']);return new Uint8Array(await crypto.subtle.deriveBits({name:'HKDF',hash:'SHA-256',salt,info},k,len*8));}
function cat(...p){const n=p.reduce((a,x)=>a+x.length,0),o=new Uint8Array(n);let i=0;for(const x of p){o.set(x,i);i+=x.length;}return o;}

// RFC 8291 decryption as a browser/push service would do it.
export async function decryptPayload(receiver,authSecret,body){
 const salt=body.slice(0,16),rs=new DataView(body.buffer,body.byteOffset+16,4).getUint32(0),idlen=body[20],senderPub=body.slice(21,21+idlen),cipher=body.slice(21+idlen);
 assert.equal(idlen,65);assert.equal(rs,4096);
 const receiverPub=new Uint8Array(await crypto.subtle.exportKey('raw',receiver.publicKey));
 const senderKey=await crypto.subtle.importKey('raw',senderPub,{name:'ECDH',namedCurve:'P-256'},false,[]);
 const shared=new Uint8Array(await crypto.subtle.deriveBits({name:'ECDH',public:senderKey},receiver.privateKey,256));
 const ikm=await hkdf(authSecret,shared,cat(te.encode('WebPush: info\0'),receiverPub,senderPub),32);
 const cek=await hkdf(salt,ikm,te.encode('Content-Encoding: aes128gcm\0'),16),nonce=await hkdf(salt,ikm,te.encode('Content-Encoding: nonce\0'),12);
 const key=await crypto.subtle.importKey('raw',cek,'AES-GCM',false,['decrypt']);
 const plain=new Uint8Array(await crypto.subtle.decrypt({name:'AES-GCM',iv:nonce},key,cipher));
 assert.equal(plain[plain.length-1],2,'last record delimiter');
 return td.decode(plain.slice(0,-1));
}

export async function makeSubscription(endpoint){
 const receiver=await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},true,['deriveBits']);
 const authSecret=crypto.getRandomValues(new Uint8Array(16));
 return {receiver,authSecret,json:{endpoint,keys:{p256dh:toB64u(new Uint8Array(await crypto.subtle.exportKey('raw',receiver.publicKey))),auth:toB64u(authSecret)}}};
}

test('payload encrypted for a subscription decrypts to the same JSON',async()=>{
 const sub=await makeSubscription('https://push.example/abc');
 const body=await encryptPayload(sub.json.keys.p256dh,sub.json.keys.auth,JSON.stringify({title:'店舗 A から呼び出しです'}));
 assert.deepEqual(JSON.parse(await decryptPayload(sub.receiver,sub.authSecret,body)),{title:'店舗 A から呼び出しです'});
});

test('VAPID header carries a JWT the public key verifies, scoped to the push origin',async()=>{
 const keys=await generateVapidKeys();
 const header=await vapidAuthorization('https://web.push.apple.com/QWxs',keys,'https://almighty.example');
 const m=/^vapid t=([^,]+), k=(.+)$/.exec(header);assert.ok(m);
 assert.equal(m[2],keys.publicKey);assert.equal(fromB64u(keys.publicKey).length,65);
 const [h,b,sig]=m[1].split('.');
 const claims=JSON.parse(td.decode(fromB64u(b)));assert.equal(claims.aud,'https://web.push.apple.com');assert.equal(claims.sub,'https://almighty.example');assert.ok(claims.exp>Date.now()/1000);
 const pub=await crypto.subtle.importKey('jwk',keys.publicJwk,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
 assert.ok(await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},pub,fromB64u(sig),te.encode(h+'.'+b)));
});
