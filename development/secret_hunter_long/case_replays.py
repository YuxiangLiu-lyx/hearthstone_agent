"""Replay stored actions against the actual engine, including next visible state."""
import json
import time
from development.secret_hunter_long.study import RUN,HERE,ROOT
from development.secret_hunter_long.tactical import setup,visible
from development.secret_hunter_mcgs import train

CASES=[('astra-board-proxy',51401009,2),('bot2-trade-proxy',51401008,1),('astra-sticky-proxy',51401047,2)]

def main():
    setup()
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    db=train.connect(RUN);db.execute('CREATE TABLE IF NOT EXISTS auxiliary_games (key TEXT PRIMARY KEY,status TEXT,started REAL,finished REAL,result TEXT)');db.commit()
    pop={s['name']:s for s in json.loads((ROOT/'development/teacher_eval/core.json').read_text())};records=[]
    for name,seed,seat in CASES:
        for arm in ('B','DARC'):
            key=f'case-{arm}-{seed}-{name}-s{seat}';old=db.execute('select * from auxiliary_games where key=?',(key,)).fetchone()
            if old:
                assert old['status']=='done';records.append(json.loads(old['result']));continue
            row=db.execute("select result from tasks where batch='deck-screen' and candidate=? and seed=? and seat=? and opponent like ? and status='done'",(arm,seed,seat,'%'+name+'%')).fetchone()
            assert row;result=json.loads(row['result']);spec=pop[name];folder=RUN/'batches/deck-screen'/arm/'games'/result['game']
            logs={i:[json.loads(l) for l in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
            with db:db.execute('insert into auxiliary_games values (?,?,?,?,?)',(key,'running',time.time(),None,None))
            try:
                decks={seat:load_deck(HERE/'candidates'/arm/'deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
                e=Engine(decks[1],decks[2],seed,max_turns=180);ix={1:0,2:0};trace=[];own=[]
                while not e.over:
                    active,_=e.pending();r=logs[active][ix[active]];s=e.view(active)
                    assert visible(s)==visible(r['state']),(key,active,ix[active])
                    before=visible(e.view(seat));assert e.step(active,r['action']).accepted
                    event={'player':active,'turn':s['turn'],'action':r['action'],'before_public':before,'after_public':visible(e.view(seat))}
                    trace.append(event)
                    if active==seat:own.append(event)
                    ix[active]+=1
                assert e.winner==result['result']['winner']
                evidence=RUN/'case-replays'/(key+'.json');train.atomic(evidence,{'key':key,'arm':arm,'source':str(folder),'winner':e.winner,'steps':len(trace),'own_actions':own,'all_actions':trace})
                record={'key':key,'arm':arm,'seed':seed,'opponent':name,'seat':seat,'winner':e.winner,'own_win':e.winner==seat,
                    'steps':len(trace),'all_visible_states_and_actions_verified':True,'path':str(evidence)}
                with db:db.execute("update auxiliary_games set status='done',finished=?,result=? where key=?",(time.time(),json.dumps(record),key))
                records.append(record)
            except Exception as exc:
                with db:db.execute("update auxiliary_games set status='error',finished=?,result=? where key=?",(time.time(),json.dumps({'error':repr(exc)}),key))
                raise
    train.atomic(RUN/'case-replay-audit.json',records);print(json.dumps(records))

if __name__=='__main__':main()
