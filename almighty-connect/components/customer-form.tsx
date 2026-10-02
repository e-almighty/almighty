'use client';
import {useState} from 'react';
import {CheckCircle2,LockKeyhole,Send} from 'lucide-react';
import type {Prompt} from '@/lib/contracts';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {RadioGroup,RadioGroupItem} from '@/components/ui/radio-group';
import {Checkbox} from '@/components/ui/checkbox';
function Choice({label,options,value,onChange}:{label:string;options:string[];value:string;onChange:(v:string)=>void}){return <fieldset className="choice-field"><legend>{label}</legend><RadioGroup value={value} onValueChange={onChange}>{options.map((v,i)=><label key={v} className={'choice '+(v===value?'selected':'')}><RadioGroupItem value={v}/><span>{v}</span></label>)}</RadioGroup></fieldset>}
export default function CustomerForm({prompt,busy,onSubmit}:{prompt:Prompt;busy:boolean;onSubmit:(a:Record<string,string>)=>Promise<boolean>}){
 const [v,setV]=useState<Record<string,string>>({});const set=(k:string,x:string)=>setV(a=>({...a,[k]:x}));
 if(prompt.answeredAt)return <section className="response-success"><CheckCircle2 size={42}/><h2>送信しました</h2><p>三宮のスタッフが内容を確認しています。<br/>そのままお待ちください。</p></section>;
 return <form className="customer-form" onSubmit={async e=>{e.preventDefault();await onSubmit(v)}}><p className="eyebrow">三宮スタッフからのお願い</p><h2>{prompt.title}</h2>{prompt.text&&<p className="prompt-copy">{prompt.text}</p>}{prompt.kind==='offer'&&<div className="offer-price">税込 <b>¥{(prompt.price??0).toLocaleString('ja-JP')}</b><small>内容確認用です。この操作で決済は行いません。</small></div>}
 {prompt.kind==='contact'&&<><label className="input-label">お名前（検証用の仮名）<Input required value={v.name??''} onChange={e=>set('name',e.target.value)} autoComplete="off" maxLength={80} placeholder="例：テスト 太郎"/></label><Choice label="ご相談内容" value={v.topic??''} options={['パソコンの初期設定','Microsoftアカウント','料金・サービスの相談','その他']} onChange={x=>set('topic',x)}/><label className="consent"><Checkbox checked={v.consent==='yes'} onCheckedChange={x=>set('consent',x===true?'yes':'')}/><span>入力内容を三宮の担当者に送信します。相談終了時にアプリから削除します。</span></label></>}
 {prompt.kind==='microsoft'&&<><div className="safety-note"><LockKeyhole size={18}/>パスワード・認証コードは入力しません。</div><Choice label="Microsoftアカウントをお持ちですか？" options={['持っている','持っていない','分からない']} value={v.account??''} onChange={x=>set('account',x)}/><Choice label="メールアドレスのご希望" options={['既存メールを使いたい','新しいメールを作りたい','相談して決めたい']} value={v.emailPlan??''} onChange={x=>set('emailPlan',x)}/><Choice label="アカウント作成に使う、ご自身の端末" options={['自分のスマートフォン','購入したパソコン','自分の端末は手元にない']} value={v.ownDevice??''} onChange={x=>set('ownDevice',x)}/></>}
 {prompt.kind==='offer'&&<Choice label="ご希望をお聞かせください" options={['内容を確認しました','もう一度説明してください','今回は見送ります']} value={v.decision??''} onChange={x=>set('decision',x)}/>}
 {prompt.kind==='guide'&&<Choice label="ご確認" options={['確認しました','手伝ってください']} value={v.decision??''} onChange={x=>set('decision',x)}/>}
 <Button className="large-button full" type="submit" disabled={busy}><Send size={18}/>{busy?'送信中…':'三宮スタッフに送信する'}</Button></form>
}
