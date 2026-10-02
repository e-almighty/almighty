'use client';
import '@/lib/compat';
import {useEffect,useState} from 'react';
import Desk from './desk';
import DeskBoundary from './desk-boundary';
import type {Device} from '@/lib/contracts';
// The caller and receiver have independent entry points and device preferences.
export default function ReceptionEntry({role='store'}:{role?:Device['role']}){
 const [device,setDevice]=useState<Device|null>(null);
 useEffect(()=>{let slot=role==='store'?'A':'1';try{const saved=localStorage.getItem('almighty-'+role+'-slot');const previous=JSON.parse(localStorage.getItem('almighty-device')??'null');const value=saved??(previous?.role===role?previous.slot:null);if((role==='store'?['A','B']:['1','2','3','4','5']).includes(value))slot=value;}catch{}setDevice({role,slot});},[role]);
 if(!device)return <main className="shell"><p>受付を準備しています</p></main>;
 return <DeskBoundary><Desk device={device}/></DeskBoundary>;
}
