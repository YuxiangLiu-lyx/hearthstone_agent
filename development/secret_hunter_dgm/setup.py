"""Freeze the original Krush deck and inherited research before new experiments."""
import collections, json, os, shutil, subprocess, time
from pathlib import Path
from development.secret_hunter_program.common import ROOT, sha, write
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
D=ROOT/'docs/secret_hunter_dgm'; W=ROOT/'development/secret_hunter_dgm'
EXPECTED='54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4'
def main():
 assert not (D/'freeze.json').exists()
 assert sha(ROOT/'secret-hunter-program/deck.json')==EXPECTED
 used=set();sources=[]
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
      if isinstance(b,list) and len(b)==2 and all(isinstance(n,int) for n in b):used.update(range(b[0],b[0]+b[1]))
    visit(v)
  elif isinstance(x,list):
   for v in x:visit(v)
 for folder in ('experiments','development','docs'):
  for base,dirs,files in os.walk(ROOT/folder):
   dirs[:]=[d for d in dirs if d not in ('games','__pycache__','secret_hunter_dgm','p1','p2','replay','scratch')]
   for f in files:
    if not (f.endswith('.json') or f=='results.jsonl'):continue
    p=Path(base)/f
    if p.stat().st_size>40_000_000:continue
    try:rows=[json.loads(x) for x in p.read_text().splitlines()] if p.suffix=='.jsonl' else [json.loads(p.read_text())]
    except (ValueError,UnicodeError):continue
    before=len(used)
    for row in rows:visit(row)
    if len(used)>before:sources.append(str(p.relative_to(ROOT)))
 blocks={'pilot':[950000,12],'development':[950100,600],'core':[951000,80],'guardrail':[952000,20],'client':[953000,4]}
 assert not any(set(range(s,s+n))&used for s,n in blocks.values())
 write(D/'seed-audit.json',{'used_seeds':sorted(used),'sources':sources,'reserved_blocks':blocks})
 protected={p:sha(ROOT/p) for p in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines() if (ROOT/p).is_file()}
 write(D/'protected.json',protected)
 for name,source in [('K0','secret-hunter-program'),('K1','development/secret_hunter_next/candidates/M1'),('C0','development/secret_hunter_chance/candidates/C2')]:
  dest=W/'candidates'/name
  shutil.copytree(ROOT/source,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
  shutil.copyfile(ROOT/'secret-hunter-program/deck.json',dest/'deck.json')
 freeze={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'baselines':{n:fingerprint(W/'candidates'/n) for n in ('K0','K1')},'deck_sha256':EXPECTED,'populations':{n:{'path':f'development/teacher_eval/{n}.json','sha256':sha(ROOT/f'development/teacher_eval/{n}.json'),'opponents':snapshot(json.loads((ROOT/f'development/teacher_eval/{n}.json').read_text()))} for n in ('core','guardrail')}}
 write(D/'freeze.json',freeze)
 write(D/'plan.json',{'started':time.time(),'seed_blocks':blocks,'final_core':{'seeds':80,'opponents':6,'seats':[1,2],'arms':['K0','K1','one_frozen_challenger'],'games':2880},'final_guardrail':{'seeds':20,'opponents':14,'seats':[1,2],'arms':3,'games':1680},'primary':'0.5 * mean(three Astra rates) + 0.5 * mean(two bot2 rates)','gates':{'K0_primary_gain':.01,'K0_primary_paired_lower_strictly_greater':0,'family_max_drop':.05,'guardrail_overall_max_drop':.03,'guardrail_single_max_drop':.10,'K1':'Report gain and paired interval; no automatic superiority claim','reliability':'Fixed deck, public inputs, no unexplained errors, complete CLI target <=2s, extracted artifact validation and traces'},'statistics':'10000 paired bootstrap draws of whole common seed clusters, both seats/all opponents retained. Errors remain in denominator.','counterfactual':'Start 60 stratified source games; original action retained even outside fast model. Conditional hidden-state diagnostics explicitly labeled. Whole seed clusters determine split. Adaptive extra samples for selected disagreements.','selection':'Offline Codex proposes explainable code changes from diagnostics; archive complementary parents; common-block comparisons. Runtime Python only, no learned weights. Target 8-12 substantive children, at least 3 evidence-backed directions, stop at documented plateau/reliability/budget.','stop':['16000 full attempt reservations','80000 short branches','21600 cumulative experiment seconds','Protect 5000 games and 2700 seconds for final work','Do not continue after final opening or manufacture empty variants']})
 write(D/'budget.json',{'limits':{'full_games':16000,'short_branches':80000,'experiment_seconds':21600},'final_reserve':5000,'final_time_reserve':2700,'runs':[]})
 write(D/'candidates.json',{'K0':{'parent_ids':['historical-H7'],'status':'confirmed_champion','hypothesis':'Frozen original H7; historical status only, re-evaluated here'},'K1':{'parent_ids':['historical-M1'],'status':'provisional','hypothesis':'M1 mechanisms transferred to byte-identical original deck; no inherited D1 result'},'C0':{'parent_ids':['historical-chance-C2'],'status':'provisional','hypothesis':'Retest exact/sampled summon and response search on original Krush/Misdirection deck'}})
 print(json.dumps({'prior_seed_values':len(used),'protected_files':len(protected),'blocks':blocks}))
if __name__=='__main__':main()
