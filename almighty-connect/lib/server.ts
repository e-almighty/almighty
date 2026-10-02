import { env } from 'cloudflare:workers';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import type { Device, Session } from './contracts';
export class ApiError extends Error {constructor(public status:number,message:string){super(message)}}
export function db(){if(!env.DB)throw new ApiError(503,'受付データに接続できません。少し待って再試行してください。');return env.DB;}
export async function identity(){return (await account()).userId;}
export async function account(){const u=await getChatGPTUser();if(!u)throw new ApiError(401,'検証用アカウントでログインしてください。');return u;}
export function originCheck(req:Request){const origin=req.headers.get('origin');if(!origin||origin!==new URL(req.url).origin)throw new ApiError(403,'この画面から操作をやり直してください。');}
export function roleCheck(d:Device,role:string){if(d.role!==role)throw new ApiError(403,'この端末では実行できない操作です。');}
export async function clean(tenant:string){const now=Date.now();await db().batch([db().prepare('DELETE FROM consultations WHERE tenant = ? AND expires <= ?').bind(tenant,now),db().prepare('DELETE FROM receiver_connections WHERE tenant=? AND seen<?').bind(tenant,now-86400000)]);}
export async function session(tenant:string,id:string){const row=await db().prepare('SELECT * FROM consultations WHERE tenant=? AND id=?').bind(tenant,id).first<any>();if(!row||row.expires<=Date.now())throw new ApiError(404,'この相談は終了したか、期限が切れています。');return decode(row);}
export function decode(row:any):Session{return {id:row.id,store:row.store,staff:row.staff,status:row.status,created:row.created,expires:row.expires,version:row.version,...JSON.parse(row.payload)};}
export function participant(s:Session,d:Device){if(d.role==='store'?s.store!==d.slot:s.staff!==d.slot)throw new ApiError(403,'この相談の担当端末ではありません。');}
export async function save(tenant:string,s:Session){const payload=JSON.stringify({prompt:s.prompt,messages:s.messages,outcome:s.outcome,pushes:s.pushes,lastPush:s.lastPush});const r=await db().prepare('UPDATE consultations SET payload=?, version=version+1, status=? WHERE tenant=? AND id=? AND version=?').bind(payload,s.status,tenant,s.id,s.version).run();if(!r.meta.changes)throw new ApiError(409,'相手側で情報が更新されました。画面を確認してもう一度操作してください。');}
export function reply(data:unknown,status=200){return Response.json(data,{status,headers:{'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'}});}
export function fail(e:unknown){if(e instanceof ApiError)return reply({error:e.message},e.status);if(e&&typeof e==='object'&&'issues'in e)return reply({error:'入力内容を確認してください。空欄や選択されていない項目があります。'},400);console.error('desk-operation-failed',e instanceof Error?e.name:'unknown');return reply({error:'処理を完了できませんでした。入力を残したまま再試行できます。'},503);}
