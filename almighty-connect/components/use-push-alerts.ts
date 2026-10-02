'use client';
import {useCallback,useEffect,useState} from 'react';
// Lock-screen alerts for a sleeping reception iPad. On iPadOS this only works when the page was
// opened from a Home Screen icon (iPadOS 16.4+), so the hook reports what the user has to do.
export type PushStatus='checking'|'unsupported'|'home-screen'|'off'|'on'|'denied';
type Send=(a:{action:string;[key:string]:unknown})=>Promise<unknown>;

function fromB64u(s:string):Uint8Array{s=s.replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';const bin=atob(s);const out=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out;}
function isStandalone(){try{return window.matchMedia('(display-mode: standalone)').matches||(navigator as Navigator&{standalone?:boolean}).standalone===true;}catch{return false;}}
function isApple(){return /iPad|iPhone|Macintosh/.test(navigator.userAgent)&&'ontouchend' in document;}

export function usePushAlerts(enabled:boolean,publicKey:string|undefined,send:Send){
 const [status,setStatus]=useState<PushStatus>(()=>{
  if(typeof window==='undefined'||!enabled)return 'checking';
  const supported='serviceWorker' in navigator&&'PushManager' in window&&'Notification' in window;
  return supported?'checking':isApple()&&!isStandalone()?'home-screen':'unsupported';
 });
 useEffect(()=>{
  if(!enabled||!('serviceWorker' in navigator)||!('PushManager' in window)||!('Notification' in window))return;
  let cancelled=false;
  navigator.serviceWorker.register('/sw.js').then(async reg=>{
   const sub=await reg.pushManager.getSubscription();
   if(cancelled)return;
   if(Notification.permission==='denied')setStatus('denied');
   else if(sub&&Notification.permission==='granted'){setStatus('on');void send({action:'subscribe',subscription:sub.toJSON()}).catch(()=>{});}
   else setStatus('off');
  }).catch(()=>{if(!cancelled)setStatus('unsupported');});
  return()=>{cancelled=true;};
 },[enabled,send]);
 const enable=useCallback(async()=>{
  if(!publicKey)throw new Error('通知の準備ができていません。少し待ってからもう一度押してください。');
  const permission=await Notification.requestPermission();
  if(permission!=='granted'){setStatus('denied');throw new Error('通知が許可されませんでした。');}
  const reg=await navigator.serviceWorker.ready;
  const sub=(await reg.pushManager.getSubscription())??await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:fromB64u(publicKey) as BufferSource});
  await send({action:'subscribe',subscription:sub.toJSON()});
  setStatus('on');
 },[publicKey,send]);
 const disable=useCallback(async()=>{
  const reg=await navigator.serviceWorker.ready;const sub=await reg.pushManager.getSubscription();
  if(sub){await send({action:'unsubscribe',endpoint:sub.endpoint}).catch(()=>{});await sub.unsubscribe();}
  setStatus('off');
 },[send]);
 return {status,enable,disable};
}
