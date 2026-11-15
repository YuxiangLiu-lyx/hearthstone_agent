"""Evaluate a locked deployable policy from existing paired root worlds."""
import argparse
import json
import time
from development.secret_hunter_astra_sprint.study import RUN,HERE
from development.secret_hunter_astra_sprint.cfqueue import reserve
from development.secret_hunter_astra_sprint import ledger
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha

def main(arm,lock,source_prefix='sprint'):
    record=json.loads(lock.read_text());assert record['candidate']==arm
    assert record['source_sha256']==fingerprint(HERE/'candidates'/arm)
    sources=[json.loads(p.read_text()) for p in sorted((RUN/'tactical-sources').glob(source_prefix+'-*.json'))]
    jobs=[]
    for src in sources:
        for world in range(3):
            jobs.append((f"{src['case']}-w{world}-policy-{arm}",
                {'case':src['case'],'sample':world,'route':'baseline','arm':'DARCL2','policy_arm':arm}))
    path=RUN/(arm+'-continuation-plan.json')
    plan={'created':time.time(),'arm':arm,'source_sha256':record['source_sha256'],'hypothesis_lock_sha256':sha(lock),
        'roots':len(sources),'jobs':len(jobs),'worlds':[0,1,2],
        'scope':'Actual locked policy from original DARCL2 public prefixes; candidate continues all later own decisions, opponent fixed. Compare each root/world with archived DARCL2 baseline. Whole-game validation remains required.',
        'budget_note':'All attempts charged, including errors/interruption. No new seeds or hidden information enter runtime.'}
    if path.exists():assert json.loads(path.read_text())['source_sha256']==plan['source_sha256']
    else:ledger.atomic(path,plan)
    reserve('tactical',jobs);print(json.dumps(plan,indent=2))

if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--lock',type=Path,required=True)
    p.add_argument('--source-prefix',default='sprint')
    a=p.parse_args();main(a.arm,a.lock,a.source_prefix)
