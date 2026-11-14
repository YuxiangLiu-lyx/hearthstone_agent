"""Fresh experiment namespace; preserve every old validator, ledger and candidate."""
import argparse
from collections import Counter
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import ROOT, sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
from hs_arena.deck import deck_from_ids

HERE = ROOT/'development/secret_hunter_long'
RUN = Path(os.environ.get('HUNTER_LONG_RUN', str(ROOT/'runs/long-20261114'))).resolve()
BASE_SHA = 'ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9'
DECK_SHA = '54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4'
ZIP_SHA = '6b20fe6572857413fcc87b9134d94eb06340fa4be6f62578ac8354a58a9a067b'
ANCHOR = 'd07a9017d0178b70f4b2f99a32d921afb60e2397'

def deck_check(source):
    base=json.loads((HERE/'candidates/B/deck.json').read_text())
    deck=json.loads((source/'deck.json').read_text())
    assert deck['hero_class']=='HUNTER' and len(deck['cards'])==30
    deck_from_ids(deck['hero_class'],deck['cards'])
    old,new=Counter(base['cards']),Counter(deck['cards'])
    removed=list((old-new).elements());added=list((new-old).elements())
    assert len(removed)==len(added)<=2, (removed,added)
    changes=[{'slot':i,'removed':a,'added':b} for i,(a,b) in enumerate(zip(base['cards'],deck['cards'])) if a!=b]
    # New cards occupy replaced slots; no shifts or reorder of retained cards.
    assert len(changes)==len(removed)
    assert Counter(x['removed'] for x in changes)==Counter(removed)
    assert Counter(x['added'] for x in changes)==Counter(added)
    for cid in ('EX1_610','EX1_611','EX1_536','NEW1_019','EX1_538','EX1_531'):
        assert new[cid]==old[cid], ('protected core',cid)
    return {'ordered_cards':deck['cards'],'hero_class':'HUNTER','deck_sha256':sha(source/'deck.json'),
            'changes':changes,'replacements':len(removed),'retained':30-len(removed),
            'krush_line':bool(new['EX1_543'])}

def initialize(db):
    if train.meta(db,'manifest'):return
    import hs_arena
    protected=['development/teacher_eval/core.json','development/teacher_eval/guardrail.json',
      'development/teacher_eval/run.py','development/teacher_eval/compare.py',
      'development/secret_hunter_tactics/run.py','development/opponents/population.py',
      'development/opponents/search.py','development/benchmarks/run.py',
      'development/secret_hunter_dgm/deck_guard.py','development/secret_hunter_final/study.py']
    engine_root=Path(hs_arena.__file__).parent
    # Entire installed course source + resource files, before the first new match.
    engine={str(p):sha(p) for p in sorted(engine_root.rglob('*')) if p.is_file() and p.suffix in ('.py','.json','.xml','.txt')}
    start=time.time()
    m={'created':start,'deadline':start+43200,'candidate_generation_deadline':start+30600,
       'base_commit':ANCHOR,'git_start':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
       'limits':{'seconds':43200,'full_games':20000,'continuations':24000},
       'reserved_final_games':5000,'engine_version':importlib.metadata.version('hs-arena'),
       'versions':{n:importlib.metadata.version(n) for n in ('hs-arena','hearthstone','hearthstone-data')},
       'engine':engine,'protected':{p:sha(ROOT/p) for p in protected},
       'opponents':{p:snapshot(json.loads((ROOT/p).read_text())) for p in protected[:2]},
       'seed_blocks':{'pilot':[51400000,51400099],'development':[51401000,51419999],
                      'conditional':[51420000,51439999],'selection':[51500000,51500099],
                      'selection_guard':[51501000,51501007],
                      'final_core':[51600000,51600099],'final_guard':[51700000,51700015]},
       'promotion':{'primary':'equal Astra/Bot2 family paired terminal win rate',
          'statistical_route':'primary 95% whole-source-seed bootstrap lower bound strictly positive',
          'family_regression_limit_pp':2.5,'guard_regression_limit_pp':2,
          'correction_route':'L2 alone only: proved narrow lethal repair and no observed regression in any core family or guard',
          'reliability':'zero illegal/timeout/unexpected fallback/exit/policy/opponent/harness error; full CLI <=2 seconds',
          'default':'B if no challenger passes'},
       'selection_rule':'one challenger, maximum equal-family Astra/Bot2 terminal rate among reliability-passing candidates; no validation tuning',
       'final_target':{'per_arm_core':1200,'per_arm_guard':448,'seeds_core':100,'seeds_guard':16},
       'source_partition':'All opponents, seats, adjacent states and alternate futures share source seed partition. Label train/holdout uses seed mod 5 (0,1 held out).',
       'scope':'Frozen local proxies. Formal C2 double-Arcane results must be distinguished from original Krush deck.',
       'generation_policy':'Unattended loops only run recorded candidates; code proposals require an actual Codex review of saved evidence.'}
    assert m['engine_version']=='0.2.2'
    train.atomic(RUN/'manifest.json',m);train.setmeta(db,'manifest',m)
    for k,v in {'effective_seconds':0,'continuations':0,'candidates':{},'best':'B','mode':'long_research'}.items():train.setmeta(db,k,v)

