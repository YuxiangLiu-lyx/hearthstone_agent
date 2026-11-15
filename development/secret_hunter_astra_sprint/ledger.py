"""Sprint-local ledger derived from the established durable game supervisor."""
import json,os,signal,sqlite3,sys,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import summarize
from development.secret_hunter_mcgs.supervision import GameProcess
STOP=False

def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:
        json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    temp.replace(path)

def connect(run):
    run.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(run/'ledger.sqlite');db.row_factory=sqlite3.Row
    db.executescript('''PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,phase TEXT,arms TEXT,start INTEGER,seeds INTEGER,status TEXT);
    CREATE TABLE IF NOT EXISTS tasks(key TEXT PRIMARY KEY,batch TEXT,candidate TEXT,phase TEXT,opponent TEXT,seed INTEGER,seat INTEGER,status TEXT,result TEXT);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,task TEXT,status TEXT,started REAL,finished REAL,result_path TEXT);
    CREATE TABLE IF NOT EXISTS auxiliary_games(key TEXT PRIMARY KEY,status TEXT,started REAL,finished REAL,result TEXT);
    ''');db.commit();return db

def meta(db,key,default=None):
    r=db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
    return json.loads(r[0]) if r else default

def setmeta(db,key,value):
    db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',(key,json.dumps(value)));db.commit()

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
    # Fresh processes also prevent same-named modules crossing candidates.
    active={};index=0;last=time.monotonic();stop_deadline=None;retries={}
    def interrupt(aid,task,reason):
        with db:
            db.execute('UPDATE attempts SET status=?,finished=? WHERE id=?',(reason,time.time(),aid))
            db.execute("UPDATE tasks SET status='pending' WHERE key=?",(task['key'],))
        print(json.dumps({'batch':batch,'arm':arm,'attempt':aid,'execution_failure':reason,
                          'strategy_score':None}),flush=True)
    try:
        while active or (index<len(tasks) and not STOP):
            now=time.monotonic()
            if STOP and stop_deadline is None:stop_deadline=now+args.stop_grace_seconds
            limits=meta(db,'manifest')['limits'];seconds=meta(db,'effective_seconds',0)+now-last
            attempts=db.execute('SELECT count(*) FROM attempts').fetchone()[0]+db.execute('SELECT count(*) FROM auxiliary_games').fetchone()[0]
            reserved=0 if meta(db,'final_opened',False) else meta(db,'manifest')['reserved_final_games']
            while index<len(tasks) and len(active)<args.workers and not STOP:
                if attempts>=limits['full_games']-reserved or seconds>=limits['seconds'] or time.time()>=meta(db,'manifest')['deadline']:break
                task=tasks[index];index+=1
                with db:
                    cursor=db.execute('INSERT INTO attempts(task,status,started) VALUES (?,?,?)',(task['key'],'running',time.time()))
                    aid=cursor.lastrowid;result_path=run/'attempts'/f'{aid:06d}.json'
                    db.execute('UPDATE attempts SET result_path=? WHERE id=?',(str(result_path.resolve()),aid))
                    db.execute("UPDATE tasks SET status='running' WHERE key=?",(task['key'],))
                job=(str(src),json.loads(task['opponent']),task['seed'],task['seat'],str(run/'batches'/batch/arm),'python')
                full_cli=task['phase'] in ('cli_development','selection','final_core','final_guard')
                timeout=args.cli_game_timeout_seconds if full_cli else args.game_timeout_seconds
                request=result_path.with_suffix('.request.json')
                atomic(request,{'task':job,'result_path':str(result_path),'full_cli':full_cli,
                                'timeout_seconds':timeout})
                try:
                    process=GameProcess([sys.executable,'-m','development.secret_hunter_mcgs.game_worker',str(request)],
                                        ROOT,result_path.with_suffix('.worker.log'))
                except Exception:
                    interrupt(aid,task,'launch_failed')
                    raise
                active[aid]=(process,task,result_path,timeout);attempts+=1
            if not active:break
            time.sleep(.2);changed=False;now=time.monotonic()
            for aid,(process,task,result_path,timeout) in list(active.items()):
                reason=None
                if stop_deadline is not None and now>=stop_deadline:reason='interrupted'
                elif time.time()>=meta(db,'manifest')['deadline']:reason='budget_expired'
                elif now-process.started>=timeout:reason='timeout'
                elif process.process.poll() is None:continue
                process.close();del active[aid];changed=True
                try:
                    row=json.loads(result_path.read_text())
                    assert row['seed']==task['seed'] and row['seat']==task['seat']
                    assert row['opponent']==json.loads(task['opponent'])['name'] and 'score' in row
                except (OSError,ValueError,KeyError,AssertionError):
                    interrupt(aid,task,reason or 'worker_failed')
                    # A failed execution remains charged, with no fabricated loss.
                    # Retry once per invocation; a persistent failure leaves the
                    # batch incomplete and prevents selection or final promotion.
                    if not STOP and reason not in ('budget_expired','interrupted') and retries.get(task['key'],0)<1:
                        retries[task['key']]=retries.get(task['key'],0)+1;tasks.append(task)
                    continue
                with db:
                    db.execute("UPDATE attempts SET status='done',finished=? WHERE id=?",(time.time(),aid))
                    db.execute("UPDATE tasks SET status='done',result=? WHERE key=?",(json.dumps(row),task['key']))
                print(json.dumps({'batch':batch,'arm':arm,'attempt':aid,'score':row['score'],'error':row.get('harness_error'),'wall_s':row.get('wall_s')}),flush=True)
            now=time.monotonic()
            if changed or now-last>=5:
                setmeta(db,'effective_seconds',meta(db,'effective_seconds',0)+now-last);last=now
                status(db,run)
    finally:
        for aid,(process,task,_,_) in active.items():
            process.close();interrupt(aid,task,'interrupted')
        setmeta(db,'effective_seconds',meta(db,'effective_seconds',0)+time.monotonic()-last)
        status(db,run)
    assert fingerprint(src)==candidate['sha256']
