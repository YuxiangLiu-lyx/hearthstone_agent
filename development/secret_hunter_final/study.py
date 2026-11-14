"""Reuse the audited process supervisor and attempt ledger with a fresh budget."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import time
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import ROOT, sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot

HERE = ROOT/'development/secret_hunter_final'
RUN = Path(os.environ.get('KRUSH_FINAL_RUN',str(ROOT/'runs/final-20261113'))).resolve()
BASE_SHA = 'ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9'
DECK_SHA = '54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4'

def initialize(db):
    if train.meta(db, 'manifest'): return
    protected=['development/teacher_eval/core.json','development/teacher_eval/guardrail.json',
               'development/teacher_eval/run.py','development/secret_hunter_tactics/run.py',
               'development/teacher_eval/compare.py','development/opponents/population.py',
               'development/opponents/search.py','development/benchmarks/run.py']
    import hs_arena
    engine_root=Path(hs_arena.__file__).parent
    engine={str(p):sha(p) for p in sorted(engine_root.rglob('*.py'))}
    start=time.time()
    m={'created':start,'deadline':start+21600,'candidate_generation_deadline':start+14400,
       'base_commit':'5c02d4870a86e2915095ec66d6afab60510afa50',
       'limits':{'seconds':21600,'full_games':6000,'continuations':6000},
       'reserved_final_games':1408,'engine_version':importlib.metadata.version('hs-arena'),
       'engine':engine,'protected':{p:sha(ROOT/p) for p in protected},
       'opponents':{p:snapshot(json.loads((ROOT/p).read_text())) for p in protected[:2]},
       'seed_blocks':{'pilot':[41300000,41300009],'development':[41301000,41309999],
                      'conditional':[41310000,41329999],'final_core':[41400000,41400039],
                      'final_guard':[41500000,41500007]},
       'promotion':{'primary':'equal Astra/Bot2 family win rate, seed-cluster paired',
                    'statistical_route':'positive primary gain, 95% cluster lower bound > 0',
                    'correction_route':'proved narrow lethal correction, no observed final regression in any family or guard; do not claim population gain',
                    'family_regression_limit_pp':2.5,'guard_regression_limit_pp':2,
                    'reliability':'zero illegal, timeouts, unexpected fallback or execution errors; complete CLI <= 2s',
                    'default':'engine-trap-v2 if evidence insufficient'},
       'grouping':'All opponents, seats, adjacent states and futures share source-seed partition.',
       'scope':'Frozen local proxies only. Formal C2 score 10 is separate.'}
    assert m['engine_version']=='0.2.2'
    train.atomic(RUN/'manifest.json',m);train.setmeta(db,'manifest',m)
    train.setmeta(db,'effective_seconds',0);train.setmeta(db,'continuations',0)
    train.setmeta(db,'candidates',{});train.setmeta(db,'best','B');train.setmeta(db,'mode','final_research')

def register(db):
    cs=train.meta(db,'candidates',{})
    for p in sorted((HERE/'candidates').iterdir()):
        if not p.is_dir():continue
        assert sha(p/'deck.json')==DECK_SHA
        item={'name':p.name,'path':str(p.relative_to(ROOT)),'sha256':fingerprint(p)}
        if p.name in cs:
            assert item['sha256']==cs[p.name]['sha256'], ('immutable candidate changed',p.name)
            assert fingerprint(ROOT/cs[p.name]['path'])==item['sha256']
        else:cs[p.name]=item
    train.setmeta(db,'candidates',cs)
    train.atomic(RUN/'candidates.json',cs)
    return cs

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','run','status','freeze','report'])
    p.add_argument('--batch');p.add_argument('--arms',nargs='+');p.add_argument('--start',type=int);p.add_argument('--seeds',type=int)
    p.add_argument('--pool',default='core',choices=['core','guardrail']);p.add_argument('--workers',type=int,default=2)
    p.add_argument('--final',action='store_true');p.add_argument('--warm',action='store_true')
    p.add_argument('--selection',type=Path,help='Frozen list of opponent/seed/seat keys; historical or conditional only')
    a=p.parse_args()
    RUN.mkdir(parents=True,exist_ok=True)
    if a.command=='status':
        db=train.connect(RUN);print(json.dumps(train.status(db,RUN,False),indent=2));return
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=train.connect(RUN);initialize(db);cs=register(db);m=train.meta(db,'manifest')
        from development.secret_hunter_final.integrity import check
        check()
        assert all(sha(ROOT/p)==s for p,s in m['protected'].items())
        assert all(sha(Path(p))==s for p,s in m['engine'].items())
        assert all(snapshot(json.loads((ROOT/p).read_text()))==v for p,v in m['opponents'].items())
        if a.command=='init':return
        if a.command=='freeze':
            assert not train.meta(db,'final_opened',False)
            assert a.arms and len(a.arms)==2 and a.arms[0]=='B'
            final_seeds={k:v for k,v in m['seed_blocks'].items() if k.startswith('final')}
            amendment=RUN/'final-plan-amendment.json'
            if amendment.exists():
                updated=json.loads(amendment.read_text());assert updated['promotion_unchanged']==m['promotion']
                final_seeds=updated['seeds']
            f={'created':time.time(),'arms':a.arms,'fingerprints':{x:cs[x]['sha256'] for x in a.arms},
               'promotion':m['promotion'],'seeds':{k:v for k,v in m['seed_blocks'].items() if k.startswith('final')}}
            f['seeds']=final_seeds;f['preopening_plan_amendment_sha256']=sha(amendment) if amendment.exists() else None
            path=RUN/'final-freeze.json';assert not path.exists()
            train.atomic(path,f);return
        if a.command=='report':train.analyze(db,RUN,a.batch);return
        assert time.time()<m['deadline']
        if a.final:
            f=json.loads((RUN/'final-freeze.json').read_text());assert a.arms==f['arms']
            assert all(cs[x]['sha256']==f['fingerprints'][x] for x in a.arms)
            lo,hi=f['seeds']['final_guard' if a.pool=='guardrail' else 'final_core']
            assert lo<=a.start and a.start+a.seeds-1<=hi
            assert not a.warm
            train.setmeta(db,'final_opened',True)
        else:
            assert not train.meta(db,'final_opened',False),'No adaptation after final opening'
            assert time.time()<m['candidate_generation_deadline']
            assert (41300000<=a.start and a.start+a.seeds<=41330000) or (a.selection and a.start in (21110024,21110037))
        phase=('final_guard' if a.pool=='guardrail' else 'final_core') if a.final else ('development' if a.warm else 'cli_development')
        existing=db.execute('select * from batches where id=?',(a.batch,)).fetchone()
        if existing:
            assert json.loads(existing['arms'])==a.arms and existing['start']==a.start and existing['seeds']==a.seeds and existing['phase']==phase
        if a.selection:
            assert not a.final
            selected=json.loads(a.selection.read_text());key='selection_'+a.batch
            if existing:assert train.meta(db,key)==selected
            else:
                pop={o['name']:o for o in json.loads((ROOT/f'development/teacher_eval/{a.pool}.json').read_text())}
                assert len({tuple(x) for x in selected})==len(selected)
                with db:
                    db.execute('insert into batches values (?,?,?,?,?,?)',(a.batch,phase,json.dumps(a.arms),a.start,a.seeds,'pending'))
                    for name,seed,seat in selected:
                        assert a.start<=seed<a.start+a.seeds and seat in (1,2)
                        for arm in a.arms:
                            taskkey=json.dumps([arm,phase,name,seed,seat],separators=(',',':'))
                            db.execute('insert into tasks values (?,?,?,?,?,?,?,?,NULL)',
                                       (taskkey,a.batch,arm,phase,json.dumps(pop[name]),seed,seat,'pending'))
                train.setmeta(db,key,selected)
        else:train.reserve(db,a.batch,phase,a.arms,a.start,a.seeds,a.pool)
        train.reconcile(db)
        train.setmeta(db,'effective_seconds',time.time()-m['created']);train.setmeta(db,'pid',os.getpid())
        a.game_timeout_seconds=90;a.cli_game_timeout_seconds=150;a.stop_grace_seconds=5
        signal.signal(signal.SIGTERM,lambda *_:setattr(train,'STOP',True))
        signal.signal(signal.SIGINT,lambda *_:setattr(train,'STOP',True))
        try:
            for arm in a.arms:
                if train.STOP:break
                train.run_arm(db,RUN,a.batch,arm,a)
            if a.selection:
                from development.secret_hunter_final.statistics import selected_report
                selected_report(db,RUN,a.batch,a.selection)
            else:train.analyze(db,RUN,a.batch)
        finally:
            train.setmeta(db,'pid',None);train.status(db,RUN)

if __name__=='__main__':main()
