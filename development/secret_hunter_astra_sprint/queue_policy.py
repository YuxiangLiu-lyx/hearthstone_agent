"""Evaluate a locked deployable policy from existing paired root worlds."""
import argparse
import json
import time
from development.secret_hunter_astra_sprint.study import RUN,HERE
from development.secret_hunter_astra_sprint.cfqueue import reserve
from development.secret_hunter_astra_sprint import ledger
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha

def main(arm,lock,source_prefix='sprint',split='all'):
    record=json.loads(lock.read_text());assert record['candidate']==arm
    assert record['source_sha256']==fingerprint(HERE/'candidates'/arm)
    pattern='*.json' if source_prefix=='all' else source_prefix+'-*.json'
    sources=[r for p in sorted((RUN/'tactical-sources').glob(pattern)) if 'case' in (r:=json.loads(p.read_text())) and 'state' in r and (split=='all' or r['split']==split)]
    jobs=[]
    for src in sources:
        for world in range(3):
            jobs.append((f"{src['case']}-w{world}-policy-{arm}",
                {'case':src['case'],'sample':world,'route':'baseline','arm':'DARCL2','policy_arm':arm}))
    path=RUN/(arm+'-continuation-plan.json')
    plan={'created':time.time(),'arm':arm,'source_sha256':record['source_sha256'],'hypothesis_lock_sha256':sha(lock),
        'roots':len(sources),'jobs':len(jobs),'worlds':[0,1,2],'source_prefix':source_prefix,'split_filter':split,
        'source_status':'Seen development roots only; no independent source validation here' if split=='train' else 'Use the hypothesis chronology to distinguish unopened from already-seen label sources',
        'scope':'Actual locked policy from original DARCL2 public prefixes; candidate continues all later own decisions, opponent fixed. Compare each root/world with archived DARCL2 baseline. Whole-game validation remains required.',
        'budget_note':'All attempts charged, including errors/interruption. No new seeds or hidden information enter runtime.'}
    if path.exists():
        prior=json.loads(path.read_text());assert all(prior[k]==plan[k] for k in ('source_sha256','roots','jobs','worlds')), 'Do not silently expand an existing candidate continuation plan'
    else:ledger.atomic(path,plan)
    reserve('tactical',jobs);print(json.dumps(plan,indent=2))

if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--lock',type=Path,required=True)
    p.add_argument('--source-prefix',default='sprint')
    p.add_argument('--split',choices=['all','train','validation'],default='all')
    a=p.parse_args();main(a.arm,a.lock,a.source_prefix,a.split)
