"""Execute an immutable list of already-reviewed commands, never propose code."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from development.secret_hunter_long.study import ROOT,RUN
from development.secret_hunter_program.common import sha
from development.secret_hunter_mcgs import train

def main():
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);a=p.parse_args()
    plan=json.loads(a.plan.read_text());digest=sha(a.plan);db=train.connect(RUN);manifest=train.meta(db,'manifest')
    while True:
        assert time.time()<manifest['candidate_generation_deadline']
        row=db.execute('select status from batches where id=?',(plan['wait_for'],)).fetchone()
        if row and row['status']=='done':break
        time.sleep(5)
    for args in plan['commands']:
        assert sha(a.plan)==digest and not train.meta(db,'final_opened',False)
        assert time.time()<manifest['candidate_generation_deadline']
        print(json.dumps({'defined_plan':str(a.plan),'sha256':digest,'command':args}),flush=True)
        subprocess.run([sys.executable,'-m']+args,cwd=ROOT,check=True)
    print(json.dumps({'defined_plan_complete':str(a.plan)}),flush=True)

if __name__=='__main__':main()
