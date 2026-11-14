"""Run only these already-defined experiments after the initial deck batch."""
import json
import subprocess
import sys
import time
from development.secret_hunter_long.study import RUN,ROOT
from development.secret_hunter_mcgs import train

STAGES=[
    ['--batch','mechanism-core','--arms','B','KO','TMILL','TRPLY','BL2','--start','51402000','--seeds','20','--workers','3','--warm'],
    ['--batch','lethal-guard','--arms','B','BL2','--start','51403000','--seeds','4','--pool','guardrail','--workers','3','--warm'],
]

def main():
    db=train.connect(RUN);m=train.meta(db,'manifest');plan=RUN/'defined-next-stages.json'
    definition={'wait_for':'deck-screen','stages':STAGES,'policy':'fixed candidates and new seeds; no unattended proposals or code changes'}
    if plan.exists():assert json.loads(plan.read_text())==definition
    else:train.atomic(plan,definition)
    while time.time()<m['candidate_generation_deadline']:
        row=db.execute("select status from batches where id='deck-screen'").fetchone()
        if row and row['status']=='done':break
        time.sleep(5)
    else:raise RuntimeError('development deadline before deck screen completion')
    report=json.loads((RUN/'batches/deck-screen/report.json').read_text())
    assert all(not r['all']['harness_errors'] for r in report['arms'].values())
    for args in STAGES:
        assert time.time()<m['candidate_generation_deadline']
        print(json.dumps({'starting_defined_stage':args}),flush=True)
        subprocess.run([sys.executable,'-m','development.secret_hunter_long.study','run']+args,cwd=ROOT,check=True)
        batch=args[args.index('--batch')+1]
        row=db.execute('select status from batches where id=?',(batch,)).fetchone()
        assert row and row['status']=='done',('incomplete defined stage',batch)
    print(json.dumps({'defined_stages_complete':True}),flush=True)

if __name__=='__main__':main()
