"""Bounded next development blocks; each child invocation remains resumable."""
import json
import subprocess
import sys
import time
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train

def main():
    db=train.connect(RUN)
    while True:
        row=db.execute('select status from batches where id="dev-guard"').fetchone()
        if row and row[0]=='done' and train.meta(db,'pid') is None:break
        assert time.time()<train.meta(db,'manifest')['candidate_generation_deadline']
        time.sleep(2)
    time.sleep(.25)
    jobs=[
        ['--batch','dev2-core','--arms','B','M','L2','ML2','--start','41303000','--seeds','12'],
        ['--batch','dev2-guard','--arms','B','M','L2','ML2','--start','41304000','--seeds','4','--pool','guardrail'],
        ['--batch','conditional-core','--arms','B','M','--start','41310000','--seeds','240','--selection',str(RUN/'conditional-core.json')],
        ['--batch','conditional-guard','--arms','B','M','--start','41311000','--seeds','120','--pool','guardrail','--selection',str(RUN/'conditional-guardrail.json')],
    ]
    for args in jobs:
        name=args[1]
        with (RUN/(name+'.log')).open('a') as log:
            subprocess.run([sys.executable,'-u','-m','development.secret_hunter_final.study','run',*args,'--workers','3','--warm'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        print(json.dumps({'completed':name}),flush=True)

if __name__=='__main__':main()
