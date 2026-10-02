'use client';
import {useEffect,useRef,useState} from 'react';
import type {DailyCall} from '@daily-co/daily-js';
import {Video,VideoOff,Headphones} from 'lucide-react';
import {Button} from '@/components/ui/button';
export default function VideoCall({configured,connect}:{configured:boolean;connect:()=>Promise<{url:string;token:string}>}){
 const mount=useRef<HTMLDivElement>(null),call=useRef<DailyCall|null>(null),alive=useRef(true);const [status,setStatus]=useState('ready'),[error,setError]=useState('');
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;void call.current?.destroy();call.current=null;}},[]);
 // Begin after the staff's answer makes the consultation active on both devices.
 // A cancellable timer also avoids duplicate joins during development StrictMode.
 const connection=useRef(connect);connection.current=connect;
 const joining=useRef(false);
 useEffect(()=>{if(!configured)return;const timer=setTimeout(()=>{void join();},0);return()=>clearTimeout(timer);},[configured]);
 async function join(){if(joining.current)return;joining.current=true;setStatus('connecting');setError('');try{await call.current?.destroy();call.current=null;const Daily=(await import('@daily-co/daily-js')).default;if(!Daily.supportedBrowser().supported)throw new Error('このブラウザでは通話に対応していません。iPadのSafariを更新してお試しください。');const credentials=await connection.current();if(!alive.current||!mount.current)return;const frame=Daily.createFrame(mount.current,{showLeaveButton:true,iframeStyle:{width:'100%',height:'100%',border:'0',borderRadius:'16px'}});call.current=frame;
 frame.on('joined-meeting',()=>{if(alive.current)setStatus('joined')});frame.on('left-meeting',()=>{if(alive.current)setStatus('ready')});frame.on('error',()=>{if(alive.current){setError('通話に接続できません。カメラ・マイクの許可と回線を確認し、再接続してください。');setStatus('ready');}});await frame.join(credentials);
 }catch(e){if(alive.current){setError(e instanceof Error?e.message:'接続できませんでした');setStatus('ready');}}finally{joining.current=false;}}
 return <section className="video-panel"><div className="video-label"><span><Video size={18}/> ビデオ通話</span><span>{!configured?'未設定':status==='joined'?'通話室に参加中':status==='connecting'?'接続しています':'接続待ち'}</span></div><div ref={mount} className={'video-mount '+(status==='ready'?'inactive':'')}/>{status==='ready'&&<div className="video-empty">{configured?<Video size={38}/>:<VideoOff size={38}/>}<h3>{configured?'顔を見ながらお話ししましょう':'通話サービスを設定すると映像が表示されます'}</h3><p>{configured?'カメラとマイクの使用を許可してください。':'現在は操作検証用です。入力・案内のやりとりをお試しいただけます。'}</p>{configured&&<Button onClick={join} className="large-button"><Headphones/>通話に再接続</Button>}</div>}{error&&<p className="video-error" role="alert">{error}</p>}<div className="video-foot">入力画面を開いたまま通話できます。録画・録音は行いません。</div></section>
}

