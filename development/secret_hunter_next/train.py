"""Regularized pairwise value learning; game-level split and no final data access."""
import json,math,random,shutil
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_next.features import NAMES
from development.secret_hunter_next.accounting import reserve,finish

def main():
 reserve('preference-learning',short=200)
 cases=readlines(ROOT/'docs/secret_hunter_next/counterfactual-v2.jsonl');assert len(cases)==24
 assert all(o['terminal'] and not o['error'] for c in cases for a in c['alternatives'] for o in a['outcomes'])
 data={'train':[],'validation':[]}
 for c in cases:
  for i,a in enumerate(c['alternatives']):
   for b in c['alternatives'][i+1:]:
    data[c['split']].append(([x-y for x,y in zip(a['features'],b['features'])],12*(a['win_rate']-b['win_rate'])))
 w=[0.]*len(NAMES)
 # Fixed prior/regularizer. Validation games never choose features, steps, or strength.
 for step in range(1200):
  grad=[.25*x for x in w]
  for x,y in data['train']:
   err=sum(a*b for a,b in zip(w,x))-y
   for j,z in enumerate(x):grad[j]+=2*err*z/len(data['train'])
  for j in range(len(w)):w[j]-=.035*grad[j]
 def metrics(rows):
  informative=[(x,y) for x,y in rows if abs(y)>1e-9]
  return {'pairs':len(rows),'informative_pairs':len(informative),'mse':sum((sum(a*b for a,b in zip(w,x))-y)**2 for x,y in rows)/len(rows),'zero_model_mse':sum(y*y for _,y in rows)/len(rows),'direction_accuracy':sum((sum(a*b for a,b in zip(w,x))>0)==(y>0) for x,y in informative)/len(informative) if informative else None}
 report={'features':NAMES,'coefficients':w,'training_games':[c['game'] for c in cases if c['split']=='train'],'validation_games':[c['game'] for c in cases if c['split']=='validation'],'metrics':{k:metrics(v) for k,v in data.items()},'scope':'24 selected development games, six conditional future samples per action, not an estimate over unknown hands; no final block used. Fixed ridge and learning rate. No learned model is eligible for the submission because the current assignment forbids bundled model weights.'}
 write(ROOT/'docs/secret_hunter_next/learning.json',report)
 src=ROOT/'development/secret_hunter_next/candidates/M1';dest=src.parent/'L1';shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
 shutil.copyfile(ROOT/'development/secret_hunter_next/features.py',dest/'scripts/learned_features.py')
 p=dest/'scripts/race_plan.py';s=p.read_text().replace('    return score\n',"    if cfg.get('learned_value'):\n        from learned_features import features\n        score += max(-8., min(8., sum(w*x for w,x in zip(cfg['learned_value'], features(s)))))\n    return score\n");p.write_text(s)
 cfg=json.loads((dest/'config.json').read_text());cfg.update(version='next-L1',parent='M1',learned_value=w);write(dest/'config.json',cfg)
 finish('preference-learning',actual_short=0);print(json.dumps(report))
if __name__=='__main__':main()
