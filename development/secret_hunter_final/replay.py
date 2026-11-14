"""Verify stored actions against the original engine, without policy reranking."""
import argparse
import json
from pathlib import Path
import random
from development.secret_hunter_final.study import ROOT,RUN,HERE
from development.secret_hunter_final.counterfactual import setup,restore,digest,visible
from development.secret_hunter_mcgs import train

def verify_cf(path):
    row=json.loads(path.read_text());source=json.loads((RUN/'early-sources'/(row['case']+'.json')).read_text())
    e,prefix=restore(source);sample=row['sample'];seat=source['seat']
    if sample:
        rng=random.Random(71600000+source['seed']*17+sample)
        for i in (1,2):rng.shuffle(e.player(i).deck)
        e.game.random.seed(81700000+source['seed']*31+sample)
    if row.get('scenario')=='forced_coil':
        from hearthstone.enums import Zone
        q=e.player(3-seat)
        if not any(c.id=='EX1_302' for c in q.hand):
            coil=next(c for c in q.deck if c.id=='EX1_302')
            if q.hand:q.hand[0].zone=Zone.DECK;coil.zone=Zone.HAND
            else:q.deck.remove(coil);q.deck.append(coil)
    assert [c.id for c in e.player(1).deck]==row['audit_hidden']['deck1']
    assert [c.id for c in e.player(2).deck]==row['audit_hidden']['deck2']
    for step in row['trace']:
        assert e.pending()[0]==step['seat']
        assert digest(e.view(step['seat']))==step['state_digest']
        assert e.step(step['seat'],step['action']).accepted
    assert e.over and e.winner==row['winner']
    return {'file':str(path),'kind':'counterfactual','prefix_steps':prefix,'actions':len(row['trace']),
            'winner':e.winner,'every_visible_state_verified':True}

def verify_game(batch,arm,key):
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    db=train.connect(RUN);rows=[json.loads(x[0]) for x in db.execute('select result from tasks where batch=? and candidate=? and status="done"',(batch,arm))]
    row=next(r for r in rows if (r['opponent'],r['seed'],r['seat'])==tuple(key))
    pop={s['name']:s for pool in ['core','guardrail'] for s in json.loads((ROOT/f'development/teacher_eval/{pool}.json').read_text())}
    deck=load_deck(HERE/'candidates/B/deck.json');op=load_deck(ROOT/pop[row['opponent']]['deck']);seat=row['seat']
    e=Engine(deck,op,row['seed'],max_turns=180) if seat==1 else Engine(op,deck,row['seed'],max_turns=180)
    folder=RUN/'batches'/batch/arm/'games'/row['game']
    logs={i:[json.loads(x) for x in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in [1,2]}
    indices={1:0,2:0};steps=0
    while not e.over:
        active,_=e.pending();r=logs[active][indices[active]]
        assert visible(e.view(active))==visible(r['state']),(active,indices[active])
        assert e.step(active,r['action']).accepted
        steps+=1;indices[active]+=1
    assert e.winner==row['result']['winner']
    return {'batch':batch,'arm':arm,'key':key,'actions':steps,'winner':e.winner,'every_visible_state_verified':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--continuation',type=Path)
    p.add_argument('--batch');p.add_argument('--arm');p.add_argument('--opponent');p.add_argument('--seed',type=int);p.add_argument('--seat',type=int);a=p.parse_args()
    setup();db=train.connect(RUN)
    train.setmeta(db,'extra_continuations',train.meta(db,'extra_continuations',0)+1)
    result=verify_cf(a.continuation) if a.continuation else verify_game(a.batch,a.arm,[a.opponent,a.seed,a.seat])
    print(json.dumps(result))

if __name__=='__main__':main()