def register(db):
    cs=train.meta(db,'candidates',{})
    for p in sorted((HERE/'candidates').iterdir()):
        if not p.is_dir():continue
        item={'name':p.name,'path':str(p.relative_to(ROOT)),'sha256':fingerprint(p),**deck_check(p)}
        if p.name in cs:
            assert {k:v for k,v in item.items() if k!='path'}=={k:v for k,v in cs[p.name].items() if k!='path'}, ('immutable candidate changed',p.name)
            assert fingerprint(ROOT/cs[p.name]['path'])==item['sha256']
        else:cs[p.name]=item
    assert cs['B']['sha256']==BASE_SHA and cs['B']['deck_sha256']==DECK_SHA
    train.setmeta(db,'candidates',cs);train.atomic(RUN/'candidates.json',cs)
    return cs

def check(m):
    assert all(sha(ROOT/p)==h for p,h in m['protected'].items())
    assert all(sha(Path(p))==h for p,h in m['engine'].items())
    assert all(snapshot(json.loads((ROOT/p).read_text()))==v for p,v in m['opponents'].items())
    assert all(importlib.metadata.version(k)==v for k,v in m['versions'].items())

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','run','status','freeze','report'])
    p.add_argument('--batch');p.add_argument('--arms',nargs='+');p.add_argument('--start',type=int);p.add_argument('--seeds',type=int)
    p.add_argument('--pool',default='core',choices=['core','guardrail']);p.add_argument('--workers',type=int,default=3)
    p.add_argument('--final',action='store_true');p.add_argument('--selection-stage',action='store_true');p.add_argument('--warm',action='store_true')
    p.add_argument('--selection',type=Path)
    a=p.parse_args();RUN.mkdir(parents=True,exist_ok=True)
    if a.command=='status':
        db=train.connect(RUN);print(json.dumps(train.status(db,RUN,False),indent=2));return
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=train.connect(RUN);initialize(db);cs=register(db);m=train.meta(db,'manifest');check(m)
        if a.command=='init':return
        if a.command=='freeze':
            assert not train.meta(db,'final_opened',False)
            assert a.arms and a.arms[0]=='B' and 1<=len(a.arms)<=2
            f={'created':time.time(),'arms':a.arms,'fingerprints':{x:cs[x]['sha256'] for x in a.arms},
               'promotion':m['promotion'],'seeds':{k:v for k,v in m['seed_blocks'].items() if k.startswith('final')},
               'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
            assert not (RUN/'final-freeze.json').exists();train.atomic(RUN/'final-freeze.json',f);return
        if a.command=='report':train.analyze(db,RUN,a.batch);return
        assert time.time()<m['deadline']
        if a.final:
            f=json.loads((RUN/'final-freeze.json').read_text());assert a.arms==f['arms']
            assert all(cs[x]['sha256']==f['fingerprints'][x] for x in a.arms)
            lo,hi=f['seeds']['final_guard' if a.pool=='guardrail' else 'final_core']
            assert lo<=a.start and a.start+a.seeds-1<=hi and not a.warm
            train.setmeta(db,'final_opened',True)
        else:
            assert not train.meta(db,'final_opened',False),'No changes or new development after final opening'
            assert time.time()<m['candidate_generation_deadline']
            allowed=['selection','selection_guard'] if a.selection_stage else ['pilot','development','conditional']
            assert any(m['seed_blocks'][k][0]<=a.start and a.start+a.seeds-1<=m['seed_blocks'][k][1] for k in allowed)
        phase=('final_guard' if a.pool=='guardrail' else 'final_core') if a.final else ('selection' if a.selection_stage else ('development' if a.warm else 'cli_development'))
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
                            db.execute('insert into tasks values (?,?,?,?,?,?,?,?,NULL)',(taskkey,a.batch,arm,phase,json.dumps(pop[name]),seed,seat,'pending'))
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
            if not a.selection:train.analyze(db,RUN,a.batch)
            else:
                from development.secret_hunter_final.statistics import selected_report
                selected_report(db,RUN,a.batch,a.selection)
        finally:
            train.setmeta(db,'pid',None);train.status(db,RUN)

if __name__=='__main__':main()
