// Render every recorded decision for the native macOS MP4 encoder.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const out=fileURLToPath(new URL('../../dist/replays/zoo-v7/',import.meta.url));
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'hearthstone-video-frames-'));
const pages=await (await fetch('http://127.0.0.1:9229/json/list')).json();
const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
let id=0;const pending=new Map();
ws.onmessage=({data})=>{const m=JSON.parse(data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result)}};
function send(method,params={}){return new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
await send('Page.enable');await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1200,deviceScaleFactor:1,mobile:false});
const manifests=[];
try{
 for(const slug of ['victory','defeat']){
  await send('Page.navigate',{url:pathToFileURL(out+slug+'.html').href});
  for(let i=0;i<60;i++){await new Promise(r=>setTimeout(r,50));if(await evaluate(`Boolean(window.REPLAY&&REPLAY.data.slug==='${slug}')`))break}
  const match=await evaluate('REPLAY.data');
  if(match.slug!==slug)throw Error('Wrong replay');
  await evaluate(`document.fonts.ready.then(()=>{const s=document.createElement('style');s.textContent='*{transition:none!important;animation:none!important}';document.head.append(s)})`);
  const manifest={slug,game_id:match.game_id,width:1440,height:1200,fps:2,output:out+slug+'.mp4',actions:match.frames.length-1,frames:[]};
  for(const f of match.frames){
   await evaluate(`REPLAY.go(${f.index});document.getElementById('play').textContent='▶ 视频回放';new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))`);
   const current=await evaluate('Number(document.body.dataset.frame)');
   if(current!==f.index)throw Error('Replay frame mismatch');
   const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
   const filename=path.join(temp,`${slug}-${String(f.index).padStart(3,'0')}.png`);
   await fs.writeFile(filename,Buffer.from(data,'base64'));
   const ticks=f.index===match.frames.length-1?10:f.index===0?6:f.note?6:f.kind==='end_turn'?2:4;
   manifest.frames.push({path:filename,ticks});
  }
  manifest.duration_seconds=manifest.frames.reduce((n,f)=>n+f.ticks,0)/manifest.fps;
  const filename=path.join(temp,slug+'.json');
  await fs.writeFile(filename,JSON.stringify(manifest,null,2));manifests.push(filename);
  console.log(`${slug}: ${match.frames.length} states, ${manifest.duration_seconds}s`);
 }
 await fs.writeFile(out+'video-manifests.json',JSON.stringify({manifests},null,2)+'\n');
 console.log(JSON.stringify({manifests},null,2));
}finally{ws.close()}
