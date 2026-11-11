"""Measure warm file-to-action calls and a stale observation during a hung worker."""
import json,shutil,sys,tempfile,time,subprocess
from pathlib import Path
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
from development.secret_hunter_next.accounting import reserve,finish
C=ROOT/'development/secret_hunter_next/release/secret-hunter-program'
def main():
 reserve('pipeline-checks',short=200)
 sys.path.insert(0,str(C/'scripts'))
 from program_policy import decide
 from state_features import with_public_history
 from action_validator import legal
 cfg=json.loads((C/'config.json').read_text());src=ROOT/'experiments/secret-hunter-next-m1-screen';zs=[]
 for r in sorted(readlines(src/'results.jsonl'),key=lambda x:(x['opponent'],x['seed'],x['seat']))[:18]:
  history=[]
  for z in readlines(src/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl'):
   history+=z['state'].get('events',[])
   if z['state']['phase']=='main':zs.append((z['state'],history[:]))
 zs.sort(key=lambda z:len(z[0]['you']['hand'])+len(z[0]['you']['board'])*len(z[0]['opponent']['board']))
 selected=zs[::max(1,len(zs)//50)][:50]+zs[-50:];times=[];nodes=[];errors=[]
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);statepath=root/'state.json';histpath=root/'history.jsonl'
  for s,hist in selected:
   raw={k:v for k,v in s.items() if k not in ('public_opponent_evidence','hero_attack_available')};statepath.write_text(json.dumps(raw));histpath.write_text('\n'.join(json.dumps(e) for e in hist))
   start=time.monotonic();state=json.loads(statepath.read_text());history=[json.loads(x) for x in histpath.read_text().splitlines()];state=with_public_history(state,history)
   a,info=decide(state,cfg|{'_deadline':start+1.5});elapsed=time.monotonic()-start
   assert legal(raw,a);times.append(elapsed);nodes.append(info['nodes']);errors.append(info.get('error'))
  tree=root/'skill';shutil.copytree(C,tree,ignore=shutil.ignore_patterns('__pycache__','game','scratch'));(tree/'game').mkdir()
  current=selected[-1][0];(tree/'game/state.json').write_text(json.dumps(current))
  (tree/'scripts/program_policy.py').write_text('import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n')
  start=time.monotonic();proc=subprocess.Popen([sys.executable,'scripts/decide.py'],cwd=tree,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  time.sleep(.15);(tree/'game/state.json').write_text(json.dumps(current|{'seq':current['seq']+1}))
  out,err=proc.communicate(timeout=2.5);elapsed=time.monotonic()-start;assert proc.returncode==0 and json.loads(out)['refresh_required']
 report={'warm_file_to_action_s':quantiles(times),'internal_nodes':quantiles(nodes),'errors':sum(bool(x) for x in errors),'stale_while_hung':{'elapsed_s':elapsed,'refresh_required':True,'stale_action_emitted':False},'scope':'Warm process: file/history reads, parse, public features, decision; imports already initialized. Cold CLI measurements separately include interpreter/import/worker startup. OS/filesystem scheduling is not hard real time.'}
 write(ROOT/'docs/secret_hunter_next/pipeline-checks.json',report);finish('pipeline-checks',actual_short=len(selected)+1);print(json.dumps(report))
if __name__=='__main__':main()
