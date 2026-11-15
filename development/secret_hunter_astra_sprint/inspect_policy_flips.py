"""Reconstruct recorded prefixes to inspect flips; no new policy rollouts."""
import argparse
import json
import random
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.tactical import setup, restore, digest


def main(arm):
    setup()
    report = json.loads((RUN / f'{arm}-policy-continuations.json').read_text())
    cases = []
    for row in report['rows']:
        if not row['delta']:
            continue
        source = json.loads((RUN / 'tactical-sources' / (row['case'] + '.json')).read_text())
        old = json.loads((RUN / 'tactical-labels' / f"{row['case']}-w{row['world']}-baseline.json").read_text())
        engine, _ = restore(source)
        if row['world']:
            rng = random.Random(81600000 + source['seed'] * 17 + row['world'])
            for seat in (1, 2):
                rng.shuffle(engine.player(seat).deck)
            engine.game.random.seed(91700000 + source['seed'] * 31 + row['world'])
        first = row['first_difference']
        for event in old['trace'][:first['step']]:
            active, _ = engine.pending()
            assert active == event['seat']
            assert digest(engine.view(active)) == event['state_digest']
            assert engine.step(active, event['action']).accepted
        state = engine.view(source['seat'])
        assert digest(state) == first['state_digest']
        entities = {x['entity_id']: x for side in ('you', 'opponent')
                    for x in state[side]['board'] + [state[side]['hero']]}
        entities.update({x['entity_id']: x for x in state['you']['hand']})
        def describe(action):
            return {**action, 'entities': {k: entities[v].get('name', entities[v].get('card_id', 'hero'))
                    for k, v in action.items() if k in ('card', 'attacker', 'target') and v in entities}}
        cases.append({**row, 'T': state['you']['max_mana'], 'state': state,
                      'baseline_description': describe(first['baseline']),
                      'candidate_description': describe(first['candidate'])})
    result = {'candidate': arm, 'cases': cases,
              'scope': 'Replay existing recorded actions only up to first divergence; no new alternatives or terminal continuations. Source groups and worlds retain their existing seen status.'}
    ledger.atomic(RUN / f'{arm}-flip-inspection.json', result)
    print(json.dumps([{k: r[k] for k in ('case', 'world', 'delta', 'T', 'baseline_description', 'candidate_description')}
                      for r in cases], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', required=True)
    main(parser.parse_args().arm)
