"""Explicit, resumable batches with immutable pools and reserved final seeds."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import ROOT,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot,summarize
from development.teacher_eval.compare import paired
from development.secret_hunter_turn_plans.build import HERE,Y1

RUN=Path(os.environ.get('KRUSH_TURN_RUN',str(ROOT/'runs/turn-plans-20261112'))).resolve()
# A new run receives a fresh four-hour budget. An existing manifest always
# retains its original creation time and deadline across interruptions.
START=time.time()


def initialize(db):
    if train.meta(db,'manifest'):return
    protected=['development/teacher_eval/core.json','development/teacher_eval/guardrail.json',
               'development/teacher_eval/run.py','development/secret_hunter_tactics/run.py',
               'development/opponents/population.py','development/opponents/search.py']
    manifest={'created':START,'deadline':START+14400,'limits':{'seconds':14400,'full_games':5000,'continuations':6000},
              'protected':{p:sha(ROOT/p) for p in protected},'reserved_final_games':0,
              'opponents':{p:snapshot(json.loads((ROOT/p).read_text())) for p in protected[:2]},
              'seed_blocks':{'pilot':[31000000,31000003],'development':[31000100,31000999],
                             'final_core':[31100000,31100039],'final_guard':[31200000,31200007]},
              'missing_historical_baseline':{'commit':'0066a30','branch':'research/secret-hunter-astra-plans',
                    'missing':['docs/secret_hunter_astra_plans/REPORT.md','development/secret_hunter_astra_plans/','engine-trap-v2 code and original paired rows'],
                    'reported_not_reverified':{'Y1_Astra':'176/240','engine-trap-v2_Astra':'188/240','flips':19,'regressions':7},
                    'search':'Checked both Documents and Developer repositories, stable worktree, Spotlight names and remote research refs/main tree.',
                    'replacement':'R0-trap-reference is an independently rebuilt public-model turn reference, NOT engine-trap-v2.'}}
    train.setmeta(db,'manifest',manifest);train.atomic(RUN/'manifest.json',manifest)
    train.setmeta(db,'effective_seconds',time.time()-START);train.setmeta(db,'continuations',0)
    train.setmeta(db,'best','Y1');train.setmeta(db,'mode','explicit_turn_study')
    candidates={'Y1':{'name':'Y1','path':str(Y1.relative_to(ROOT)),'sha256':fingerprint(Y1)}}
    for c in json.loads((HERE/'lineage.json').read_text()):candidates[c['name']]=c
    train.setmeta(db,'candidates',candidates)


def report(db,batch):
    b=db.execute('select * from batches where id=?',(batch,)).fetchone()
    arms=json.loads(b['arms']);rows={a:[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done' order by seed,opponent,seat",(batch,a))] for a in arms}
    complete=not db.execute("select 1 from tasks where batch=? and status!='done' limit 1",(batch,)).fetchone()
    result={'batch':batch,'complete':complete,'arms':{a:summarize(rs) for a,rs in rows.items() if rs},'comparisons':{}}
    if complete and not any(r.get('harness_error') for rs in rows.values() for r in rs):
        for a in arms[1:]:
            comparisons={'all':paired(rows[arms[0]],rows[a])}
            if b['phase']!='final_guard':
                comparisons['primary']=paired(rows[arms[0]],rows[a],groups=['astra','bot2'],equal_groups=True)
                comparisons['astra']=paired(rows[arms[0]],rows[a],groups=['astra'])
            result['comparisons'][a]=comparisons
        for a in arms:
            path=RUN/'batches'/batch/a/'results.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(''.join(json.dumps(r)+'\n' for r in rows[a]))
        with db:db.execute("update batches set status='done' where id=?",(batch,))
    train.atomic(RUN/'batches'/batch/'report.json',result)
    print(json.dumps({'batch':batch,'complete':complete,'wins':{a:[r['all']['wins'],r['all']['n']] for a,r in result['arms'].items()},'comparisons':result['comparisons']}),flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','run','status','report'])
    p.add_argument('--batch');p.add_argument('--arms',nargs='+');p.add_argument('--start',type=int);p.add_argument('--seeds',type=int)
    p.add_argument('--pool',default='core',choices=['core','guardrail']);p.add_argument('--final',action='store_true')
    p.add_argument('--historical-audit',action='store_true')
    p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    if args.command=='status':
        # WAL readers do not need the trainer's exclusive writer lock.
        db=sqlite3.connect(f'file:{RUN}/ledger.sqlite?mode=ro',uri=True)
        db.row_factory=sqlite3.Row
        print(json.dumps(train.status(db,RUN,False),indent=2));return
    RUN.mkdir(parents=True,exist_ok=True)
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=train.connect(RUN);initialize(db)
        if args.command=='status':print(json.dumps(train.status(db,RUN,False),indent=2));return
        if args.command=='init':return
        if args.command=='report':report(db,args.batch);return
        manifest=train.meta(db,'manifest')
        for path,digest in manifest['protected'].items():assert sha(ROOT/path)==digest,path
        for path,versions in manifest['opponents'].items():assert snapshot(json.loads((ROOT/path).read_text()))==versions
        assert time.time()<manifest['deadline'],'Four-hour wall budget exhausted'
        candidates=train.meta(db,'candidates')
        for c in json.loads((HERE/'lineage.json').read_text()):
            if c['name'] in candidates:assert candidates[c['name']]['sha256']==c['sha256']
            candidates[c['name']]=c
        train.setmeta(db,'candidates',candidates)
        if args.final:
            assert (RUN/'final-freeze.json').exists(),'Freeze candidate before opening final seeds'
            freeze=json.loads((RUN/'final-freeze.json').read_text())
            assert args.arms==freeze['arms']
            for a in args.arms:assert candidates[a]['sha256']==freeze['fingerprints'][a]
            block=manifest['seed_blocks']['final_guard' if args.pool=='guardrail' else 'final_core']
            assert block[0]<=args.start and args.start+args.seeds-1<=block[1]
            train.setmeta(db,'final_opened',True)
        elif args.historical_audit:assert 21110000<=args.start and args.start+args.seeds<=21110040
        else:assert 31000000<=args.start and args.start+args.seeds<=31001000
        phase=('final_guard' if args.pool=='guardrail' else 'final_core') if args.final else 'cli_development'
        train.reserve(db,args.batch,phase,args.arms,args.start,args.seeds,args.pool)
        train.reconcile(db);train.setmeta(db,'effective_seconds',time.time()-manifest['created'])
        train.setmeta(db,'pid',os.getpid())
        args.game_timeout_seconds=90;args.cli_game_timeout_seconds=150;args.stop_grace_seconds=5
        signal.signal(signal.SIGTERM,lambda *_:setattr(train,'STOP',True))
        signal.signal(signal.SIGINT,lambda *_:setattr(train,'STOP',True))
        try:
            for arm in args.arms:
                if train.STOP:break
                train.run_arm(db,RUN,args.batch,arm,args)
            report(db,args.batch)
        finally:
            train.setmeta(db,'pid',None);train.status(db,RUN)


if __name__=='__main__':main()
