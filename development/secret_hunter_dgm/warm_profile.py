"""Measure warm file-to-action calls and a stale observation during a hung worker."""
import json,shutil,sys,tempfile,time,subprocess
from pathlib import Path
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
from development.secret_hunter_dgm.accounting import reserve,finish
C=ROOT/'development/secret_hunter_dgm/release/secret-hunter-program'
def main():
 reserve('warm-profile',short=120,final=True)
 sys.path.insert(0,str(C/'scripts'))
 from program_policy import decide
 from state_features import with_public_history
 from action_validator import legal
 cfg=json.loads((C/'config.json').read_text());src=ROOT/'experiments/secret-hunter-dgm-c1-screen';zs=[]
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
 report={'warm_file_to_action_s':quantiles(times),'internal_nodes':quantiles(nodes),'errors':sum(bool(x) for x in errors),'scope':'Complete warm file/history/parse/features/decision; imports already initialized. Cold process and fault evidence separate.'}
 write(ROOT/'docs/secret_hunter_dgm/warm-profile.json',report);finish('warm-profile',actual_short=len(selected));print(json.dumps(report))
if __name__=='__main__':main()
