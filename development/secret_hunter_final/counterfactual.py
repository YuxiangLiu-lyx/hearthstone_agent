"""Exact-prefix restoration, paired whole-turn interventions and durable labels."""
import argparse
import copy
import hashlib
import fcntl
import json
import os
from pathlib import Path
import random
import signal
import sqlite3
import subprocess
import sys
import time
import traceback
from development.secret_hunter_final.study import ROOT,RUN,HERE
from development.secret_hunter_mcgs import train

def setup():
    sys.path.insert(0,str(HERE/'candidates/B/scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()

def visible(s):return {k:s.get(k) for k in ('phase','turn','you','opponent','legal_actions')}
def digest(s):return hashlib.sha256(json.dumps(visible(s),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def restore(source):
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    seat=source['seat'];spec=source['opponent_spec']
    decks={seat:load_deck(HERE/'candidates/B/deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
    e=Engine(decks[1],decks[2],source['seed'],max_turns=180)
    folder=ROOT/source['game_path'];logs={i:[json.loads(x) for x in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
    indices={1:0,2:0};steps=0
    while not e.over:
        active,_=e.pending();row=logs[active][indices[active]];s=e.view(active)
        assert visible(s)==visible(row['state']), ('prefix public mismatch',source['case'],active,indices[active])
        if active==seat and row['state']['seq']==source['seq']:
            assert digest(s)==source['state_digest'];return e,steps
        assert e.step(active,row['action']).accepted
        indices[active]+=1;steps+=1
    raise ValueError('root not reached')

def mine(batch='dev-core',arm='B',cap=160):
    setup()
    from development.secret_hunter_final.early_routes import ROUTES,features,propose
    db=train.connect(RUN)
    rows=[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done' order by seed,opponent,seat",(batch,arm))]
    pop={o['name']:o for o in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    cases=[];coverage={'games':len(rows),'wins_empty_t3':0,'losses_empty_t3':0,'wins':0,'losses':0,'eligible':0,'outside_effect':0,'outside_with_chance':0}
    for r in rows:
        if r.get('harness_error'):continue
        coverage['wins' if r['score'] else 'losses']+=1
        folder=RUN/'batches'/batch/arm/'games'/r['game']
        logs=[json.loads(x) for x in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()]
        turns=set();pool=[]
        for z in logs:
            s=z['state']
            if s['phase']!='main':continue
            if z['info'].get('turn_search',{}).get('reason')=='top_action_outside_effect_coverage':
                coverage['outside_effect']+=1;coverage['outside_with_chance']+=bool(z['info'].get('chance'))
            first=s['turn'] not in turns;turns.add(s['turn']);f=features(s)
            if first and f['mana']==3 and f['own_empty'] and f['incoming']>=4:
                coverage['wins_empty_t3' if r['score'] else 'losses_empty_t3']+=1
            if not 1<=f['mana']<=5:continue
            # Prioritize natural opening coin forks and later lost-board states.
            if not ((f['coin'] and f['mana']<=3) or (2<=f['mana']<=5 and f['incoming']>=3) or (f['opponent_hunter'] and 2<=f['mana']<=4)):continue
            available=[]
            for route in ROUTES:
                a=propose(s,route,{},z['action'])
                if a is not None and (a!=z['action'] or route=='bank_tail'):
                    available.append(route)
            if len(available)<2:continue
            priority=(not r['score'],f['own_empty'] and f['incoming']>=4,first,f['coin'],len(available))
            pool.append((priority,z,available))
        # One root per game limits adjacent-state duplication. All seats/proxies
        # still use the same seed split, including all future samples.
        if not pool:continue
        coverage['eligible']+=1
        _,z,routes=max(pool,key=lambda x:x[0]);s=z['state']
        cid=f"{r['seed']}-{r['opponent']}-s{r['seat']}-q{s['seq']}"
        cases.append({'case':cid,'seed':r['seed'],'seat':r['seat'],'seq':s['seq'],
             'source_score':r['score'],'state':s,'state_digest':digest(s),'opponent_spec':pop[r['opponent']],
             'game_path':str(folder.relative_to(ROOT)),'features':features(s),
             'split':'validation' if r['seed']%5 in (0,1) else 'train',
             'routes':['baseline']+list(dict.fromkeys(routes[:6]+[x for x in ('bank_tail','power','hounds_trade') if x in routes])),
             'original_action':z['action']})
    # Balanced source inclusion: keep both wins and losses, then deterministic
    # source ordering, never select based on counterfactual outcomes.
    cases=sorted(cases,key=lambda c:(c['source_score'],c['seed'],c['case']))
    lost=[c for c in cases if not c['source_score']];won=[c for c in cases if c['source_score']]
    chosen=lost[:cap//2]+won[:cap-len(lost[:cap//2])]
    dest=RUN/'early-sources';dest.mkdir(exist_ok=True)
    for c in chosen:train.atomic(dest/(c['case']+'.json'),c)
    train.atomic(dest/'manifest.json',{'cases':[c['case'] for c in chosen],'coverage':coverage,
                                     'selection':'one root/game, losses up to half; six alternatives plus shared-first/power/Hounds controls',
                                     'partition':'source seed modulo 5; 0,1 held out, 2,3,4 train'})
    print(json.dumps({'sources':len(chosen),'coverage':coverage}))

def execute(job):
    setup()
    from development.secret_hunter_final.early_routes import propose
    from program_policy import decide
    from state_features import with_public_history
    from action_validator import legal
    from development.secret_hunter_tactics.run import opponent
    source=json.loads((RUN/'early-sources'/(job['case']+'.json')).read_text())
    e,prefix=restore(source);seat=source['seat'];root_turn=e.turn
    before=digest(e.view(seat));sample=job['sample']
    if sample:
        # Offline alternative worlds preserve actual simulated hand and deck
        # multisets but resample both hidden remaining orders and future RNG.
        rng=random.Random(71600000+source['seed']*17+sample)
        for i in (1,2):rng.shuffle(e.player(i).deck)
        e.game.random.seed(81700000+source['seed']*31+sample)
    if job.get('scenario')=='forced_coil':
        from hearthstone.enums import Zone
        q=e.player(3-seat)
        if not any(c.id=='EX1_302' for c in q.hand):
            coil=next((c for c in q.deck if c.id=='EX1_302'),None)
            if coil is None:raise ValueError('No unspent Coil for stress conditioning')
            if q.hand:
                exchanged=q.hand[0];exchanged.zone=Zone.DECK;coil.zone=Zone.HAND
            else:
                q.deck.remove(coil);q.deck.append(coil)
    assert before==digest(e.view(seat))
    hidden={'deck1':[c.id for c in e.player(1).deck],'deck2':[c.id for c in e.player(2).deck],
            'hand1':[c.id for c in e.player(1).hand],'hand2':[c.id for c in e.player(2).hand],
            'rng_hash':hashlib.sha256(repr(e.game.random.getstate()).encode()).hexdigest()}
    cfg=json.loads((HERE/'candidates/B/config.json').read_text());foe=opponent(source['opponent_spec'])
    memory={};sequence=[];trace=[];endpoint=None;after_response=None;changes=0;forced_used=False
    for step in range(600):
        if e.over:break
        active,_=e.pending();s=e.view(active)
        history=[v for ev in e.events if (v:=ev.view(active)) is not None]
        s.update(player=active,seq=step+1,game_id='offline-public-turn',timeout_s=2,events=[])
        s=with_public_history(s,history)
        intervention=active==seat and e.turn==root_turn
        if active==seat:
            a,info=decide(s,cfg)
            base=dict(a)
            if intervention and job['route']!='baseline' and info.get('reason')!='guaranteed_lethal':
                alternative=propose(s,job['route'],memory,base)
                if alternative is not None:a=alternative
            changes+=int(intervention and a!=base)
        else:
            a=foe.fn(s);base=None
            if job.get('scenario')=='forced_coil' and not forced_used and e.turn==root_turn+1:
                coil=next((c for c in s['you']['hand'] if c['card_id']=='EX1_302'),None)
                amani=next((m for m in s['you']['board'] if m['card_id']=='EX1_393' and not m.get('silenced') and m['health']==m['max_health'] and m['health']>1),None)
                forced={'type':'play_card','card':coil['entity_id'],'target':amani['entity_id']} if coil and amani else None
                if forced and legal(s,forced):a=forced;forced_used=True
        assert legal(s,a), ('route illegal',job,a)
        if intervention:
            sequence.append({'action':a,'baseline_action':base,'state_digest':digest(s),
                             'hand':[(c['entity_id'],c['card_id']) for c in s['you']['hand']],
                             'board':[(m['entity_id'],m['card_id']) for side in ('you','opponent') for m in s[side]['board']]})
        trace.append({'seat':active,'action':a,'state_digest':digest(s)})
        assert e.step(active,a).accepted
        if intervention:endpoint=visible(e.view(seat))
        if after_response is None and (e.over or e.turn>=root_turn+2):after_response=visible(e.view(seat))
    assert e.over, ('nonterminal',job)
    return {**job,'source_seed':source['seed'],'split':source['split'],'features':source['features'],
            'prefix_verified_steps':prefix,'root_digest':before,'audit_hidden':hidden,
            'win':int(e.winner==seat),'winner':e.winner,'terminal':True,'actions_changed':changes,
            'forced_coil_used':forced_used,
            'first_changed':bool(sequence and sequence[0]['action']!=sequence[0]['baseline_action']),
            'later_changed':any(x['action']!=x['baseline_action'] for x in sequence[1:]),
            'sequence':sequence,'endpoint':endpoint,'after_response':after_response,'trace':trace}

def run_jobs(samples=3,workers=2,limit=2400,scenario='natural'):
    from development.secret_hunter_mcgs.supervision import GameProcess
    db=train.connect(RUN)
    db.executescript('''CREATE TABLE IF NOT EXISTS cf_jobs(key TEXT PRIMARY KEY,job TEXT,status TEXT,result_path TEXT);
    CREATE TABLE IF NOT EXISTS cf_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT,status TEXT,started REAL,finished REAL);''')
    manifest=json.loads((RUN/'early-sources/manifest.json').read_text())
    output=RUN/'early-labels';output.mkdir(exist_ok=True)
    for cid in manifest['cases']:
        source=json.loads((RUN/'early-sources'/(cid+'.json')).read_text())
        if scenario=='forced_coil' and source.get('kind')!='late_cheap_defense':continue
        for sample in range(samples):
            for route in source['routes']:
                key=f'{cid}-{sample}-{route}'+('-forced_coil' if scenario=='forced_coil' else '')
                job={'case':cid,'sample':sample,'route':route,'scenario':scenario}
                db.execute('insert or ignore into cf_jobs values (?,?,?,?)',(key,json.dumps(job),'pending',str(output/(key+'.json'))))
    db.commit()
    # A file result is committed before marking a job done. Interrupted work is
    # charged; reruns skip durable results and record a new attempt otherwise.
    with db:
        for r in db.execute("select * from cf_jobs where status='running'").fetchall():
            db.execute('update cf_jobs set status=? where key=?',('done' if Path(r['result_path']).exists() else 'pending',r['key']))
        db.execute("update cf_attempts set status='interrupted',finished=? where status='running'",(time.time(),))
    todo=db.execute("select * from cf_jobs where status='pending' order by key").fetchall();active={};ix=0
    end=train.meta(db,'manifest')['candidate_generation_deadline']
    try:
        while active or ix<len(todo):
            used=db.execute('select count(*) from cf_attempts').fetchone()[0]
            while ix<len(todo) and len(active)<workers and used<min(limit,6000) and time.time()<end:
                row=todo[ix];ix+=1;path=Path(row['result_path']);request=path.with_suffix('.request.json')
                train.atomic(request,json.loads(row['job']))
                with db:
                    aid=db.execute("insert into cf_attempts(key,status,started) values (?,'running',?)",(row['key'],time.time())).lastrowid
                    db.execute("update cf_jobs set status='running' where key=?",(row['key'],))
                train.setmeta(db,'continuations',used+1+train.meta(db,'extra_continuations',0))
                proc=GameProcess([sys.executable,'-m','development.secret_hunter_final.counterfactual','worker','--request',str(request)],ROOT,path.with_suffix('.log'))
                active[aid]=(proc,row);used+=1
            if not active:break
            time.sleep(.2)
            for aid,(proc,row) in list(active.items()):
                if proc.process.poll() is None and time.monotonic()-proc.started<60:continue
                proc.close();del active[aid];path=Path(row['result_path'])
                result=json.loads(path.read_text()) if path.exists() else {'error':'worker_timeout_or_crash'}
                status='error' if result.get('error') else 'done'
                with db:
                    db.execute('update cf_attempts set status=?,finished=? where id=?',(status,time.time(),aid))
                    db.execute('update cf_jobs set status=? where key=?',(status,row['key']))
                if aid%25==0 or status=='error':print(json.dumps({'attempt':aid,'status':status,'error':result.get('error')}),flush=True)
    finally:
        for aid,(proc,row) in active.items():
            proc.close()
            with db:
                db.execute("update cf_attempts set status='interrupted',finished=? where id=?",(time.time(),aid))
                db.execute("update cf_jobs set status='pending' where key=?",(row['key'],))
    print(json.dumps({'cf_status':dict(db.execute('select status,count(*) from cf_jobs group by status').fetchall())}))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['mine','run','worker'])
    p.add_argument('--request',type=Path);p.add_argument('--samples',type=int,default=3);p.add_argument('--workers',type=int,default=2)
    p.add_argument('--limit',type=int,default=2400);p.add_argument('--cap',type=int,default=160)
    p.add_argument('--scenario',choices=['natural','forced_coil'],default='natural');a=p.parse_args()
    if a.command=='mine':mine(cap=a.cap)
    elif a.command=='run':
        with (RUN/'cf-writer.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            def stop(*_):raise KeyboardInterrupt
            signal.signal(signal.SIGTERM,stop)
            run_jobs(a.samples,a.workers,a.limit,a.scenario)
    else:
        try:result=execute(json.loads(a.request.read_text()))
        except Exception:result={'error':traceback.format_exc()}
        train.atomic(a.request.with_name(a.request.name.replace('.request.json','.json')),result)

if __name__=='__main__':main()
