"""Durable paired experiments; all launched attempts consume budget, including failures."""
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
from development.secret_hunter_program.common import ROOT, sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import worker as play, summarize, snapshot
from development.teacher_eval.compare import paired
from development.secret_hunter_mcgs.build import build, Y1, HERE
from development.secret_hunter_dgm.deck_guard import check

STOP=False

def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:
        json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    temp.replace(path)

def worker(task,result_path,full_cli=False):
    if full_cli:
        from development.secret_hunter_mcgs.cli_match import worker as cli_play
        row=cli_play(task)
    else:
        row=play(task);row['execution']='warm_python'
    atomic(result_path,row);return row

def connect(run):
    run.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(run/'ledger.sqlite');db.row_factory=sqlite3.Row
    db.executescript('''PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,phase TEXT,arms TEXT,start INTEGER,seeds INTEGER,status TEXT);
    CREATE TABLE IF NOT EXISTS tasks(key TEXT PRIMARY KEY,batch TEXT,candidate TEXT,phase TEXT,opponent TEXT,seed INTEGER,seat INTEGER,status TEXT,result TEXT);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,task TEXT,status TEXT,started REAL,finished REAL,result_path TEXT);
    ''');db.commit();return db

def meta(db,key,default=None):
    r=db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
    return json.loads(r[0]) if r else default

def setmeta(db,key,value):
    db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',(key,json.dumps(value)));db.commit()

def initialize(db,run,args):
    if meta(db,'manifest'):
        manifest=meta(db,'manifest')
        for path,digest in manifest['protected'].items():assert sha(ROOT/path)==digest,path
        for p,versions in manifest['opponents'].items():assert snapshot(json.loads((ROOT/p).read_text()))==versions
        return
    check(Y1)
    protected=['development/teacher_eval/core.json','development/teacher_eval/guardrail.json',
               'development/teacher_eval/run.py','development/secret_hunter_tactics/run.py',
               'development/teacher_eval/compare.py','development/opponents/population.py',
               'development/opponents/search.py','docs/secret_hunter_face_validation/checkpoint.json',
               'docs/secret_hunter_winrate/checkpoint.json']
    manifest={'created':time.time(),'base_commit':'5afec0f074e56145723f544e23aba062f4be14e3',
        'protected':{p:sha(ROOT/p) for p in protected},
        'opponents':{p:snapshot(json.loads((ROOT/p).read_text())) for p in protected[:2]},
        'limits':{'seconds':args.hours*3600,'full_games':args.max_full_games,'continuations':args.max_continuations},
        'workers':args.workers,'reserved_final_games':3040,
        'seed_blocks':{'development':[10000000,10049999],'selection':[10050000,10059999],
                       'final_core':[10100000,10100079],'final_guard':[10200000,10200019]},
        'promotion':{'primary_gain_min':.01,'primary_ci_lower_gt':0,'goal':.03,
                     'family_regression_limit':.025,'guard_regression_limit':.02,
                     'illegal':0,'timeouts':0,'cli_max_s':2.},
        'scope':'Fixed original ordered deck; local proxies only. Historical seeds remain known/development.'}
    assert manifest['limits']['full_games']>=manifest['reserved_final_games']+200
    setmeta(db,'manifest',manifest);setmeta(db,'effective_seconds',0);setmeta(db,'continuations',0)
    setmeta(db,'next_experiment','Diagnose fresh loss trajectories; no unattended structural code edits.')
    atomic(run/'manifest.json',manifest)
    candidates={'Y1':{'path':str(Y1.relative_to(ROOT)),'sha256':fingerprint(Y1),'parent':None}}
    for filename in ('lineage.json','structural-lineage.json','particle-lineage.json','identity-lineage.json','confidence-lineage.json'):
        for item in json.loads((HERE/filename).read_text()):candidates[item['name']]=item
    setmeta(db,'candidates',candidates);setmeta(db,'best','Y1')
    setmeta(db,'archive',['Y1','M5-uct','M5-fixed','M5-dpw'])

def reserve(db,batch,phase,arms,start,seeds,pool='core'):
    if db.execute('SELECT 1 FROM batches WHERE id=?',(batch,)).fetchone():return
    population=json.loads((ROOT/f'development/teacher_eval/{pool}.json').read_text())
    overlap=db.execute('SELECT id FROM batches WHERE start < ? AND start+seeds > ?', (start+seeds,start)).fetchall()
    assert not overlap,('seed block already reserved',overlap)
    with db:
        db.execute('INSERT INTO batches VALUES (?,?,?,?,?,?)',(batch,phase,json.dumps(arms),start,seeds,'pending'))
        for arm in arms:
            for o in population:
                for seed in range(start,start+seeds):
                    for seat in (1,2):
                        key=json.dumps([arm,phase,o['name'],seed,seat],separators=(',',':'))
                        db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,NULL)',
                                   (key,batch,arm,phase,json.dumps(o),seed,seat,'pending'))

