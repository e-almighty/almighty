// D1-backed VAPID key storage and push delivery for the Worker. Pure crypto lives in webpush-crypto.ts.
import {db} from './server';
import {encryptPayload,vapidAuthorization,generateVapidKeys,toB64u,fromB64u,type VapidKeys,type PushSubscriptionRow} from './webpush-crypto';
export * from './webpush-crypto';
function concat(...parts:Uint8Array[]):Uint8Array{const n=parts.reduce((a,p)=>a+p.length,0);const out=new Uint8Array(n);let o=0;for(const p of parts){out.set(p,o);o+=p.length;}return out;}
let cached:VapidKeys|null=null;
/** Loads the shared VAPID pair from D1, generating it on first use. */
export async function vapidKeys():Promise<VapidKeys>{
 if(cached)return cached;
 const read=async()=>db().prepare('SELECT public_jwk,private_jwk FROM push_keys WHERE id=?').bind('vapid').first<{public_jwk:string;private_jwk:string}>();
 let row=await read();
 if(!row){const fresh=await generateVapidKeys();await db().prepare('INSERT OR IGNORE INTO push_keys(id,public_jwk,private_jwk,created) VALUES(?,?,?,?)').bind('vapid',JSON.stringify(fresh.publicJwk),JSON.stringify(fresh.privateJwk),Date.now()).run();row=await read();}
 if(!row)throw new Error('push keys unavailable');
 const publicJwk=JSON.parse(row.public_jwk) as JsonWebKey,privateJwk=JSON.parse(row.private_jwk) as JsonWebKey;
 const raw=concat(new Uint8Array([4]),fromB64u(publicJwk.x!),fromB64u(publicJwk.y!));
 cached={publicJwk,privateJwk,publicKey:toB64u(raw)};
 return cached;
}

/** Sends one push. Returns the push service status; 404/410 mean the subscription is gone. */
export async function sendPush(sub:PushSubscriptionRow,payload:unknown,subject:string,ttl=120):Promise<number>{
 const keys=await vapidKeys();
 const body=await encryptPayload(sub.p256dh,sub.auth,JSON.stringify(payload));
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),8000);
 try{
  const r=await fetch(sub.endpoint,{method:'POST',headers:{Authorization:await vapidAuthorization(sub.endpoint,keys,subject),'Content-Encoding':'aes128gcm','Content-Type':'application/octet-stream',TTL:String(ttl),Urgency:'high',Topic:'almighty-call'},body:body as BufferSource,signal:controller.signal});
  return r.status;
 }catch{return 0;}finally{clearTimeout(timer);}
}
