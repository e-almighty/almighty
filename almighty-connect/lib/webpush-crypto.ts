// Web Push (RFC 8030/8291/8292) with WebCrypto only, so it runs inside the Cloudflare Worker.
// The VAPID key pair is generated once and kept in D1 (push_keys), so the owner needs no setup.

export type PushSubscriptionRow={endpoint:string;p256dh:string;auth:string};
export type VapidKeys={publicJwk:JsonWebKey;privateJwk:JsonWebKey;publicKey:string};

const te=new TextEncoder();
export function toB64u(buf:ArrayBuffer|Uint8Array):string{const b=buf instanceof Uint8Array?buf:new Uint8Array(buf);let s='';for(const x of b)s+=String.fromCharCode(x);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
export function fromB64u(s:string):Uint8Array{s=s.replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';const bin=atob(s);const out=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out;}
function concat(...parts:Uint8Array[]):Uint8Array{const n=parts.reduce((a,p)=>a+p.length,0);const out=new Uint8Array(n);let o=0;for(const p of parts){out.set(p,o);o+=p.length;}return out;}
async function hkdf(salt:Uint8Array,ikm:Uint8Array,info:Uint8Array,length:number):Promise<Uint8Array>{const key=await crypto.subtle.importKey('raw',ikm as BufferSource,'HKDF',false,['deriveBits']);return new Uint8Array(await crypto.subtle.deriveBits({name:'HKDF',hash:'SHA-256',salt:salt as BufferSource,info:info as BufferSource},key,length*8));}

/** Encrypts a payload for one subscription (aes128gcm content encoding, single record). */
export async function encryptPayload(p256dh:string,auth:string,plaintext:string):Promise<Uint8Array>{
 const receiverPublic=fromB64u(p256dh),authSecret=fromB64u(auth);
 const local=await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},true,['deriveBits']) as CryptoKeyPair;
 const localPublic=new Uint8Array(await crypto.subtle.exportKey('raw',local.publicKey));
 const remoteKey=await crypto.subtle.importKey('raw',receiverPublic as BufferSource,{name:'ECDH',namedCurve:'P-256'},false,[]);
 const shared=new Uint8Array(await crypto.subtle.deriveBits({name:'ECDH',public:remoteKey},local.privateKey,256));
 const ikm=await hkdf(authSecret,shared,concat(te.encode('WebPush: info\0'),receiverPublic,localPublic),32);
 const salt=crypto.getRandomValues(new Uint8Array(16));
 const cek=await hkdf(salt,ikm,te.encode('Content-Encoding: aes128gcm\0'),16);
 const nonce=await hkdf(salt,ikm,te.encode('Content-Encoding: nonce\0'),12);
 const aesKey=await crypto.subtle.importKey('raw',cek as BufferSource,'AES-GCM',false,['encrypt']);
 const padded=concat(te.encode(plaintext),new Uint8Array([2]));
 const cipher=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce as BufferSource},aesKey,padded as BufferSource));
 const rs=4096;const header=concat(salt,new Uint8Array([(rs>>>24)&255,(rs>>>16)&255,(rs>>>8)&255,rs&255]),new Uint8Array([localPublic.length]),localPublic);
 return concat(header,cipher);
}

/** Builds the VAPID Authorization header for the push service that owns the endpoint. */
export async function vapidAuthorization(endpoint:string,keys:VapidKeys,subject:string):Promise<string>{
 const aud=new URL(endpoint).origin;const exp=Math.floor(Date.now()/1000)+12*3600;
 const head=toB64u(te.encode(JSON.stringify({typ:'JWT',alg:'ES256'})));const body=toB64u(te.encode(JSON.stringify({aud,exp,sub:subject})));
 const key=await crypto.subtle.importKey('jwk',keys.privateJwk,{name:'ECDSA',namedCurve:'P-256'},false,['sign']);
 const signature=new Uint8Array(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},key,te.encode(head+'.'+body)));
 return `vapid t=${head}.${body}.${toB64u(signature)}, k=${keys.publicKey}`;
}

export async function generateVapidKeys():Promise<VapidKeys>{
 const pair=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']) as CryptoKeyPair;
 const publicJwk=await crypto.subtle.exportKey('jwk',pair.publicKey),privateJwk=await crypto.subtle.exportKey('jwk',pair.privateKey);
 return {publicJwk,privateJwk,publicKey:toB64u(new Uint8Array(await crypto.subtle.exportKey('raw',pair.publicKey)))};
}

