import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'オールマイティ Connect｜遠隔サポート',description:'店舗iPadと三宮のスタッフをつなぐ遠隔接客窓口',icons:{icon:'/favicon.svg'},robots:{index:false,follow:false}};
// Runs before any module script so older iPads (iPadOS 13-15.3) can execute the router and the desk.
// Keep in sync with lib/compat.ts, which repeats these for modules that load without the layout.
const COMPAT=`(function(){try{var c=window.crypto;if(c&&typeof c.randomUUID!=='function'){c.randomUUID=function(){var b=new Uint8Array(16);if(c.getRandomValues)c.getRandomValues(b);else for(var i=0;i<16;i++)b[i]=Math.floor(Math.random()*256);b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;var h='';for(var j=0;j<16;j++)h+=('0'+b[j].toString(16)).slice(-2);return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20)}}}catch(e){}
if(typeof Object.hasOwn!=='function')Object.hasOwn=function(o,k){return Object.prototype.hasOwnProperty.call(o,k)};
if(typeof Array.prototype.at!=='function')Array.prototype.at=function(n){n=Math.trunc(n)||0;if(n<0)n+=this.length;return n<0||n>=this.length?undefined:this[n]};
if(typeof String.prototype.replaceAll!=='function')String.prototype.replaceAll=function(s,r){return typeof s==='string'?this.split(s).join(typeof r==='function'?r(s):r):this.replace(s,r)};
if(typeof Promise.allSettled!=='function')Promise.allSettled=function(l){return Promise.all(Array.from(l,function(p){return Promise.resolve(p).then(function(v){return{status:'fulfilled',value:v}},function(r){return{status:'rejected',reason:r}})}))};
if(typeof globalThis==='undefined')window.globalThis=window;})();`;
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="ja"><head><script dangerouslySetInnerHTML={{__html:COMPAT}}/></head><body>{children}</body></html>}
