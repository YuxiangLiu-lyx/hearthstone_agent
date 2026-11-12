"""Recompute paired development evidence and keep rejected local-learning evidence."""
import json
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write,readlines
from development.benchmarks.run import fingerprint
from development.teacher_eval.compare import compare
D=ROOT/'docs/secret_hunter_chance';W=ROOT/'development/secret_hunter_chance';E=ROOT/'experiments'
pairs=[('m1-screen','c1-screen'),('m1-response','c1-response'),('m1-response','c2-response'),('c1-response','c2-response'),('m1-retain','c1-retain'),('m1-retain','c2-retain'),('c1-retain','c2-retain'),('d1-retain','c2-retain')]
comparisons={a+'__'+b:compare(E/('secret-hunter-chance-'+a),E/('secret-hunter-chance-'+b)) for a,b in pairs}
write(D/'development-results.json',comparisons)
cs=readlines(D/'counterfactual.jsonl')
def gain(c):
 q=c['chance'];chosen=next(v for v in q['comparisons'] if v['action']==c['alternative'])
 return chosen['value']-q['comparisons'][0]['value']
def delta(c):return c['alternatives'][1]['win_rate']-c['alternatives'][0]['win_rate']
train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation']
scores=[{'threshold':t,'train_conditional_delta':sum(delta(c) for c in train if gain(c)>=t)/len(train)} for t in (0,1,2,4,8)]
best=max(scores,key=lambda x:(x['train_conditional_delta'],x['threshold']))
report={'train_games':len(train),'validation_games':len(val),'grid':scores,'chosen_on_train':best,'validation_conditional_delta':sum(delta(c) for c in val if gain(c)>=best['threshold'])/len(val),'all_c1_train_delta':sum(map(delta,train))/len(train),'all_c1_validation_delta':sum(map(delta,val))/len(val),'deployed':False,'reason':'Tiny conditional sample, held-out regression; no reliable evaluation-learning gain. No learned weights or fitted gate included in release.'}
write(D/'evaluation-learning.json',report)
registry=[]
for arm,parent,hypothesis,decision in [('M1','previous round M1','Mechanism reference, unchanged','Retained as development control; remains unpromoted'),('C1','M1','Public exact/sampled summon chance plus contingent deterministic continuation','166/192 but 327/384 retention, behind C2. No reliable held-out counterfactual gain; do not retain'),('C2','C1','Evaluate each chance endpoint through bounded visible attack response; reject unsupported reply','328/384 vs M1 325/384 and D1 319/384 on independent retention. Freeze for final; development estimate only')]:
 runs=[]
 for p in sorted(E.glob('secret-hunter-chance-'+arm.lower()+'-*')):
  if (p/'summary.json').exists():runs.append({'path':str(p.relative_to(ROOT)),'summary':json.loads((p/'summary.json').read_text())})
 registry.append({'candidate':arm,'parent':parent,'hypothesis':hypothesis,'source_sha256':fingerprint(W/'candidates'/arm),'deck':'Fixed D1 deck','runs':runs,'decision':decision})
write(D/'candidates.json',registry)
for k in ('m1-retain__c2-retain','d1-retain__c2-retain'):print(k,json.dumps(comparisons[k]['hard_family_macro']))
