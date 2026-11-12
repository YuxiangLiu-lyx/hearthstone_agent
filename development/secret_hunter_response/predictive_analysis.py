"""Seed-cluster uncertainty for predictive ablations; no additional fitting."""
import json,random
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.calibrate import predict,LABELS
D=ROOT/'docs/secret_hunter_response';rows=[r for r in readlines(D/'opponent_replies.jsonl') if r['audit']['seed']%5==0];models=json.loads((D/'models-offline-only.json').read_text());bigram=json.loads((D/'bigram-filtered-offline.json').read_text());seeds=sorted({r['audit']['seed'] for r in rows});loss={}
for mode,m in models.items():
 loss[mode]={seed:[] for seed in seeds}
 for r in rows:
  ps=predict(m['weights'],r,mode,bigram,m['temperature']);loss[mode][r['audit']['seed']].append(sum((p-r['labels'][k])**2 for p,k in zip(ps,LABELS))/6)
results={};rng=random.Random(143)
for mode in models:
 if mode=='baseline':continue
 ds=[]
 for _ in range(10000):
  group=rng.choices(seeds,k=len(seeds));n=sum(len(loss[mode][s]) for s in group)
  ds.append(sum(sum(loss[mode][s])-sum(loss['baseline'][s]) for s in group)/n)
 ds.sort();results[mode]={'delta_brier':sum(sum(loss[mode][s])-sum(loss['baseline'][s]) for s in seeds)/len(rows),'paired_seed_95':[ds[250],ds[9750]]}
write(D/'calibration-cluster-intervals.json',{'test_seeds':len(seeds),'test_rows':len(rows),'differences':results,'sign':'Negative error difference is better. Only 8 groups; intervals are descriptive and do not remove model-selection uncertainty.'});print(json.dumps(results))
