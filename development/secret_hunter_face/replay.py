"""Replay a public Secret-control example, stopping before any terminal continuation."""
import argparse
import copy
import json
import sys
from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.accounting import reserve, finish
from development.secret_hunter_response.counterfactual import public_key, projection

D = ROOT/'docs/secret_hunter_face'
C = ROOT/'development/secret_hunter_face/candidates/F2'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='face-preference-secret-replay')
    parser.add_argument('--out', default='docs/secret_hunter_face/secret-replay.json')
    args = parser.parse_args()
    reserve(args.name, short=200, seconds=180)
    sys.path.insert(0, str(C/'scripts'))
    from program_policy import decide
    from action_validator import legal
    from state_features import with_public_history
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    selected = json.loads((D/'secret-example-state.json').read_text())
    seat = selected['audit']['seat']
    source = ROOT/'experiments/secret-hunter-response-y1-response-data'
    spec = next(x for x in json.loads((source/'config.json').read_text())['population']
                if x['name'] == selected['audit']['opponent'])
    own, other = load_deck(C/'deck.json'), load_deck(ROOT/spec['deck'])
    engine = Engine(own if seat == 1 else other, other if seat == 1 else own,
                    selected['audit']['seed'], max_turns=180)
    saved = D/'secret-replay-prefix.json'
    if saved.exists():
        prefix = json.loads(saved.read_text())['actions']
        for step in prefix:
            assert engine.step(step['player'], step['action']).accepted
    else:
        game = selected['state']['game_id']
        observations = {i: readlines(source/'games'/game/f'p{i}/observations.jsonl') for i in (1, 2)}
        cursor = {1: 0, 2: 0}; prefix = []
        while True:
            who, _ = engine.pending()
            entry = observations[who][cursor[who]]
            if who == seat and entry['state']['seq'] == selected['state']['seq']:
                break
            action = entry['action']
            assert engine.step(who, action).accepted and not engine.over
            prefix.append({'player': who, 'action': action}); cursor[who] += 1
        write(saved, {'audit': selected['audit'], 'seq': selected['state']['seq'],
                      'actions': prefix, 'public_state_sha256': public_key(selected['state'])})
    assert public_key(engine.view(seat)) == public_key(selected['state'])
    cfg = json.loads((C/'config.json').read_text()); records = []
    for arm, config in [('Y1', {**cfg, 'face_preference': False}), ('F2', cfg)]:
        branch = copy.deepcopy(engine); trace = []
        for _ in range(20):
            state = branch.view(seat)
            state.update(player=seat, seq=len(trace), game_id='secret-control-replay')
            state = with_public_history(state, [v for e in branch.events if (v := e.view(seat)) is not None])
            action, info = decide(state, config)
            assert legal(state, action) and not info.get('error')
            assert branch.step(seat, action).accepted and not branch.over
            trace.append({'action': action, 'reason': info['reason']})
            if action['type'] == 'end_turn':
                break
        else:
            raise AssertionError('Turn did not finish')
        endpoint = projection(branch.view(seat))
        reply = None
        state = branch.view(3-seat)
        for attacker in state['you']['board']:
            possible = {'type': 'attack', 'attacker': attacker['entity_id'],
                        'target': state['opponent']['hero']['entity_id']}
            if legal(state, possible):
                assert branch.step(3-seat, possible).accepted and not branch.over
                reply = possible
                break
        records.append({'candidate': arm, 'own_turn': trace, 'endpoint': endpoint,
                        'one_feasible_visible_attack': reply, 'after_reply': projection(branch.view(seat))})
    report = {'source': selected['audit'], 'public_state_sha256': public_key(selected['state']),
              'prefix_actions': len(prefix), 'branches': records, 'terminal_games': 0,
              'scope': 'One replayed own turn and one feasible visible attack. This is not a predicted opponent policy or a win-rate measurement.'}
    write(ROOT/args.out, report)
    finish(args.name, actual_short=len(prefix)+sum(len(r['own_turn'])+int(r['one_feasible_visible_attack'] is not None) for r in records), full_games=0)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
