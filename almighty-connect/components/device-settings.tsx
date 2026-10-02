'use client';
import {useEffect,useState} from 'react';
import type {Device} from '@/lib/contracts';
export default function DeviceSettings({role}:{role:Device['role']}){
 const [slot,setSlot]=useState(role==='store'?'A':'1');
 useEffect(()=>{try{const saved=localStorage.getItem('almighty-'+role+'-slot');if(saved)setSlot(saved);}catch{}},[role]);
 function save(){try{localStorage.setItem('almighty-'+role+'-slot',slot);}catch{}window.location.assign(role==='store'?'/':'/reception');}
 return <main className="shell"><section className="intro"><h1>{role==='store'?'呼び出し用端末の設定':'三宮の応答用端末の設定'}</h1><p>設置担当者が初回だけ設定します。複数台にはそれぞれ別の番号を設定してください。</p></section><section className="panel device-settings"><label>この端末の番号<select value={slot} onChange={e=>setSlot(e.target.value)}>{(role==='store'?['A','B']:['1','2','3','4','5']).map(value=><option value={value} key={value}>{role==='store'?'店舗の端末 '+(value==='A'?'1':'2'):value==='5'?'業務端末':'三宮 iPad '+value}</option>)}</select></label><button className="primary-link" onClick={save}>保存して受付に戻る</button></section></main>;
}
