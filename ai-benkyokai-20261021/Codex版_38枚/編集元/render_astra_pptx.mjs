import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const root='C:/Users/user/Documents/Codex/2026-10-19/ai-ai';
const source=path.join(root,'outputs/2026-10-21_Astra勉強会_38枚_編集用_v4.pptx');
const out=path.join(root,'work/pptx_screenshots');
await fs.mkdir(out,{recursive:true});
const presentation=await PresentationFile.importPptx(await FileBlob.load(source));
const slides=presentation.slides.items;
for(let i=0;i<slides.length;i++){
  const blob=await presentation.export({slide:slides[i],format:'png',scale:1});
  await fs.writeFile(path.join(out,'slide_'+String(i+1).padStart(3,'0')+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({slides:slides.length,out}));
