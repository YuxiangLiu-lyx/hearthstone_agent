"""Open locked H2 route labels; evaluate coefficients without refitting."""
import collections,json,time
from development.secret_hunter_astra_sprint.study import RUN,HERE
from development.secret_hunter_astra_sprint.tactical import setup
from development.secret_hunter_astra_sprint.labels import read
from development.secret_hunter_astra_sprint.train_ranker import before_handoff,evaluate
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import sha

def main():
 lock=RUN/'hypotheses/H2-lock.json';record=json.loads(lock.read_text());model=json.loads((RUN/'H2-fitted-ranker.json').read_text())
 assert sha(RUN/'H2-fitted-ranker.json')==record['fitted_model_sha256']
 setup('DARCL2')
 from race_plan import value
 from tactical_model import prepare
 from public_response import worst_reply
 from development.secret_hunter_astra_sprint.rank_features import vector,eligible
 cfg=json.loads((HERE/'candidates/DARCL2/config.json').read_text());results={};cache={}
 for split,worlds,manifest in [('train',(2,),'manifest-diagnostic-dev-late1-DARCL2.json'),('validation',(0,1,2),'manifest-diagnostic-holdout2-late1-DARCL2.json')]:
  cases=set(json.loads((RUN/'tactical-sources'/manifest).read_text())['cases']);pairs,_=read(split,worlds,lock,cases);rows=[];skipped=0
  for r in pairs:
   def endpoint(route):
    key=(r['case'],r['world'],route)
    if key in cache:return cache[key]
    label=json.loads((RUN/'tactical-labels'/f"{r['case']}-w{r['world']}-{route}.json").read_text());s=before_handoff(label)
    if not s or not eligible(s) or min(s[k]['hero']['health'] for k in ('you','opponent'))<=0:cache[key]=None;return None
    initial=prepare({**s,'planning_mode':'response'});reply=worst_reply(initial,cfg,time.monotonic()+2,48)
    if not reply['supported'] or reply['visible_lethal_found']:cache[key]=None;return None
    cache[key]=(vector(initial,reply['state']),.15*value(initial,cfg)+.85*reply['value']);return cache[key]
   base=endpoint('baseline');other=endpoint(r['route'])
   if not base or not other or abs(other[1]-base[1])>50:skipped+=1;continue
   rows.append({k:r[k] for k in ('case','seed','world','route','delta')}|{'x':[a-b for a,b in zip(other[0],base[0])],'base':base[0],'alternative':other[0],'prior_delta':other[1]-base[1]})
  results[split]={'worlds':worlds,'pairs':len(rows),'skipped':skipped,**evaluate(rows,model['coef'])}
 result={'created':time.time(),'candidate':'PRR','lock_sha256':sha(lock),'model_sha256':sha(RUN/'H2-fitted-ranker.json'),'results':results,'scope':'Held-out teacher endpoint ranking, not actual deployable-policy or full-game gains; no refitting.'}
 ledger.atomic(RUN/'H2-heldout-ranking.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
