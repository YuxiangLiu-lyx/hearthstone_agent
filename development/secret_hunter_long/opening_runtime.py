"""Verify the deployed CLI exactly implements the locked opening intervention."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import sys
from development.secret_hunter_long.study import HERE,RUN
from development.secret_hunter_mcgs.runtime import probe
from development.secret_hunter_program.common import quantiles
from development.secret_hunter_mcgs import train

def main():
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--candidate',required=True);p.add_argument('--start',type=int,default=51421000);a=p.parse_args()
    m=json.loads((RUN/'mulligan-sources'/f'manifest-{a.arm}-{a.start}.json').read_text())
    cases=[json.loads((RUN/'mulligan-sources'/(cid+'.json')).read_text()) for cid in m['cases']]
    sys.path.insert(0,str(HERE/'candidates'/a.arm/'scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    from development.secret_hunter_tactics.run import opponent
    from development.secret_hunter_long.study import ROOT
    # Mining may inspect player2's visible opening while player1 is pending.
    # A CLI probe must use the actual pending decision, after player1 acts.
    states=[]
    for ix,s in enumerate(cases):
        seat=s['seat'];spec=s['opponent_spec'];decks={seat:load_deck(HERE/'candidates'/a.arm/'deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
        e=Engine(decks[1],decks[2],s['seed'])
        if e.pending()[0]!=seat:
            other=e.pending()[0];assert e.step(other,opponent(spec).fn(e.view(other))).accepted
        state=e.view(seat);assert state['phase']=='mulligan'
        assert [(c['entity_id'],c['card_id']) for c in state['you']['hand']]==[tuple(x) for x in s['opening_hand']]
        states.append({**state,'seq':1000+ix,'player':seat,'timeout_s':2,'events':[]})
    def check(pair):
        ix,s=pair;state=states[ix]
        r=probe(HERE/'candidates'/a.candidate,state,'locked-opening');r['case']=s['case']
        r['matches_locked_label_action']=r['action']==s['options']['trap_no_low']
        assert r['matches_locked_label_action'] and r['valid'] and not r['worker_error'] and not r['fallback'] and r['elapsed_s']<=2
        return r
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(check,enumerate(cases)))
    result={'candidate':a.candidate,'public_sources':len(cases),'all_match':True,'latency_s':quantiles([r['elapsed_s'] for r in rows]),'records':rows}
    train.atomic(RUN/f'opening-runtime-{a.candidate}.json',result);print(json.dumps({k:v for k,v in result.items() if k!='records'}))

if __name__=='__main__':main()
