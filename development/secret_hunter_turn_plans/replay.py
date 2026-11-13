"""Replay stored engine actions exactly, independently of search timing."""
import argparse
import json
from pathlib import Path
import sys
from development.secret_hunter_turn_plans.build import HERE
from development.secret_hunter_turn_plans.study import RUN,ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('result',type=Path);args=parser.parse_args()
    result=json.loads(args.result.read_text())
    request=json.loads(args.result.with_name(args.result.stem+'.request.json').read_text())
    source_path=Path(request['source'])
    local_source=RUN/source_path.parent.name/source_path.name
    if local_source.exists():
        # Evidence archives can be extracted outside the original workstation.
        source_path=local_source
    source=json.loads(source_path.read_text())
    sys.path[:0]=[str(HERE/'candidates'/result.get('candidate','R1-memory')/'scripts'),str(ROOT/'development/secret_hunter_mcgs')]
    from mcgs_init import initialize
    initialize()
    from mcgs_world import build
    from action_validator import legal
    assert result['full_trace'],'This job did not save the complete trace; use a sample-zero evidence case.'
    hidden=result['audit_hidden_hypothesis'];seed=41000000+source['source_seed']*1000+result['sample']
    world=build(source['state'],seed,opponent_hand=hidden['opponent_hand'],opponent_deck=hidden['opponent_deck'])
    world.game.random.seed(hidden['initial_rng_seed'])
    if 'own_deck' in hidden:assert [c.id for c in world.player(1).deck]==hidden['own_deck']
    for index,step in enumerate(result['full_trace']):
        state=world.view(step['seat'])
        for key in ('phase','turn','you','opponent'):
            assert state.get(key)==step['state'].get(key),(index,key)
        assert legal(state,step['action']),(index,step['action'])
        assert world.step(step['seat'],step['action']).accepted
    assert world.over and world.winner==result['winner']
    print(json.dumps({'case':result['case'],'sample':result['sample'],'route':result['route'],
                      'actions':len(result['full_trace']),'winner':world.winner,'exact_public_trace_match':True}))


if __name__=='__main__':main()
