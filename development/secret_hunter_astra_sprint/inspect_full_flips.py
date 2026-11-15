"""Read every completed paired flip, regressions first, without new games."""
import argparse
import json
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.tactical import digest


def describe(state, action):
    entities = {x['entity_id']: x for side in ('you', 'opponent')
                for x in state[side]['board'] + [state[side]['hero']]}
    entities.update({x['entity_id']: x for x in state['you']['hand']})
    return {k: entities[v].get('name', entities[v].get('card_id', 'hero'))
            if k in ('card', 'attacker', 'target') and v in entities else v
            for k, v in action.items()}


def main(batch, arm):
    db = ledger.connect(RUN)
    assert db.execute('select status from batches where id=?', (batch,)).fetchone()[0] == 'done'
    if batch.startswith('final-'):
        assert all(db.execute('select status from batches where id=?', (b,)).fetchone()[0] == 'done'
                   for b in ('final-core', 'final-guard'))
    report = json.loads((RUN / 'batches' / batch / 'report.json').read_text())
    flips = report['comparisons'][arm]['flips']
    cases = []
    for flip in sorted(flips, key=lambda r: (r['b_win'] - r['a_win'], r['seed'], r['opponent'], r['seat'])):
        logs = []
        for name, game_key in (('DARCL2', 'a_game'), (arm, 'b_game')):
            path = RUN / 'batches' / batch / name / 'games' / flip[game_key] / f"p{flip['seat']}/observations.jsonl"
            logs.append([json.loads(line) for line in path.read_text().splitlines()])
        first_state = next((i for i, (a, b) in enumerate(zip(*logs)) if digest(a['state']) != digest(b['state'])), None)
        first_action = next((i for i, (a, b) in enumerate(zip(*logs)) if a['action'] != b['action']), None)
        record = {**flip, 'first_public_state_difference_index': first_state,
                  'first_action_difference_index': first_action}
        if first_action is not None:
            a, b = (xs[first_action] for xs in logs)
            record.update(same_public_state=digest(a['state']) == digest(b['state']),
                          baseline_description=describe(a['state'], a['action']),
                          candidate_description=describe(b['state'], b['action']),
                          baseline=a, candidate=b,
                          baseline_next=logs[0][first_action + 1]['state'] if first_action + 1 < len(logs[0]) else None,
                          candidate_next=logs[1][first_action + 1]['state'] if first_action + 1 < len(logs[1]) else None)
        cases.append(record)
    result = {'batch': batch, 'candidate': arm, 'cases': cases,
              'scope': 'All completed paired flips, original-win regressions first. Next visible observation can include opponent actions. A deck change makes public states differ from the opening; differing entity IDs alone do not prove a tactical change.'}
    ledger.atomic(RUN / 'analysis' / f'{batch}-{arm}-flip-inspection.json', result)
    print(json.dumps([{**{k: v for k, v in r.items() if k not in ('baseline', 'candidate', 'baseline_next', 'candidate_next')},
                       'T': r.get('baseline', {}).get('state', {}).get('you', {}).get('max_mana')}
                      for r in cases], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('batch')
    parser.add_argument('arm')
    args = parser.parse_args()
    main(args.batch, args.arm)
