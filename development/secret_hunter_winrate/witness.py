"""Replay an archived source prefix and execute one policy turn in the course engine."""
import argparse
import json
import sys
from pathlib import Path
from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.accounting import reserve, finish
from development.secret_hunter_response.counterfactual import reconstruct, public_key, projection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--case', type=int, default=33)
    parser.add_argument('--out', required=True)
    parser.add_argument('--name', help='Unique optional ledger name for a fresh replay attempt')
    args = parser.parse_args()
    candidate = ROOT/args.candidate
    sys.path.insert(0, str(candidate/'scripts'))
    from program_policy import decide
    from action_validator import legal
    from state_features import with_public_history
    name = args.name or 'winrate-witness-'+candidate.name+'-'+str(args.case)
    reserve(name, short=200, seconds=120)
    row = next(r for r in readlines(ROOT/'docs/secret_hunter_response/counterfactual-balanced.jsonl')
               if r['case_id'] == args.case)
    case = row['case']; seat = case['row']['seat']
    engine, _, prefix = reconstruct(case)
    cfg = json.loads((candidate/'config.json').read_text())
    trace = []
    for _ in range(20):
        s = engine.view(seat)
        s.update(player=seat, seq=len(trace), game_id='public-witness')
        s = with_public_history(s, [v for ev in engine.events if (v := ev.view(seat)) is not None])
        action, info = decide(s, cfg)
        assert legal(s, action) and not info.get('error')
        trace.append({'public_state_sha256': public_key(s), 'action': action, 'info': info})
        assert engine.step(seat, action).accepted
        if engine.over or action['type'] == 'end_turn':
            break
    else:
        raise AssertionError('Turn failed to terminate')
    write(ROOT/args.out, {'candidate': args.candidate, 'case': args.case,
                         'source': case['row'], 'initial_public_state': case['observation'],
                         'prefix_actions': prefix, 'trace': trace,
                         'after': projection(engine.view(seat))})
    finish(name, actual_short=prefix+len(trace))
    print(json.dumps({'candidate': candidate.name, 'actions': [r['action'] for r in trace]}))


if __name__ == '__main__':
    main()
