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
from development.secret_hunter_astra_sprint import ledger as train
from development.secret_hunter_program.common import ROOT, sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
from hs_arena.deck import deck_from_ids

HERE = ROOT/'development/secret_hunter_astra_sprint'
RUN = Path(os.environ.get('HUNTER_SPRINT_RUN', str(ROOT/'runs/astra-sprint-20261114'))).resolve()
BASE_SHA = 'e0cf461721004b82ab70cd128fbdd99ab2d59bb8e6c561d11449f8ea06d3b6c4'
DECK_SHA = 'af78480d96fd2fc11b77f0ca8f17c5703a6bda5934c2041622f762ca0128b7d1'
ZIP_SHA = '0130813f56655e7b802e2cbbe539526f6ab2a1a8f1acf4d27af6e5fdee5a9a0e'
ANCHOR = '8c158c07280788d7b7872476dd728ba43e3e71ca'

def deck_check(source):
    base=json.loads((HERE/'candidates/DARCL2/deck.json').read_text())
    deck=json.loads((source/'deck.json').read_text())
    assert deck['hero_class']=='HUNTER' and len(deck['cards'])==30
    deck_from_ids(deck['hero_class'],deck['cards'])
    old,new=Counter(base['cards']),Counter(deck['cards'])
    removed=list((old-new).elements());added=list((new-old).elements())
    assert len(removed)==len(added)<=1, (removed,added)
    changes=[{'slot':i,'removed':a,'added':b} for i,(a,b) in enumerate(zip(base['cards'],deck['cards'])) if a!=b]
    # New cards occupy replaced slots; no shifts or reorder of retained cards.
    assert len(changes)==len(removed)
    assert Counter(x['removed'] for x in changes)==Counter(removed)
    assert Counter(x['added'] for x in changes)==Counter(added)
    for cid in ('EX1_610','EX1_611','EX1_554','EX1_533','EX1_536','NEW1_019','EX1_538','EX1_531'):
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
    start_record=json.loads((RUN/'start.json').read_text());start=start_record['started_utc']
    m={'created':start,'deadline':start_record['deadline'],'candidate_generation_deadline':start_record['deadline']-10800,
       'base_commit':ANCHOR,'baseline':'DARCL2','git_start':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
       'limits':{'seconds':36000,'full_games':18000,'continuations':16000},'reserved_final_games':5000,
       'engine_version':importlib.metadata.version('hs-arena'),
       'versions':{n:importlib.metadata.version(n) for n in ('hs-arena','hearthstone','hearthstone-data')},
       'engine':engine,'protected':{p:sha(ROOT/p) for p in protected},
       'opponents':{p:snapshot(json.loads((ROOT/p).read_text())) for p in protected[:2]},
       'seed_blocks':{'pilot':[62140000,62140099],'development':[62150000,62159999],
                      'label_holdout':[62160000,62169999],'conditional':[62170000,62179999],
                      'selection':[62250000,62250079],'selection_guard':[62251000,62251007],
                      'final_core':[62350000,62350169],'final_guard':[62450000,62450015],
                      'auxiliary':[62550000,62550099]},
       'promotion':{'primary':'equal mean of the three Astra proxy win rates','gain_min':.02,
          'one_sided_90_lower_gt':0,'two_sided_95_reported':True,'astra_nonnegative_proxies_min':2,
          'bot1_regression_limit':.02,'bot2_regression_limit':.03,'guard_regression_limit':.02,
          'reliability':'zero illegal/timeout/unexpected fallback/exit/policy/opponent/harness error; full CLI <=2 seconds',
          'default':'Exact original DARCL2 ZIP if any gate fails or final sample incomplete'},
       'selection_rule':'DARCL2 plus at most two candidates; highest reliable Astra macro, tie within 0.5pp resolved by paired balanced 6/4/4 expected positive score above 10; then fewer edits then stable name. No selection tuning.',
       'final_target':{'per_arm_core':2040,'per_arm_guard':448,'seeds_core':170,'seeds_guard':16},
       'capacity_rule':'Before selection opens, choose 170 core groups if measured CLI time plus 45 minute packaging/protocol margin fits original deadline, else 100 if it fits; otherwise baseline acceptance only. Never adapt to final outcomes.',
       'source_partition':'Development and label holdout use disjoint registered blocks; every opponent, seat, root and world for one seed stays in that block.',
       'scope':'Existing course 0.2.2 proxies only. Historical sources and seeds are seen. No formal Slack submission.',
       'generation_policy':'Only Codex evidence review proposes new source; unattended loops execute fixed commands only.'}
    assert m['engine_version']=='0.2.2'
    train.atomic(RUN/'manifest.json',m);train.setmeta(db,'manifest',m)
    for k,v in {'effective_seconds':0,'continuations':0,'candidates':{},'best':'DARCL2','mode':'astra_sprint'}.items():train.setmeta(db,k,v)

