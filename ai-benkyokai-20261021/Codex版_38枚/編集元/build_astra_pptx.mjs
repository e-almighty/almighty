import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const root = 'C:/Users/user/Documents/Codex/2026-10-19/ai-ai';
const skill = 'C:/Users/user/.codex/plugins/cache/openai-primary-runtime/presentations/26.915.20218/skills/presentations';
const pythonExecutable = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
process.env.RUNTIME_NODE = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';
process.env.RUNTIME_BIN_DIR = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override';
process.env.RUNTIME_PYTHON = pythonExecutable;
const source = JSON.parse(await fs.readFile(path.join(root,'work/slide_employee_script.json'),'utf8'));
const coverImage = await fs.readFile(path.join(root,'outputs/2026-10-21_Astra勉強会_表紙素材.png'));
const visualFiles={12:'research_photo.png',13:'document_illustration.png',15:'data_photo.png',16:'website_illustration.png',17:'ai_photo.png',21:'sales_photo.png'};
const visualImages=Object.fromEntries(await Promise.all(Object.entries(visualFiles).map(async ([n,file])=>[n,await fs.readFile(path.join(root,'work/assets',file))])));
const slides = source.slides;
if (slides.length !== 38) throw new Error('Expected 38 slides');
const { finalizePresentation } = await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const presentation = Presentation.create({slideSize:{width:1280,height:720}});
const font = 'Yu Gothic';
const C = {ink:'#0D2A43',blue:'#2A77A3',muted:'#365C76',ice:'#EDF7FC',ice2:'#E1F2F9',white:'#F8FBFD'};
const bg = i => [C.ice,C.white,C.ice2][i%3];
const assigned={2:'steps',3:'statement',4:'metric',5:'comparison',6:'diagram',7:'split',8:'diagram',9:'metric',10:'statement',11:'diagram',12:'photo',13:'illustration',14:'diagram',15:'photo',16:'illustration',17:'photo',18:'steps',19:'steps',20:'diagram',21:'photo',22:'diagram',23:'split',24:'diagram',25:'comparison',26:'list',27:'comparison',28:'split',29:'diagram',30:'metric',31:'diagram',32:'list',33:'split',34:'comparison',35:'comparison',36:'comparison',37:'diagram',38:'statement'};
function addText(slide,value,left,top,width,height,fontSize,bold=false,color=C.ink){
  const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=String(value??'');
  shape.text.style={typeface:font,fontSize,bold,color,autoFit:'shrinkText'};
  return shape;
}
function addCard(slide,label,left,top,width,height,index=0,accent=false,sub=''){
  slide.shapes.add({geometry:'rect',position:{left,top,width,height},fill:accent?'#D7EEF8':'#FFFFFF',line:{fill:accent?C.blue:'#AED8E9',width:2}});
  if(index) addText(slide,String(index).padStart(2,'0'),left+19,top+16,55,27,17,true,C.blue);
  addText(slide,label,left+21,top+(sub?58:45),width-42,sub?55:75,width<210?25:31,true,C.ink);
  if(sub) addText(slide,sub,left+21,top+118,width-42,58,22,true,C.muted);
}
function addDiagram(slide,s){
  const n=s.number;
  const data={6:['モデル','実行基盤','ツール','資料・ルール','権限・承認'],8:['Astra|難題の設計','Sol|日々の実務','Luna|定型の大量処理'],11:['Web・ファイル検索','コード実行・修正','画像生成・PC操作','外部連携（MCP）'],14:['根拠を集める','1枚1メッセージ','全ページを確認'],20:['調査担当','検証担当','親が統合'],22:['今できる','設定すればできる','人が判断する'],24:['目的','背景','成果物','制約','道具・権限','検証','完了条件'],29:['作る','実物を見る','直して再確認'],31:['Astra|難題を設計','Sol|実務を回す','Luna|大量処理'],37:['成功率','所要時間','成功1件の費用']}[n]??s.bullets??[];
  if(n===6){data.forEach((x,j)=>{const left=76+j*32,top=354+j*57,width=1020-j*34;slide.shapes.add({geometry:'rect',position:{left,top,width,height:49},fill:j===4?'#D7EEF8':'#FFFFFF',line:{fill:j===4?C.blue:'#AED8E9',width:2}});addText(slide,String(j+1).padStart(2,'0'),left+22,top+9,45,30,17,true,C.blue);addText(slide,x,left+95,top+5,width-120,39,27,true,C.ink);});return;}
  if(n===11){
    const xy=[[76,378],[706,378],[76,532],[706,532]];
    data.forEach((x,j)=>addCard(slide,x,xy[j][0],xy[j][1],500,116,j+1));
    addCard(slide,'ASTRA',554,462,170,90,0,true);return;
  }
  if(n===20){
    addCard(slide,data[0],76,390,490,105,1);
    addCard(slide,data[1],714,390,490,105,2);
    addText(slide,'↘',500,500,90,50,36,true,C.blue);addText(slide,'↙',690,500,90,50,36,true,C.blue);
    addCard(slide,data[2],396,557,490,97,3,true);return;
  }
  if(n===24){data.forEach((x,j)=>{const second=j>=4;const col=second?j-4:j;const left=second?220+col*295:76+col*282;addCard(slide,x,left,second?530:384,second?260:250,113,j+1,j===6);});return;}
  const w=326,g=65;
  data.forEach((x,j)=>{const [main,sub]=String(x).split('|');addCard(slide,main,76+j*(w+g),407,w,197,j+1,j===data.length-1,sub??'');if(j<data.length-1)addText(slide,'→',76+j*(w+g)+w+10,474,55,60,43,true,C.blue);});
}
function parseMetric(v){
  const text=String(v??'');
  const parts=text.split(/[｜|：:]/);
  return parts.length>1?[parts[0].trim(),parts.slice(1).join(' ').trim()]:[text,''];
}
function comparison(s){
  const b=s.bullets??[];
  if(s.number===5) return ['質問への回答','道具を使う仕事','人が次の作業を考える','調査・制作・確認まで進める',''];
  if(s.number===25) return ['△ あいまい','○ 判断に使える','競合を調べて','価格帯・差別化案・上位候補を表にする',''];
  if(s.number===27) return ['自動で進める','人が確認する','閲覧・分析・下書き','送信・公開・支払い・削除',''];
  if(s.number===34) return ['GPT-6 Astra','Claude Fable 5.1','105万トークン / 最大出力12.8万','100万トークン / 最大出力12.8万','API基本単価：両者とも入力 $10 / 出力 $50（100万トークン当たり）'];
  if(s.number===35) return ['Astra','Fable 5.1','Codex・OpenAIのツール群で、曖昧な仕事から成果物へ','Claude Code・Coworkで長期の難題へ','両者の用途は重なる。自社の仕事で評価する。'];
  if(s.number===36) return ['Astra','Fable 5.1','入力27.2万トークン超で料金倍率','100万トークン全域が標準単価','キャッシュ読込：Astra $1 / Fable $0.25（100万トークン当たり）'];
  return [b[0]??'',b[1]??'',b[2]??'',b[3]??'',''];
}
for(let i=0;i<slides.length;i++){
  const s=slides[i];
  const slide=presentation.slides.add();
  slide.background.fill=bg(i);
  const mode=i===0?'cover':assigned[s.number]??'list';
  if(mode==='cover'){
    slide.images.add({blob:new Uint8Array(coverImage),contentType:'image/png',alt:'淡い水色のAI業務フローの抽象イラスト',fit:'cover',position:{left:0,top:0,width:1280,height:720}});
    addText(slide,'営業協会 AI勉強会 / 2026.10.21',76,72,1100,32,23,true,C.blue);
    addText(slide,'GPT-6 ASTRA',76,185,1130,125,98,true,C.ink);
    addText(slide,'仕事の成果につなげる使い方',76,332,1120,88,52,true,C.ink);
    addText(slide,'活用法・実務例・Claude Fable 5.1との比較',76,600,1050,48,26,true,C.muted);
  }else{
    addText(slide,s.chapter,76,52,1050,35,19,true,C.blue);
    addText(slide,s.title,76,143,1120,83,52,true,C.ink);
    if(mode==='photo'){
      slide.images.add({blob:new Uint8Array(visualImages[s.number]),contentType:'image/png',alt:s.title+'の業務写真',fit:'cover',position:{left:655,top:273,width:545,height:365}});
      addText(slide,s.message,76,283,525,170,44,true,C.ink);
      (s.bullets??[]).slice(0,3).forEach((x,j)=>{addText(slide,String(j+1).padStart(2,'0'),76,482+j*55,38,35,19,true,C.blue);addText(slide,x,126,480+j*55,475,48,27,true,C.muted);});
    }else if(mode==='illustration'){
      slide.images.add({blob:new Uint8Array(visualImages[s.number]),contentType:'image/png',alt:s.title+'の説明イラスト',fit:'contain',position:{left:600,top:291,width:600,height:365}});
      addText(slide,s.message,76,281,500,135,42,true,C.ink);
      (s.bullets??[]).slice(0,3).forEach((x,j)=>{addText(slide,String(j+1).padStart(2,'0'),76,460+j*59,38,35,19,true,C.blue);addText(slide,x,126,457+j*59,425,50,28,true,C.muted);});
    }else if(mode==='diagram'){
      addText(slide,s.message,76,272,1120,89,38,true,C.ink);
      addDiagram(slide,s);
    }else if(mode==='statement'){
      addText(slide,s.message,76,307,1120,190,57,true,C.blue);
      if(s.bullets?.length) addText(slide,s.bullets.slice(0,3).join('　 / 　'),76,575,1080,55,23,true,C.muted);
    }else if(mode==='comparison'){
      addText(slide,s.message,76,270,1120,96,39,true,C.ink);
      const [lt,rt,lb,rb,foot]=comparison(s);
      addText(slide,lt,76,420,520,53,36,true,C.blue);
      addText(slide,rt,664,420,540,53,36,true,C.blue);
      addText(slide,lb,76,500,510,112,28,true,C.muted);
      addText(slide,rb,664,500,530,112,28,true,C.muted);
      if(foot) addText(slide,foot,76,634,1100,46,22,true,C.muted);
    }else if(mode==='split'){
      addText(slide,s.message,76,305,590,240,46,true,C.ink);
      (s.bullets??[]).slice(0,3).forEach((x,j)=>addText(slide,x,735,317+j*86,455,70,29,true,C.muted));
    }else if(mode==='metric'){
      addText(slide,s.message,76,265,1120,106,40,true,C.ink);
      (s.bullets??[]).slice(0,3).forEach((x,j)=>{
        const [a,b]=parseMetric(x);
        addText(slide,a,76+j*395,450,375,84,38,true,C.blue);
        if(b) addText(slide,b,76+j*395,548,365,60,23,true,C.muted);
      });
    }else{
      addText(slide,s.message,76,270,1120,109,39,true,C.ink);
      const b=(s.bullets??[]).slice(0,4);
      if(mode==='steps'){
        const col=Math.floor(1120/b.length);
        b.forEach((x,j)=>{
          addText(slide,String(j+1).padStart(2,'0'),76+j*col,450,col-18,42,24,true,C.blue);
          addText(slide,x,76+j*col,504,col-22,130,30,true,C.ink);
        });
      }else{
        b.forEach((x,j)=>{
          const col=j%2,row=Math.floor(j/2);
          addText(slide,String(j+1).padStart(2,'0'),76+col*575,450+row*110,42,34,22,true,C.blue);
          addText(slide,x,126+col*575,447+row*110,490,92,30,true,C.ink);
        });
      }
    }
  }
  addText(slide,String(s.number).padStart(2,'0')+' / 38',1130,666,100,28,17,true,C.blue);
  const notes=String(s.notes??'')+'\n\n'+(s.sourceUrls??[]).map(u=>'出典: '+u).join('\n');
  slide.speakerNotes.textFrame.setText(notes);
}
const build=path.join(root,'work/.codex-finalizer');
await fs.mkdir(build,{recursive:true});
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const finalPath=path.join(root,'outputs/2026-10-21_Astra勉強会_38枚_編集用_v4.pptx');
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:candidate,finalPath,
  pythonExecutable,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
  requiredNativeTableOwnerSlides:[],
  explicitTotalSlideCount:38,
  fontPolicy:{basis:'design',families:[font]},
  verifyArtifactToolImport:true,
  receiptPath:path.join(build,'astra-38-v4.validation.json'),
});
console.log(JSON.stringify({finalPath,result},null,2));
