'use client';
import {Component,type ReactNode} from 'react';
// A rendering or effect error must never leave the iPad with a blank page.
export default class DeskBoundary extends Component<{children:ReactNode},{message:string|null}>{
 state={message:null as string|null};
 static getDerivedStateFromError(e:unknown){return {message:e instanceof Error?e.message:String(e)};}
 render(){
  if(this.state.message===null)return this.props.children;
  return <main className="desk"><div className="center-stage" role="alert"><h2>画面を表示できませんでした</h2><p style={{margin:'16px 0'}}>この端末のブラウザで問題が起きました。下のボタンで再読み込みしてください。直らない場合は、次の文を三宮にお伝えください。</p><p style={{fontSize:'13px',wordBreak:'break-all'}}>エラー: {this.state.message}</p><p style={{fontSize:'13px',wordBreak:'break-all'}}>ブラウザ: {typeof navigator!=='undefined'?navigator.userAgent:''}</p><button className="primary-link" style={{display:'inline-flex',margin:'20px auto 0'}} onClick={()=>window.location.reload()}>再読み込み</button></div></main>;
 }
}
