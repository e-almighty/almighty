'use client';
import {Video} from 'lucide-react';
import {meetLink} from '@/lib/meet-config';

export default function MeetCall({store,waiting=false}:{store:string;waiting?:boolean}) {
 const url=meetLink(store);
 return <section className="panel" style={{padding:'24px'}}>
  <h2><Video size={24}/> Google Meetで通話</h2>
  <p>{waiting?'三宮を呼び出しています。Meetで「参加」を押してスタッフをお待ちください。':'受付の担当者が決まりました。映像・音声はMeetで「参加」を押すとつながります。'}</p>
  {url?<a className="large-button" style={{display:'inline-flex',alignItems:'center',justifyContent:'center',background:'#1967d2',color:'white',padding:'16px 24px',borderRadius:'12px',textDecoration:'none'}} href={url} target="_blank" rel="noopener noreferrer">Google Meetを開く</a>:<p role="alert">この店舗の会議リンクは未設定です。端末設定をご確認ください。</p>}
  <p className="small-note">すでにMeetが開いている場合は、その画面へ戻ってください。入室許可が必要な場合は、三宮の主催者が許可します。</p>
  <p className="small-note">入力・料金確認はこの受付画面で行います。通話が終わったら双方でMeetから退出し、この画面の「相談を終了」を押してください。</p>
 </section>;
}
