"""Hold selected complete plans fixed and collect fresh conditional future samples."""
import json,copy,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.counterfactual import worker
from development.secret_hunter_response.accounting import reserve,finish
def main():
 D=ROOT/'docs/secret_hunter_response';source=readlines(D/'counterfactual-pilot.jsonl');pairs=[(16,'plan-2'),(8,'plan-3'),(13,'plan-1'),(2,'plan-1')];tasks=[]
 for i,pid in pairs:
  r=next(x for x in source if x['case_id']==i);c=copy.deepcopy(r['case']);c['_validation_offset']=71;c['_frozen_plans']=[{k:v for k,v in p.items() if k!='outcomes'} for p in r['plans'] if p['id'] in ('Y1',pid)];tasks.append((c,i,0,20))
 reserve('counterfactual-extended-fixed',full=160,short=1200,seconds=1200);results=[]
 with ProcessPoolExecutor(max_workers=4) as pool,(D/'counterfactual-extended.jsonl').open('w') as f:
  for r in pool.map(worker,tasks):
   results.append(r);f.write(json.dumps(r,separators=(',',':'))+'\n');f.flush();print(r['case_id'],[(p['id'],sum(o['win'] for o in p['outcomes'])) for p in r['plans']],flush=True)
 errors=[o['error'] for r in results for p in r['plans'] for o in p['outcomes'] if o['error']];finish('counterfactual-extended-fixed',actual_full=160,errors=errors);assert not errors

if __name__=='__main__':main()
