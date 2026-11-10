// Verify and capture the standalone replays in a running headless Chrome (CDP).
// Start Chrome with --headless=new --remote-debugging-port=9228, then run this file.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {fileURLToPath, pathToFileURL} from 'node:url';
const out=fileURLToPath(new URL('../../dist/replays/zoo-v7/',import.meta.url));
const pages=await (await fetch('http://127.0.0.1:9228/json/list')).json();
const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
let id=0;const pending=new Map(),errors=[],requests=[];
ws.onmessage=({data})=>{const message=JSON.parse(data);if(message.id){const p=pending.get(message.id);pending.delete(message.id);message.error?p.reject(message.error):p.resolve(message.result)}else if(message.method==='Runtime.exceptionThrown'){errors.push(message.params.exceptionDetails)}else if(message.method==='Network.requestWillBeSent'){requests.push(message.params.request.url)}};
function send(method,params={}){return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))})}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function navigate(slug){await send('Page.navigate',{url:pathToFileURL(out+slug+'.html').href});for(let i=0;i<50;i++){await pause(50);if(await evaluate(`Boolean(window.REPLAY && window.REPLAY.data.slug==='${slug}')`))return}throw Error('Replay did not load')}
async function screenshot(filename){const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile(out+filename,Buffer.from(data,'base64'))}
const checks=[];
try{
 for(const slug of ['victory','defeat']){
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:1,mobile:false});
  await navigate(slug);
  assert.equal(await evaluate('REPLAY.index'),0);
  assert.equal(await evaluate(`REPLAY.data.frames.every(f=>!('hand' in f.state.opponent))`),true);
  await evaluate(`document.getElementById('next').click()`);assert.equal(await evaluate('REPLAY.index'),1);
  await evaluate(`document.getElementById('prev').click()`);assert.equal(await evaluate('REPLAY.index'),0);
  await evaluate(`document.querySelectorAll('.chapter')[2].click()`);
  const chapter=await evaluate('REPLAY.index');assert.ok(chapter>0);
  await evaluate(`document.getElementById('before').click()`);assert.equal(await evaluate(`document.getElementById('viewBadge').textContent`),'行动前');
  assert.equal(await evaluate(`document.querySelector('#ownHero .hp-number').textContent`),await evaluate(`Math.max(0,REPLAY.data.frames[REPLAY.index-1].state.you.hero.health)+' / 30'`));
  await evaluate(`document.getElementById('after').click();document.getElementById('seek').value=12;document.getElementById('seek').dispatchEvent(new Event('input'))`);assert.equal(await evaluate('REPLAY.index'),12);
  await evaluate(`document.getElementById('reset').click();document.getElementById('speed').value='300';document.getElementById('play').click()`);await pause(720);await evaluate('REPLAY.pause()');assert.ok(await evaluate('REPLAY.index>=2'));
  await evaluate(`document.activeElement.blur();document.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',code:'ArrowRight'}))`);assert.ok(await evaluate('REPLAY.index>=3'));
  await evaluate(`document.getElementById('end').click()`);
  assert.equal(await evaluate('document.body.dataset.terminal'),'true');
  assert.equal(await evaluate('REPLAY.data.won'),slug==='victory');
  assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
  assert.equal(await evaluate(`document.querySelectorAll('.log-item.selected').length`),1);
  const logVisible=await evaluate(`(()=>{const a=document.querySelector('.log-item.selected').getBoundingClientRect(),p=document.getElementById('log').getBoundingClientRect();return a.top>=p.top&&a.bottom<=p.bottom})()`);
  assert.equal(logVisible,true,'Current action must be visible in the log');
  await evaluate(`document.getElementById('speed').value='1200'`);
  await screenshot(slug+'-preview.png');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await evaluate('REPLAY.go(REPLAY.data.chapters[2].frame)');await pause(100);
  assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true,'Mobile page must not overflow');
  await screenshot(slug+'-mobile.png');
  checks.push({slug,playback:true,seek:true,chapters:true,before_after:true,keyboard:true,result:true,desktop_layout:true,mobile_layout:true,hidden_hand_protected:true});
 }
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:pathToFileURL(out+'index.html').href});
 for(let i=0;i<50;i++){await pause(50);if(await evaluate(`document.querySelectorAll('img').length===2 && [...document.images].every(i=>i.complete&&i.naturalWidth>0)`))break}
 assert.equal(await evaluate(`document.title==='动物园 · 两场真实对战回放' && [...document.images].every(i=>i.naturalWidth>0)`),true);
 assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
 await screenshot('index-preview.png');
 assert.deepEqual(errors,[],'No JavaScript errors');
 assert.equal(requests.some(u=>/^https?:/.test(u)),false,'Standalone replay must work without network');
 await fs.writeFile(out+'browser-verification.json',JSON.stringify({browser:'Chrome headless',checks,javascript_errors:errors,network_required:false},null,2)+'\n');
 console.log(JSON.stringify(checks,null,2));
}finally{ws.close()}