def reconcile(db):
    recovered=0
    for a in db.execute("SELECT * FROM attempts WHERE status='running'").fetchall():
        path=Path(a['result_path'])
        with db:
            if path.exists():
                row=json.loads(path.read_text())
                db.execute("UPDATE tasks SET status='done',result=? WHERE key=?",(json.dumps(row),a['task']))
                db.execute("UPDATE attempts SET status='done',finished=? WHERE id=?",(time.time(),a['id']));recovered+=1
            else:
                db.execute("UPDATE attempts SET status='interrupted',finished=? WHERE id=?",(time.time(),a['id']))
                db.execute("UPDATE tasks SET status='pending' WHERE key=?",(a['task'],))
    return recovered

def status(db,run,persist=True):
    batches=[dict(r) for r in db.execute('SELECT * FROM batches ORDER BY start')]
    for b in batches:
        b['progress']={r[0]:r[1] for r in db.execute('SELECT status,count(*) FROM tasks WHERE batch=? GROUP BY status',(b['id'],))}
        b['arms']=json.loads(b['arms'])
    data={'pid':meta(db,'pid'),'mode':meta(db,'mode'),'effective_seconds':meta(db,'effective_seconds',0),
          'attempts':db.execute('SELECT count(*) FROM attempts').fetchone()[0],
          'attempt_status':{r[0]:r[1] for r in db.execute('SELECT status,count(*) FROM attempts GROUP BY status')},
          'completed':db.execute("SELECT count(*) FROM tasks WHERE status='done'").fetchone()[0],
          'continuations':meta(db,'continuations',0),'best':meta(db,'best'),'archive':meta(db,'archive'),
          'next_experiment':meta(db,'next_experiment'),'batches':batches,
          'final_opened':meta(db,'final_opened',False),'promotion':meta(db,'promotion','not evaluated'),
          'autonomy':'Automatic configuration experiments; structural changes require a recorded code revision.'}
    if persist:atomic(run/'checkpoint.json',data)
    return data

def run_arm(db,run,batch,arm,args):
    candidate=meta(db,'candidates')[arm];src=ROOT/candidate['path']
    assert fingerprint(src)==candidate['sha256'],('candidate changed',arm)
    tasks=db.execute("SELECT * FROM tasks WHERE batch=? AND candidate=? AND status='pending' ORDER BY seed,opponent,seat",(batch,arm)).fetchall()
    # Fresh pool per arm prevents same-named Python modules crossing candidates.
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        active={};index=0;last=time.monotonic()
        while active or (index<len(tasks) and not STOP):
            limits=meta(db,'manifest')['limits'];seconds=meta(db,'effective_seconds',0)
            attempts=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
            reserved=0 if meta(db,'final_opened',False) else meta(db,'manifest')['reserved_final_games']
            while index<len(tasks) and len(active)<args.workers and not STOP:
                if attempts>=limits['full_games']-reserved or seconds>=limits['seconds'] or meta(db,'continuations',0)>=limits['continuations']:break
                task=tasks[index];index+=1
                with db:
                    cursor=db.execute('INSERT INTO attempts(task,status,started) VALUES (?,?,?)',(task['key'],'running',time.time()))
                    aid=cursor.lastrowid;result_path=run/'attempts'/f'{aid:06d}.json'
                    db.execute('UPDATE attempts SET result_path=? WHERE id=?',(str(result_path.resolve()),aid))
                    db.execute("UPDATE tasks SET status='running' WHERE key=?",(task['key'],))
                job=(str(src),json.loads(task['opponent']),task['seed'],task['seat'],str(run/'batches'/batch/arm),'python')
                full_cli=task['phase'] in ('cli_development','selection','final_core','final_guard')
                active[pool.submit(worker,job,str(result_path),full_cli)]=(aid,task);attempts+=1
            if not active:break
            done,_=wait(active,timeout=5,return_when=FIRST_COMPLETED)
            for f in done:
                aid,task=active.pop(f)
                try:row=f.result()
                except Exception as exc:row={'harness_error':repr(exc),'score':0,'seed':task['seed'],'seat':task['seat'],'opponent':json.loads(task['opponent'])['name']}
                with db:
                    db.execute("UPDATE attempts SET status='done',finished=? WHERE id=?",(time.time(),aid))
                    db.execute("UPDATE tasks SET status='done',result=? WHERE key=?",(json.dumps(row),task['key']))
                print(json.dumps({'batch':batch,'arm':arm,'attempt':aid,'score':row['score'],'error':row.get('harness_error'),'wall_s':row.get('wall_s')}),flush=True)
            now=time.monotonic();setmeta(db,'effective_seconds',meta(db,'effective_seconds',0)+now-last);last=now
            status(db,run)
    assert fingerprint(src)==candidate['sha256']

