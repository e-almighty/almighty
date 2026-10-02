import { z } from 'zod';
export const deviceSchema = z.object({role:z.enum(['store','staff']),slot:z.string()}).refine(d=>d.role==='store'?['A','B'].includes(d.slot):['1','2','3','4','5'].includes(d.slot),'端末が不正です');
export type Device = z.infer<typeof deviceSchema>;
export type Prompt = {id:string;kind:'contact'|'microsoft'|'offer'|'guide';title:string;text:string;price?:number;answer?:Record<string,string>;answeredAt?:number};
export type Session = {id:string;store:string;staff:string|null;status:'waiting'|'active'|'ended';created:number;expires:number;version:number;prompt:Prompt|null;messages:{id:string;role:string;text:string;at:number}[];outcome?:string};
export type DeskState = {account?:string;sessions:Session[];staff:{slot:string;ready:number;seen:number}[];videoConfigured:boolean;now:number;available:number;queuePosition:number};
export const actionSchema=z.discriminatedUnion('action',[
 z.object({action:z.literal('call'),requestId:z.string().uuid()}),
 z.object({action:z.literal('heartbeat'),ready:z.boolean(),clientId:z.string().uuid().optional()}),
 z.object({action:z.literal('claim'),id:z.string().uuid()}),
 z.object({action:z.literal('sendPrompt'),id:z.string().uuid(),kind:z.enum(['contact','microsoft','offer','guide']),text:z.string().trim().max(1200).default(''),price:z.number().int().min(0).max(10000000).optional()}),
 z.object({action:z.literal('answer'),id:z.string().uuid(),promptId:z.string().uuid(),answer:z.record(z.string().max(500))}),
 z.object({action:z.literal('message'),id:z.string().uuid(),text:z.string().trim().min(1).max(500)}),
 z.object({action:z.literal('end'),id:z.string().uuid(),outcome:z.enum(['completed','followup','cancelled'])}),
 z.object({action:z.literal('video'),id:z.string().uuid()}),
]);
export function validateAnswer(prompt:Prompt, raw:Record<string,string>){
 const shapes={
 contact:z.object({name:z.string().trim().min(1).max(80),topic:z.enum(['パソコンの初期設定','Microsoftアカウント','料金・サービスの相談','その他']),consent:z.literal('yes')}).strict(),
 microsoft:z.object({account:z.enum(['持っている','持っていない','分からない']),emailPlan:z.enum(['既存メールを使いたい','新しいメールを作りたい','相談して決めたい']),ownDevice:z.enum(['自分のスマートフォン','購入したパソコン','自分の端末は手元にない'])}).strict(),
 offer:z.object({decision:z.enum(['内容を確認しました','もう一度説明してください','今回は見送ります'])}).strict(),
 guide:z.object({decision:z.enum(['確認しました','手伝ってください'])}).strict()
 };return shapes[prompt.kind].parse(raw);
}