def register(db):
    cs=train.meta(db,'candidates',{})
    for p in sorted((HERE/'candidates').iterdir()):
        if not p.is_dir():continue
        item={'name':p.name,'path':str(p.relative_to(ROOT)),'sha256':fingerprint(p),**deck_check(p)}
        if p.name in cs:
            assert {k:v for k,v in item.items() if k!='path'}=={k:v for k,v in cs[p.name].items() if k!='path'}, ('immutable candidate changed',p.name)
            assert fingerprint(ROOT/cs[p.name]['path'])==item['sha256']
        else:cs[p.name]=item
    assert cs['DARCL2']['sha256']==BASE_SHA and cs['DARCL2']['deck_sha256']==DECK_SHA
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
            assert a.arms and a.arms[0]=='DARCL2' and 1<=len(a.arms)<=2
            selection=json.loads((RUN/'selection-decision.json').read_text())
            assert a.arms==(['DARCL2',selection['challenger']] if selection['challenger']!='DARCL2' else ['DARCL2'])
            assert all(cs[x]['sha256']==selection['fingerprints'][x] for x in a.arms)
            f={'created':time.time(),'arms':a.arms,'fingerprints':{x:cs[x]['sha256'] for x in a.arms},
               'promotion':m['promotion'],'seeds':{k:v for k,v in m['seed_blocks'].items() if k.startswith('final')},
               'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
            releases=json.loads((RUN/'release-candidates.json').read_text())
            assert [r['name'] for r in releases]==a.arms
            assert all(sha(ROOT/r['path'])==r['zip_sha256'] and fingerprint(ROOT/r['extracted'])==f['fingerprints'][r['name']] for r in releases)
            f.update(release_records=releases,release_records_sha256=sha(RUN/'release-candidates.json'),
                     manifest_sha256=sha(RUN/'manifest.json'),engine_versions=m['versions'],
                     engine_source_files=m['engine'],opponents=m['opponents'],
                     final_target=m['final_target'],outcome_access='Read neither pool until BOTH final pools finish')
            assert not (RUN/'final-freeze.json').exists();train.atomic(RUN/'final-freeze.json',f);return
        if a.command=='report':
            from development.secret_hunter_astra_sprint.statistics import analyze
            analyze(db,RUN,a.batch);return
        assert time.time()<m['deadline']
        if a.final:
            f=json.loads((RUN/'final-freeze.json').read_text());assert a.arms==f['arms']
            assert all(cs[x]['sha256']==f['fingerprints'][x] for x in a.arms)
            assert sha(RUN/'release-candidates.json')==f['release_records_sha256']
            assert sha(RUN/'manifest.json')==f['manifest_sha256']
            assert all(sha(ROOT/r['path'])==r['zip_sha256'] and cs[r['name']]['path']==r['extracted'] for r in f['release_records'])
            lo,hi=f['seeds']['final_guard' if a.pool=='guardrail' else 'final_core']
            assert lo<=a.start and a.start+a.seeds-1<=hi and not a.warm
            train.setmeta(db,'final_opened',True)
        else:
            assert not train.meta(db,'final_opened',False),'No changes or new development after final opening'
            assert a.selection_stage or not train.meta(db,'selection_opened',False),'Selection opened: no further development or retuning'
            assert time.time()<m['candidate_generation_deadline']
            allowed=['selection','selection_guard'] if a.selection_stage else ['pilot','development','label_holdout','conditional']
            assert any(m['seed_blocks'][k][0]<=a.start and a.start+a.seeds-1<=m['seed_blocks'][k][1] for k in allowed)
        if a.selection_stage:assert not a.warm,'Selection is complete CLI'
        if a.selection_stage:
            plan=json.loads((RUN/'selection-plan.json').read_text())
            block=plan['guardrail' if a.pool=='guardrail' else 'core']
            assert a.arms==plan['arms'] and a.batch==block['batch'] and a.start==block['start'] and a.seeds==block['seeds']
            assert not train.meta(db,'cf_pid'),'Finish or explicitly stop active label workers before selection'
            selection_freeze={'arms':a.arms,'fingerprints':{x:cs[x]['sha256'] for x in a.arms},'plan':plan}
            path=RUN/'selection-freeze.json'
            if path.exists():assert json.loads(path.read_text())==selection_freeze
            else:train.atomic(path,selection_freeze)
            train.setmeta(db,'selection_opened',True)
        # The inherited selection analyzer assumes Astra/Bot2 core families.
        # Guardrail has different families; retain CLI execution and select only
        # after both independently reserved selection reports are complete.
        phase=('final_guard' if a.pool=='guardrail' else 'final_core') if a.final else ('selection' if a.selection_stage and a.pool=='core' and len(a.arms)>1 else ('development' if a.warm else 'cli_development'))
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
        from development.secret_hunter_astra_sprint.provenance import archive_code
        control=archive_code(RUN,['development/secret_hunter_astra_sprint/study.py','development/secret_hunter_astra_sprint/ledger.py',
            'development/secret_hunter_mcgs/cli_match.py','development/teacher_eval/run.py','development/secret_hunter_tactics/run.py'])
        train.atomic(RUN/'batches'/a.batch/'control-starts'/f'{time.time_ns()}.json',
            {'created':time.time(),'harness_sha256':control,'arms':a.arms,'workers':a.workers,'warm':a.warm,'phase':phase})
        train.setmeta(db,'effective_seconds',time.time()-m['created']);train.setmeta(db,'pid',os.getpid())
        a.game_timeout_seconds=90;a.cli_game_timeout_seconds=150;a.stop_grace_seconds=5
        signal.signal(signal.SIGTERM,lambda *_:setattr(train,'STOP',True))
        signal.signal(signal.SIGINT,lambda *_:setattr(train,'STOP',True))
        try:
            for arm in a.arms:
                if train.STOP:break
                train.run_arm(db,RUN,a.batch,arm,a)
            if a.final:
                remaining=db.execute("select count(*) from tasks where batch=? and status!='done'",(a.batch,)).fetchone()[0]
                if not remaining:
                    with db:db.execute("update batches set status='done' where id=?",(a.batch,))
            elif not a.selection:
                from development.secret_hunter_astra_sprint.statistics import analyze
                analyze(db,RUN,a.batch)
                train.setmeta(db,'archive',[x for x in train.meta(db,'archive',[]) if x in cs])
            else:
                from development.secret_hunter_final.statistics import selected_report
                selected_report(db,RUN,a.batch,a.selection)
        finally:
            train.setmeta(db,'pid',None);train.status(db,RUN)

if __name__=='__main__':main()