def analyze(db,run,batch):
    b=db.execute('SELECT * FROM batches WHERE id=?',(batch,)).fetchone()
    if db.execute("SELECT count(*) FROM tasks WHERE batch=? AND status!='done'",(batch,)).fetchone()[0]:return False
    arms=json.loads(b['arms']);rows={a:[json.loads(r[0]) for r in db.execute('SELECT result FROM tasks WHERE batch=? AND candidate=? ORDER BY seed,opponent,seat',(batch,a))] for a in arms}
    report={'batch':batch,'phase':b['phase'],'start':b['start'],'seed_groups':b['seeds'],'arms':{},'comparisons':{}}
    for a,rs in rows.items():
        report['arms'][a]=summarize(rs);out=run/'batches'/batch/a;out.mkdir(parents=True,exist_ok=True)
        (out/'results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rs))
    if not any(r.get('harness_error') for rs in rows.values() for r in rs):
        for a in arms[1:]:
            report['comparisons'][a]={'all':paired(rows[arms[0]],rows[a]),
                'primary':paired(rows[arms[0]],rows[a],groups=['astra','bot2'],equal_groups=True) if {'astra','bot2'}<={r['group'] for r in rows[a]} else None,
                'by_group':{g:paired(rows[arms[0]],rows[a],groups=[g]) for g in sorted({r['group'] for r in rows[a]})}}
        if b['phase'] not in ('final_core','final_guard'):
            scores={a:(sum(r['score'] for r in rows[a] if r['group']=='astra')/max(1,sum(r['group']=='astra' for r in rows[a]))+
                       sum(r['score'] for r in rows[a] if r['group']=='bot2')/max(1,sum(r['group']=='bot2' for r in rows[a])))/2 for a in arms}
            winner=max(arms,key=lambda a:scores[a]);setmeta(db,'best',winner)
            archive=list(dict.fromkeys(meta(db,'archive',[])+[winner]+arms))[-8:]
            if 'Y1' not in archive:archive=['Y1']+archive
            setmeta(db,'archive',archive)
    hard=[]
    for a in arms[1:]:
        reference={(r['opponent'],r['seed'],r['seat']):r for r in rows[arms[0]]}
        for r in rows[a]:
            base=reference[(r['opponent'],r['seed'],r['seat'])]
            if r.get('game') and base['score']!=r['score']:
                path=run/'batches'/batch/a/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl'
                decisions=[json.loads(l) for l in path.read_text().splitlines()]
                changed=[d for d in decisions if d['info'].get('mcgs',{}).get('changed')]
                if changed:hard.append({'key':[r['seed'],r['opponent'],r['seat']], 'candidate':a,
                    'baseline_score':base['score'],'candidate_score':r['score'],
                    'classification':'search_allocation_or_cutoff_value_requires_paired_continuation',
                    'decision':changed[0],'game_path':str(path.relative_to(ROOT))})
    atomic(run/'hard_cases'/f'{batch}.json',hard);atomic(run/'batches'/batch/'report.json',report)
    if hard and b['phase']=='development':
        from development.secret_hunter_mcgs.diagnose import run as diagnose
        diagnose(db,run,batch,hard)
    if b['phase']=='selection':
        setmeta(db,'selection_done',True)
        ranked=sorted(report['comparisons'],key=lambda a:report['comparisons'][a]['primary']['b_rate'],reverse=True)
        setmeta(db,'selected_challenger',ranked[0])
    with db:db.execute("UPDATE batches SET status='done' WHERE id=?",(batch,))
    print(json.dumps({'batch_complete':batch,'wins':{a:report['arms'][a]['all']['wins'] for a in arms},'hard_cases':len(hard)}),flush=True)
    return True

def propose(db,generation):
    candidates=meta(db,'candidates');eligible=[a for a in meta(db,'archive') if a.startswith(('M5-','M6-','G'))]
    parent=eligible[generation%len(eligible)] if eligible else 'M5-dpw'
    settings=dict(candidates[parent].get('settings') or {})
    changes=[{'rollout':'filtered'},{'value_board':1.6,'margin':.08},
             {'particles':8,'chance':'dpw'},{'horizon':1},{'opponent_plays':False},
             {'max_transitions':650,'margin':.10},{'graph':'ucd','d1':3,'d2':1,'chance':'fixed','width':6},
             {'horizon':5,'rollout':'guided'}]
    delta=changes[generation%len(changes)];settings.update(delta);name=f'G{generation:03d}'
    target=HERE/'candidates'/name
    if target.exists():
        cfg=json.loads((target/'config.json').read_text())
        assert cfg['mcgs']==settings and cfg['parent']==parent
        candidate={'name':name,'path':str(target.relative_to(ROOT)),'sha256':fingerprint(target),
                   'settings':settings,'parent':parent}
    else:candidate=build(name,settings,parent)
    candidate.update(hypothesis=delta,origin='automatic_preimplemented_configuration',generation=generation)
    candidates[name]=candidate;setmeta(db,'candidates',candidates);atomic(HERE/'automatic-lineage.json',candidates)
    return parent,name

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['pilot','run','resume','status'])
    p.add_argument('--run',type=Path,required=True);p.add_argument('--hours',type=float,default=8)
    p.add_argument('--max-full-games',type=int,default=12000);p.add_argument('--max-continuations',type=int,default=60000)
    p.add_argument('--workers',type=int,default=4);p.add_argument('--pilot-seeds',type=int,default=2)
    p.add_argument('--max-batches',type=int,default=0,help='Optional bounded diagnostic invocation.')
    args=p.parse_args();run=(ROOT/args.run).resolve();run.mkdir(parents=True,exist_ok=True)
    if args.command=='status':
        db=connect(run);print(json.dumps(status(db,run,False),indent=2));return
    with (run/'writer.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another writer owns this run.')
        db=connect(run);initialize(db,run,args);recovered=reconcile(db)
        if not meta(db,'preflight'):
            from development.secret_hunter_mcgs.preflight import run as preflight
            setmeta(db,'preflight',preflight(run))
        signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('STOP',True))
        signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('STOP',True))
        mode=meta(db,'mode','pilot') if args.command=='resume' else args.command
        setmeta(db,'mode',mode);setmeta(db,'pid',os.getpid())
        print(json.dumps({'started':mode,'pid':os.getpid(),'recovered':recovered}),flush=True)
        if mode=='pilot':
            from development.secret_hunter_mcgs.pilot_replay import run as pilot_replay
            pilot_replay(db,run)
            reserve(db,'pilot-000','development',['Y1','M5-uct','M5-fixed','M5-dpw'],10000000,args.pilot_seeds)
            reserve(db,'pilot-001','development',['Y1','M5-dpw'],10000100,args.pilot_seeds)
        completed=0
        while not STOP:
            batch=db.execute("SELECT * FROM batches WHERE status='pending' ORDER BY start LIMIT 1").fetchone()
            if batch is None:
                if mode=='pilot':break
                attempts=db.execute('SELECT count(*) FROM attempts').fetchone()[0];manifest=meta(db,'manifest')
                remaining=manifest['limits']['full_games']-attempts;elapsed=meta(db,'effective_seconds',0)
                if not meta(db,'selection_done',False) and (remaining<=manifest['reserved_final_games']+720 or elapsed>=manifest['limits']['seconds']*.60):
                    eligible=[a for a in reversed(meta(db,'archive')) if a.startswith(('M5-','M6-','G'))][:3]
                    reserve(db,'selection','selection',['Y1']+eligible,10050000,10)
                elif meta(db,'selection_done',False) and not meta(db,'final_opened',False):
                    challenger=meta(db,'selected_challenger')
                    setmeta(db,'challenger',challenger);setmeta(db,'final_opened',True)
                    reserve(db,'final-core','final_core',['Y1',challenger],10100000,80)
                    reserve(db,'final-guard','final_guard',['Y1',challenger],10200000,20,'guardrail')
                    atomic(run/'frozen-challenger.json',meta(db,'candidates')[challenger])
                elif meta(db,'final_opened',False):
                    from development.secret_hunter_mcgs.finalize import finalize
                    finalize(db,run)
                    break
                else:
                    generation=meta(db,'generation',0);parent,child=propose(db,generation)
                    reserve(db,f'gen-{generation:03d}','development',list(dict.fromkeys(['Y1',parent,child])),10001000+generation*100,4)
                    setmeta(db,'generation',generation+1)
                batch=db.execute("SELECT * FROM batches WHERE status='pending' ORDER BY start LIMIT 1").fetchone()
            for arm in json.loads(batch['arms']):
                if STOP:break
                run_arm(db,run,batch['id'],arm,args)
            analysis_start=time.monotonic()
            done=analyze(db,run,batch['id'])
            setmeta(db,'effective_seconds',meta(db,'effective_seconds',0)+time.monotonic()-analysis_start)
            status(db,run)
            if not done:break
            completed+=1
            if args.max_batches and completed>=args.max_batches:break
        setmeta(db,'pid',None);status(db,run)
        print(json.dumps({'stopped':True,'interrupted':STOP,'completed_batches_this_invocation':completed}),flush=True)

if __name__=='__main__':main()
