"""Run frozen, paired public-information experiments through the official engine/skill seat."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

from hs_arena.agents.base import Player, Decision
from hs_arena.deck import load_deck
from hs_arena.protocol import Config
from hs_arena.runner import play_game
from hs_arena.skill.loader import load_skill
from hs_arena.skill.seat import SkillSeat
from development.benchmarks.run import ObservedPlayer, fingerprint, load_policy, wilson
from development.secret_hunter_program.common import ROOT, sha, write


class ScriptPlayer(Player):
    kind='secret-hunter-python'
    def __init__(self, candidate):
        super().__init__('secret-hunter',load_deck(Path(candidate)/'deck.json'))
        self.cfg=json.loads((Path(candidate)/'config.json').read_text());self.history=[];self.errors=[];self.memory={}
    def start(self,seat):
        super().start(seat);self.log=open(seat.player_dir/'observations.jsonl','w')
    def decide(self,state):
        from program_policy import decide
        from state_features import with_public_history
        from action_validator import legal
        self.history.extend(state.get('events',[]));s=with_public_history(state,self.history)
        start=time.monotonic();a,info=decide(s,self.cfg,**({'memory':self.memory} if self.cfg.get('plan_cache') else {}))
        assert legal(s,a),a
        self.log.write(json.dumps({'state':s,'action':a,'info':info,'elapsed_s':time.monotonic()-start})+'\n')
        return Decision('action',a)
    def stop(self):self.log.close()


def opponent(spec):
    # Frozen action enumerator prevents candidate interface changes altering opponents.
    _,actions=load_policy(ROOT/'development/checkpoints/v3-paladin-relay-champion')
    if spec.get('policy'):
        policy,_=load_policy(ROOT/spec['policy'])
        cfg=json.loads((ROOT/spec['policy']/'config.json').read_text())
        fn=lambda s:policy.decide(s,cfg)
    elif spec['mode']=='search':
        from development.opponents.search import decide
        fn=lambda s:decide(s,actions.expand)
    else:
        from development.opponents.population import decide
        fn=lambda s:decide(s,spec['mode'],actions.expand)
    return ObservedPlayer(spec['name'],load_deck(ROOT/spec['deck']),fn)


def worker(task):
    candidate,spec,seed,seat,output,mode=task
    sys.path.insert(0,str(Path(candidate).resolve()/'scripts'))
    p=SkillSeat(load_skill(candidate)) if mode=='skill' else ScriptPlayer(candidate)
    other=opponent(spec)
    game=uuid.uuid4().hex[:16]  # Do not disclose opponent identity or seed in the visible game_id.
    folder=Path(output)/'games'/game
    start=time.monotonic()
    result=play_game({seat:p,3-seat:other},game_dir=folder,game_id=game,seed=seed,config=Config(max_turns=180))
    meta=folder/f'p{seat}'/'seat/seat.json'
    course_failure=bool(json.loads(meta.read_text()).get('course_stops')) if meta.exists() else False
    return {'opponent':spec['name'],'seed':seed,'seat':seat,'first_player':result.get('first_player'),
            'score':int(result.get('winner')==seat),'result':result,'wall_s':time.monotonic()-start,
            'game':game,'opponent_errors':other.errors,'course_failure':course_failure}


def summary(rows):
    def aggregate(rs):
        n=len(rs);w=sum(r['score'] for r in rs)
        draws=sum(r['result'].get('winner') is None for r in rs)
        return {'n':n,'wins':w,'losses':n-w-draws,'draws_or_voids':draws,'win_rate':w/n if n else None,
                'wilson95_descriptive':wilson(w,n),'forfeits':sum(r['result']['reason'].startswith('forfeit') for r in rs),
                'illegal':sum(r['result']['illegal_counts'].get(str(r['seat']),0) for r in rs),
                'timeouts':sum(r['result']['timeouts'].get(str(r['seat']),0) for r in rs),
                'opponent_errors':sum(bool(r['opponent_errors']) for r in rs)}
    return {'all':aggregate(rows),'base':aggregate([r for r in rows if r['opponent']=='official-mage']),
            'primary':aggregate([r for r in rows if r['opponent']!='official-mage']),
            'by_opponent':{n:aggregate([r for r in rows if r['opponent']==n]) for n in sorted({r['opponent'] for r in rows})},
            'by_actual_first':{str(f):aggregate([r for r in rows if (r['first_player']==r['seat'])==f]) for f in (True,False)}}


def reserve(out,mode,count):
    import fcntl
    from datetime import datetime,timezone
    ledger=ROOT/'docs/secret_hunter_tactics/budget.json'
    with open(ROOT/'docs/secret_hunter_tactics/budget.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        data=json.loads(ledger.read_text())
        assert datetime.now(timezone.utc)<datetime.fromisoformat(data['deadline_utc']),'Wall-clock research budget exhausted'
        used=sum(r['reserved'] for r in data['runs'])
        assert used+count<=data['limits']['full_games'],(used,count)
        if 'confirmation' not in str(out):
            final_used=sum(r['reserved'] for r in data['runs'] if 'confirmation' in r['out'])
            assert used+count+max(0,data['reserved_final_games']-final_used)<=data['limits']['full_games']
        if mode=='skill':assert sum(r['reserved'] for r in data['runs'] if r['mode']=='skill')+count<=2
        data['runs'].append({'out':str(out),'mode':mode,'reserved':count,'status':'started'})
        write(ledger,data)


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['python','skill'],default='python');p.add_argument('--start',type=int,required=True)
    p.add_argument('--seeds',type=int,default=2);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--opponents',default='all');p.add_argument('--seats',default='1,2')
    p.add_argument('--split',choices=['development','validation','confirmation'],default='development')
    p.add_argument('--resume',action='store_true');p.add_argument('--hypothesis',required=True);args=p.parse_args()
    manifest=json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())
    assert sha(ROOT/manifest['population'])==manifest['population_sha256']
    for spec in manifest['opponents']:
        assert sha(ROOT/spec['deck'])==spec['deck_sha256']
        for name,digest in spec['dependencies'].items():
            if not name.startswith('installed:'):assert sha(ROOT/name)==digest,name
    population=[o for o in manifest['opponents'] if args.opponents=='all' or o['name'] in args.opponents.split(',')]
    assert population and (args.split=='confirmation')==(args.start>=100000)
    deck=json.loads((Path(args.candidate)/'deck.json').read_text())
    assert sorted(deck['cards'])==sorted(json.loads((ROOT/'secret-hunter-agent/deck.json').read_text())['cards'])
    seats=list(map(int,args.seats.split(',')));count=len(population)*args.seeds*len(seats)
    out=Path(args.out)
    if args.resume:
        previous=json.loads((out/'config.json').read_text())
        assert previous['candidate_sha256']==fingerprint(args.candidate),'Frozen candidate hash changed'
        assert previous['manifest_sha256']==sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json')
        for field in ('candidate','mode','start','seeds','opponents','seats','split'):
            assert previous[field]==getattr(args,field),f'Resume {field} mismatch'
        game_dirs=list((out/'games').glob('*'))
        unfinished=[str(g) for g in game_dirs if not (g/'result.json').exists()]
        assert not unfinished,f'Unfinished official games require inspection before resuming: {unfinished}'
        recorded={json.loads(line)['game'] for line in (out/'results.jsonl').read_text().splitlines()}
        assert {g.name for g in game_dirs}==recorded,'Unrecorded game directories require manual reconciliation; do not replay them silently'
    else:
        out.mkdir(parents=True,exist_ok=False);reserve(out,args.mode,count)
    metadata={**vars(args),'candidate_sha256':fingerprint(args.candidate),'deck_sha256':sha(Path(args.candidate)/'deck.json'),
              'manifest_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),'planned_games':count,
              'hypothesis':args.hypothesis}
    if args.resume:metadata=previous
    else:write(out/'config.json',metadata)
    tasks=[(args.candidate,s,seed,seat,str(out),args.mode) for s in population for seed in range(args.start,args.start+args.seeds) for seat in seats]
    rows=[json.loads(s) for s in (out/'results.jsonl').read_text().splitlines()] if args.resume else []
    done={(r['opponent'],r['seed'],r['seat']) for r in rows}
    tasks=[t for t in tasks if (t[1]['name'],t[2],t[3]) not in done]
    if not tasks:
        print(json.dumps({'resume':'hashes verified; all scheduled games already completed','completed':len(rows)}));return
    consecutive_course_failures=0;stopped_for_external_failure=False
    with ProcessPoolExecutor(max_workers=args.workers) as pool, (out/'results.jsonl').open('a' if args.resume else 'w') as log:
        futures=[pool.submit(worker,t) for t in tasks]
        for future in as_completed(futures):
            if future.cancelled():continue
            row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            consecutive_course_failures=consecutive_course_failures+1 if row.get('course_failure') else 0
            if consecutive_course_failures>=3:
                stopped_for_external_failure=True
                for pending in futures:pending.cancel()  # Running official games finish normally.
            if len(rows)%14==0 or len(rows)==count:print(f'Completed {len(rows)}/{count}; wins {sum(r["score"] for r in rows)}',flush=True)
    assert fingerprint(args.candidate)==metadata['candidate_sha256'],'candidate changed during run'
    report=summary(rows);report.update(planned=count,completed=len(rows),stopped_for_external_failure=stopped_for_external_failure)
    write(out/'summary.json',report);print(json.dumps(report))


if __name__=='__main__':main()
