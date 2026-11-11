"""Freeze this round before inspecting any new development outcomes."""
import json, subprocess, shutil, time, os
from pathlib import Path
from datetime import datetime, timezone
from development.secret_hunter_program.common import ROOT, sha, write
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
D=ROOT/'docs/secret_hunter_chance'; W=ROOT/'development/secret_hunter_chance'
used=set(); sources=[]
for folder in ('experiments','development/experiments','docs'):
    paths=[]
    for base,dirs,files in os.walk(ROOT/folder):
        dirs[:]=[d for d in dirs if d not in ('games','secret_hunter_chance','__pycache__','p1','p2','seat','trajectory','replay') and not d.startswith('g_')]
        paths.extend(Path(base)/f for f in files if f=='results.jsonl' or f.endswith('.json'))
    for p in paths:
        if any(x in p.parts for x in ('games','secret_hunter_chance')) or any(x.startswith('g_') for x in p.parts):continue
        if p.stat().st_size>40_000_000:continue
        try:
            rows=[json.loads(x) for x in p.read_text().splitlines()] if p.suffix=='.jsonl' else [json.loads(p.read_text())]
        except (ValueError,UnicodeError):continue
        before=len(used)
        def visit(x):
            if isinstance(x,dict):
                if isinstance(x.get('seed'),int):used.add(x['seed'])
                for k,v in x.items():
                    if isinstance(v,int) and (k=='start' or k.endswith('_start') or k=='seed_start'):
                        n=x.get(k.replace('start','seeds'),x.get('seeds',x.get('seed_count',1)))
                        used.update(range(v,v+(n if isinstance(n,int) and 0<n<10000 else 1)))
                    elif k in ('seeds','seed_list') and isinstance(v,list):used.update(z for z in v if isinstance(z,int))
                    visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        for row in rows:visit(row)
        if len(used)>before:sources.append(str(p.relative_to(ROOT)))
blocks={'audit':[940000,2],'development':[940100,200],'core':[941000,40],'guardrail':[942000,20],'client':[943000,4]}
assert all(not (set(range(start,start+n))&used) for start,n in blocks.values())
write(D/'seed-audit.json',{'used_seeds':sorted(used),'sources':sources,'reserved_blocks':blocks,'note':'Scanned historical result rows and nested plan/config fields, not a numeric threshold. Final blocks are now reserved and never become unseen again.'})
protected={p:sha(ROOT/p) for p in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines() if (ROOT/p).is_file()}
write(D/'protected.json',protected)
for name,source in [('D1','development/teacher_eval/candidates/D1'),('H7','secret-hunter-program'),('M1','development/secret_hunter_next/candidates/M1'),('C1','development/secret_hunter_next/candidates/M1')]:
    shutil.copytree(ROOT/source,W/'candidates'/name,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
freeze={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'baselines':{n:fingerprint(W/'candidates'/n) for n in ('D1','H7')},'deck_sha256':sha(W/'candidates/D1/deck.json'),'populations':{n:{'path':f'development/teacher_eval/{n}.json','sha256':sha(ROOT/f'development/teacher_eval/{n}.json'),'opponents':snapshot(json.loads((ROOT/f'development/teacher_eval/{n}.json').read_text()))} for n in ('core','guardrail')}}
write(D/'freeze.json',freeze)
write(D/'plan.json',{'stage':'M0','seed_blocks':blocks,'final_core':{'seeds':40,'opponents':6,'seats':[1,2],'arms':['D1','H7','one_frozen_new_candidate'],'games':1440},'final_guardrail':{'seeds':20,'opponents':14,'seats':[1,2],'arms':3,'games':1680},'primary':'0.5 * mean(three Astra win rates) + 0.5 * mean(two bot2 win rates)','gates':{'specialist':'versus D1: primary gain >= .01, paired seed-cluster 95% lower > 0, neither Astra nor bot2 declines > .05','general':'specialist gate plus old-pool versus H7 overall decline <= .03 and each opponent decline <= .10','reliability':'No unexplained errors, illegal actions, unexpected emergency fallback, or observed >2s local CLI decision; current-sequence legal output and exact artifact reproduction'},'statistics':'10000 paired bootstrap replicates of whole shared seed clusters; report board, sticky, weakest matchup and both seats. No claims of formal noninferiority.','errors':'Every scheduled attempt remains charged. Harness errors count as zero score; do not drop anomalous pairs. An unexplained reliability error blocks promotion.','selection':'Start from unpromoted M1 with frozen D1/H7 controls. C1 exact/sampled public chance effects plus bounded adaptive continuation; C2 targeted search/guide or evaluation ablation chosen from development evidence. Use whole-game held-out counterfactual cases, no fitted weights in release. Re-evaluate parents on each fresh block, then independent retention. Freeze one candidate before final; no final-driven changes.','stop':['8000 charged full attempts','30000 charged short branches','4 hours cumulative experiment wall time','At most three structural rounds plus one development retention block','Preserve 3200 full attempts for final/ZIP/client; reduce screening if necessary'],'limits':'Fixed D1 deck, fixed existing opponents, no models or external services during decisions. Public views only. Full terminal continuations count as full games.'})
write(D/'budget.json',{'limits':{'full_games':8000,'short_branches':30000,'experiment_seconds':14400},'final_reserve':3200,'created_utc':datetime.now(timezone.utc).isoformat(),'runs':[]})
print(json.dumps({'used_seed_count':len(used),'protected_files':len(protected),'freeze':freeze},indent=2))
