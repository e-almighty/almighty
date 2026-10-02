import {db,save} from './server';
import {sendPush} from './webpush';
import type {Session} from './contracts';
// Lock-screen alerts while a call is waiting: first at the call, then every ALERT_INTERVAL until answered.
export const ALERT_INTERVAL=25000,ALERT_MAX=5;
type SubscriptionRow={endpoint:string;slot:string;p256dh:string;auth:string};
export async function alertReceivers(tenant:string,s:Session,subject:string){
 if(s.status!=='waiting')return;
 const pushes=s.pushes??0;
 if(pushes>=ALERT_MAX||(pushes>0&&Date.now()-(s.lastPush??0)<ALERT_INTERVAL))return;
 const subs=(await db().prepare('SELECT endpoint,slot,p256dh,auth FROM push_subscriptions WHERE tenant=?').bind(tenant).all()).results as SubscriptionRow[];
 const active=((await db().prepare("SELECT staff FROM consultations WHERE tenant=? AND status='active'").bind(tenant).all()).results as {staff:string}[]).map(r=>r.staff);
 const targets=subs.filter(x=>!active.includes(x.slot));
 if(!targets.length)return;
 // Record the attempt before sending so concurrent polls do not double-send.
 s.pushes=pushes+1;s.lastPush=Date.now();
 try{await save(tenant,s);s.version++;}catch{return;}
 const payload={title:'店舗 '+s.store+' から呼び出しです',body:'受付画面を開いて「応答する」を押してください。',url:'/reception'};
 await Promise.all(targets.map(async t=>{const status=await sendPush(t,payload,subject);if(status===404||status===410)await db().prepare('DELETE FROM push_subscriptions WHERE endpoint=?').bind(t.endpoint).run();}));
}
