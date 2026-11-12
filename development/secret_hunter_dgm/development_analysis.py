"""Compare only shared schedules; keep selection estimates separate from final."""
import json
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import compare,index
D=ROOT/'docs/secret_hunter_dgm';E=ROOT/'experiments';report={}
pairs={'screen':[('K0','K1'),('K1','B1'),('K1','C0'),('K1','C1'),('K1','O1')],'round2':[('K1','B1'),('K1','C1'),('K1','O1'),('C1','C2'),('K1','E1'),('C2','S1')],'round3':[('K0','K1'),('K1','E1'),('K1','S1'),('K1','T1'),('E1','X1')],'retain':[('K0','K1'),('K1','E1'),('K0','E1'),('E1','X1'),('E1','Y1'),('X1','Y1')],'guard-dev':[('K0','E1'),('K0','X1'),('K0','Y1')]}
for stage,ps in pairs.items():
 for a,b in ps:
  left=E/f'secret-hunter-dgm-{a.lower()}-{stage}';right=E/f'secret-hunter-dgm-{b.lower()}-{stage}'
  if not (left/'summary.json').exists() or not (right/'summary.json').exists():continue
  q=compare(left,right);ar=index(readlines(left/'results.jsonl'));br=index(readlines(right/'results.jsonl'));changes=[]
  for k,r in ar.items():
   traces=[[z['action'] for z in readlines(p/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl')] for p,row in ((left,r),(right,br[k]))]
   if traces[0]!=traces[1]:changes.append({'pair':k,'first_divergence_index':next((i for i,(x,y) in enumerate(zip(*traces)) if x!=y),min(map(len,traces)))})
  q['games_with_changed_action_trace']=len(changes);q['trace_changes']=changes;report[f'{stage}:{a}->{b}']=q
write(D/'development-results.json',report)
print(json.dumps({k:{'gain_pp':round(100*v.get('hard_family_macro',v['all'])['gain'],3),'ci_pp':[round(100*x,3) for x in v.get('hard_family_macro',v['all'])['gain_seed_cluster_95']],'changed_traces':v['games_with_changed_action_trace']} for k,v in report.items()},indent=2))
