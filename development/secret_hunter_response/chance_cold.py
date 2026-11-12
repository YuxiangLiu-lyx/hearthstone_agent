"""Cold CLI checks on the largest recorded public chance trees, exact release."""
import json,math,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.accounting import reserve,finish
C=ROOT/'development/secret_hunter_response/release/secret-hunter-program'
reserve('chance-cold',short=50)
sys.path.insert(0,str(C/'scripts'));from action_validator import legal
src=ROOT/'experiments/secret-hunter-response-e1-retain';states=[]
for r in readlines(src/'results.jsonl'):
 for z in readlines(src/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl'):
  q=z['info'].get('chance',{})
  if q.get('active'):states.append((q.get('nodes',0),z['state'],r['game']))
states.sort(key=lambda x:(-x[0],x[2],x[1]['seq']));results=[]
with tempfile.TemporaryDirectory() as t:
 root=Path(t)/'skill';shutil.copytree(C,root);(root/'game').mkdir()
 for nodes,s,game in states[:24]:
  (root/'game/state.json').write_text(json.dumps(s|{'game_id':game+'-cold'}))
  start=time.monotonic();p=subprocess.run([sys.executable,'scripts/decide.py'],cwd=root,capture_output=True,text=True,timeout=3);elapsed=time.monotonic()-start
  output=json.loads(p.stdout);assert p.returncode==0 and output['seq']==s['seq'] and legal(s,output['action'])
  last=readlines(root/'scratch/decisions.jsonl')[-1]
  assert not last.get('worker_error') and not last['info'].get('error') and not last['info'].get('fallback')
  results.append({'source_game':game,'seq':s['seq'],'previous_nodes':nodes,'elapsed_s':elapsed,'chance':last['info'].get('chance'),'legal':True})
times=sorted(r['elapsed_s'] for r in results);q={str(p):times[math.ceil(p*len(times))-1] for p in (.5,.95,.99,1)}
write(ROOT/'docs/secret_hunter_response/chance-cold.json',{'n':len(results),'latency_s':q,'over_2s':sum(x>2 for x in times),'details':results})
finish('chance-cold',actual_short=len(results));print(json.dumps(q))
