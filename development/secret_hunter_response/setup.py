"""Pre-register a public-response research round before collecting any new games."""
import json, os, shutil, subprocess, time
from pathlib import Path
from development.secret_hunter_program.common import ROOT, sha, write
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
D=ROOT/'docs/secret_hunter_response'; W=ROOT/'development/secret_hunter_response'
def main():
 assert not (D/'freeze.json').exists()
 old=json.loads((ROOT/'docs/secret_hunter_dgm/checkpoint.json').read_text())
 used=set(old['used_seed_values']); sources=[]
 def visit(x):
  if isinstance(x,dict):
   if isinstance(x.get('seed'),int):used.add(x['seed'])
   for k,v in x.items():
    if isinstance(v,int) and (k=='start' or k.endswith('_start')):
     n=x.get(k.replace('start','seeds'),x.get('seeds',x.get('seed_count',1)))
     used.update(range(v,v+(n if isinstance(n,int) and 0<n<10000 else 1)))
    if k in ('used_seeds','used_seed_values','seeds','seed_list') and isinstance(v,list):used.update(z for z in v if isinstance(z,int))
    if k in ('seed_blocks','reserved_blocks') and isinstance(v,dict):
     for b in v.values():
      if isinstance(b,list) and len(b)==2 and all(isinstance(z,int) for z in b):used.update(range(b[0],b[0]+b[1]))
    visit(v)
  elif isinstance(x,list):
   for v in x:visit(v)
 for folder in ('docs','development','experiments'):
  for base,dirs,files in os.walk(ROOT/folder):
   dirs[:]=[d for d in dirs if d not in ('games','__pycache__','secret_hunter_response','p1','p2','scratch','release')]
   for name in files:
    if not (name.endswith('.json') or name=='results.jsonl'):continue
    p=Path(base)/name
    if p.stat().st_size>40_000_000:continue
    try:rows=[json.loads(l) for l in p.read_text().splitlines()] if name.endswith('.jsonl') else [json.loads(p.read_text())]
    except (ValueError,UnicodeError):continue
    n=len(used)
    for row in rows:visit(row)
    if len(used)>n:sources.append(str(p.relative_to(ROOT)))
 blocks={'response_data':[960000,40],'development':[960100,800],'final_core':[961000,80],'final_guardrail':[962000,20],'client':[963000,4],'counterfactual':[964000,5000]}
 assert not any(set(range(s,s+n))&used for s,n in blocks.values())
 write(D/'seed-audit.json',{'used_seed_values':sorted(used),'sources':sources,'reserved_blocks':blocks})
 protected={p:sha(ROOT/p) for p in subprocess.check_output(['git','ls-files'],text=True).splitlines() if (ROOT/p).is_file()}
 write(D/'protected.json',protected)
 for n in ('Y1','K1'):
  shutil.copytree(ROOT/'development/secret_hunter_dgm/candidates'/n,W/'candidates'/n,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
 from development.secret_hunter_dgm.deck_guard import check
 for n in ('Y1','K1'):check(W/'candidates'/n)
 freeze={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'baselines':{n:fingerprint(W/'candidates'/n) for n in ('Y1','K1')},'deck_sha256':sha(W/'candidates/Y1/deck.json'),'populations':{n:{'sha256':sha(ROOT/f'development/teacher_eval/{n}.json'),'opponents':snapshot(json.loads((ROOT/f'development/teacher_eval/{n}.json').read_text()))} for n in ('core','guardrail')}}
 write(D/'freeze.json',freeze)
 write(D/'plan.json',{'started':time.time(),'seed_blocks':blocks,'final_core':{'start':961000,'seeds':80,'arms':['Y1','K1','one_challenger'],'games':2880},'final_guardrail':{'start':962000,'seeds':20,'arms':3,'games':1680},'primary':'0.5 * Astra family mean + 0.5 * Bot2 family mean','promotion':{'Y1_primary_gain':.01,'paired_seed_95_lower_strictly_greater':0,'family_max_drop':.05,'old_overall_max_drop':.03,'old_opponent_max_drop':.10,'runtime':'Complete cold CLI <=2 seconds in independent normal and injected fault checks; no unexplained illegal/stale actions; test extracted ZIP'},'statistics':'10000 paired bootstrap draws of whole seed groups; all opponents and both seats remain together. K1 superiority requires its paired interval.','response_validation':'Fixed seed-group split by seed modulo 5: 0 test, 1 calibration, 2/3/4 fit. No game identity, seed, proxy name, outcomes, hidden cards or future events in predictors. Multi-label actual public responses.','model_boundary':'Learned models and old Bigram counts are offline only; runtime uses independently implemented public feasibility rules and bounded scenario search, with no fitted weights.','stop':['16000 full attempts','80000 short attempts','21600 cumulative experiment seconds','5000 full/2700 seconds final reserve','Final opening freezes all strategy selection. A failed final is a negative result.']})
 write(D/'budget.json',{'limits':{'full_games':16000,'short_branches':80000,'experiment_seconds':21600},'final_reserve':5000,'final_time_reserve':2700,'runs':[]})
 write(D/'candidates.json',{n:{'parent_ids':['dgm-'+n],'status':'research_baseline','source_sha256':fingerprint(W/'candidates'/n)} for n in ('Y1','K1')})
 print(json.dumps({'prior_seed_values':len(used),'protected_files':len(protected),'blocks':blocks}))
if __name__=='__main__':main()
