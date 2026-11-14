"""Atomic counterfactual queue, charged attempts and process-group timeouts."""
import argparse
import fcntl
import json
from pathlib import Path
import signal
import sys
import time
import traceback
from development.secret_hunter_long.study import ROOT,RUN,HERE,check
from development.secret_hunter_long.provenance import archive_code
from development.benchmarks.run import fingerprint
from development.secret_hunter_mcgs import train
from development.secret_hunter_mcgs.supervision import GameProcess
from development.secret_hunter_program.common import sha

def connect():
    db=train.connect(RUN)
    db.executescript('''CREATE TABLE IF NOT EXISTS cf_jobs(key TEXT PRIMARY KEY,kind TEXT,job TEXT,status TEXT,result_path TEXT);
    CREATE TABLE IF NOT EXISTS cf_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT,status TEXT,started REAL,finished REAL);''')
    db.commit();return db

def reserve(kind,jobs):
    db=connect()
    assert not train.meta(db,'final_opened',False)
    assert not train.meta(db,'selection_opened',False),'No new labels after selection opening'
    for key,job in jobs:
        path=RUN/(kind+'-labels')/(key+'.json')
        existing=db.execute('select * from cf_jobs where key=?',(key,)).fetchone()
        if existing:assert json.loads(existing['job'])==job and existing['kind']==kind
        else:db.execute('insert into cf_jobs values (?,?,?,?,?)',(key,kind,json.dumps(job),'pending',str(path)))
    db.commit()

def run(kind,workers,limit):
    db=connect();m=train.meta(db,'manifest')
    assert not train.meta(db,'final_opened',False)
    assert not train.meta(db,'selection_opened',False),'No training after selection opening'
    check(m)
    with (RUN/'cf-writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with db:
            for r in db.execute("select * from cf_jobs where status in ('running','pending')").fetchall():
                path=Path(r['result_path']);saved=json.loads(path.read_text()) if path.exists() else {}
                expected=json.loads(r['job'])
                durable=saved.get('terminal') and saved.get('job')==expected and not saved.get('error')
                db.execute('update cf_jobs set status=? where key=?',('done' if durable else 'pending',r['key']))
            db.execute("update cf_attempts set status='interrupted',finished=? where status='running'",(time.time(),))
        todo=db.execute("select * from cf_jobs where kind=? and status='pending' order by key",(kind,)).fetchall()
        lineage={r['name']:r['sha256'] for r in json.loads((HERE/'lineage.json').read_text())}
        needed={a for row in todo for k,a in json.loads(row['job']).items() if k in ('arm','policy_arm')}
        candidates={a:fingerprint(HERE/'candidates'/a) for a in needed}
        assert all(candidates[a]==lineage[a] for a in needed),'immutable counterfactual candidate changed'
        active={};ix=0;started=0;stop=False;consecutive_errors=0
        def signal_stop(*_):
            nonlocal stop
            stop=True
        signal.signal(signal.SIGTERM,signal_stop);signal.signal(signal.SIGINT,signal_stop)
        train.setmeta(db,'cf_pid',__import__('os').getpid())
        try:
            while active or ix<len(todo):
                used=db.execute('select count(*) from cf_attempts').fetchone()[0]
                while ix<len(todo) and len(active)<workers and used<m['limits']['continuations'] and started<limit and time.time()<m['candidate_generation_deadline'] and not stop:
                    row=todo[ix];ix+=1;path=Path(row['result_path']);request=path.with_suffix('.request.json')
                    harness=archive_code(RUN,['development/secret_hunter_long/'+name for name in ('cfqueue.py',kind+'.py')])
                    train.atomic(request,{'kind':kind,'job':json.loads(row['job']),'output':str(path),'harness_sha256':harness,'candidate_fingerprints':candidates})
                    with db:
                        aid=db.execute("insert into cf_attempts(key,status,started) values (?,'running',?)",(row['key'],time.time())).lastrowid
                        db.execute("update cf_jobs set status='running' where key=?",(row['key'],))
                    train.setmeta(db,'continuations',used+1)
                    proc=GameProcess([sys.executable,'-m','development.secret_hunter_long.cfqueue','worker','--request',str(request)],ROOT,path.with_suffix('.log'))
                    active[aid]=(proc,row);used+=1;started+=1
                if not active:break
                time.sleep(.2)
                for aid,(proc,row) in list(active.items()):
                    if proc.process.poll() is None and time.monotonic()-proc.started<90:continue
                    proc.close();del active[aid];path=Path(row['result_path'])
                    result=json.loads(path.read_text()) if path.exists() else {'error':'worker_timeout_or_crash'}
                    status='error' if result.get('error') or not result.get('terminal') else 'done'
                    if status=='error':
                        train.atomic(RUN/'cf-errors'/f'{aid:06d}.json',{'job':json.loads(row['job']),'result':result})
                        consecutive_errors+=1
                        if consecutive_errors>=3:stop=True
                    else:consecutive_errors=0
                    with db:
                        db.execute('update cf_attempts set status=?,finished=? where id=?',(status,time.time(),aid))
                        db.execute('update cf_jobs set status=? where key=?',(status,row['key']))
                    if aid%50==0 or status=='error':print(json.dumps({'kind':kind,'attempt':aid,'status':status,'error':result.get('error')}),flush=True)
        finally:
            for aid,(proc,row) in active.items():
                proc.close()
                with db:
                    db.execute("update cf_attempts set status='interrupted',finished=? where id=?",(time.time(),aid))
                    db.execute("update cf_jobs set status='pending' where key=?",(row['key'],))
            train.setmeta(db,'cf_pid',None)
        print(json.dumps({'kind':kind,'cf_status':dict(db.execute('select status,count(*) from cf_jobs where kind=? group by status',(kind,)).fetchall())}))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run','worker']);p.add_argument('--kind',choices=['mulligan','tactical'])
    p.add_argument('--workers',type=int,default=3);p.add_argument('--limit',type=int,default=24000);p.add_argument('--request',type=Path)
    a=p.parse_args()
    if a.command=='run':run(a.kind,a.workers,a.limit)
    else:
        request=json.loads(a.request.read_text());job=request['job']
        try:
            if request['kind']=='mulligan':
                from development.secret_hunter_long.mulligan import execute
            else:
                from development.secret_hunter_long.tactical import execute
            result=execute(job);result['job']=job
        except Exception:result={'job':job,'error':traceback.format_exc()}
        train.atomic(Path(request['output']),result)

if __name__=='__main__':main()
