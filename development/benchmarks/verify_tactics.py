"""Recreate local test games in the host and verify flagged public-state tactics in Fireplace.

The policy receives only engine.view(), never the Engine or RNG state. Full host reconstruction
is development-only differential verification, never available to a playing policy.
"""
import argparse,copy,json,sys
from pathlib import Path
from hs_arena.engine import Engine
from hs_arena.deck import Deck
from hs_arena._fp import init_engine

def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',default='development/reports/paladin-loss-audit.json')
    p.add_argument('--out',default='development/reports/tactics-engine-verification.json');args=p.parse_args()
    sys.path.insert(0,str(Path('development/candidates/v4-paladin-search/scripts').resolve()))
    from planner import lethal_plan
    data=json.loads(Path(args.audit).read_text());results=[]
    db=init_engine();memo={id(c):c for c in db.db.values()}
    for flag in data['end_turn_possible_lethals']:
        folder=Path(flag['observations']).parents[1]
        metadata=json.loads((folder/'game.json').read_text())
        decks=[Deck(p['hero_class'],tuple(p['deck'])) for p in metadata['players']]
        e=Engine(*decks,metadata['seed'],max_turns=180)
        logs={i:iter(json.loads(l) for l in (folder/f'p{i}/observations.jsonl').read_text().splitlines()) for i in (1,2)}
        target_seat=int(Path(flag['observations']).parent.name[1:])
        found=False
        while not e.over:
            i,_=e.pending();row=next(logs[i]);s=row['state']
            if i==target_seat and s['seq']==flag['seq']:
                before=e.view(i)
                assert before['you']==s['you'] and before['opponent']==s['opponent'],'Replay divergence'
                clone=copy.deepcopy(e,dict(memo));actions=[]
                for _ in range(12):
                    if clone.over:break
                    plan=lethal_plan(clone.view(i),budget_s=.5,max_nodes=7000)
                    if not plan:break
                    assert clone.step(i,plan[0]).accepted
                    actions.append(plan[0])
                results.append({**flag,'verified_win':clone.over and clone.winner==i,'actual_actions':actions})
                found=True;break
            assert e.step(i,row['action']).accepted
        assert found
    Path(args.out).write_text(json.dumps(results,indent=2));print('Verified',sum(r['verified_win'] for r in results),'of',len(results))
    assert all(r['verified_win'] for r in results)

if __name__=='__main__':main()
