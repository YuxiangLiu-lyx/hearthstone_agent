"""Read-only diagnosis of frozen validation traces; never tune on these seeds."""
from collections import Counter, defaultdict
import gzip
import json

from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.counterfactual import public_key, projection
from development.teacher_eval.compare import index
from .analyze import D, folder


def describe(state, action):
    entities = {entity['entity_id']: entity['name'] for side in ('you', 'opponent')
                for entity in [state[side]['hero']] + state[side]['board'] + state[side].get('hand', [])}
    return {**action, **{key + '_name': entities.get(action[key]) for key in ('card', 'attacker', 'target') if key in action}}


def category(state, old, new):
    hero = state['opponent']['hero']['entity_id']
    if old['type'] == new['type'] == 'attack':
        if old['target'] != hero and new['target'] == hero:
            return 'trade_to_face'
        if old['target'] == hero and new['target'] != hero:
            return 'face_to_trade'
        return 'other_attack_change'
    if old['type'] == 'play_card' and new['type'] == 'hero_power':
        card = next(c for c in state['you']['hand'] if c['entity_id'] == old['card'])
        return 'minion_to_hero_power' if card['type'] == 'MINION' else 'spell_to_hero_power'
    return old['type'] + '_to_' + new['type']


def main():
    population = 'core'
    arms = {arm: index(readlines(folder(arm, population) / 'results.jsonl')) for arm in ('Y1', 'F2')}
    counts = {arm: Counter() for arm in arms}
    differences, mismatches = [], []
    for key in sorted(arms['Y1']):
        records = {}
        for arm in arms:
            row = arms[arm][key]
            records[arm] = readlines(folder(arm, population) / 'games' / row['game'] / f'p{row["seat"]}/observations.jsonl')
            for entry in records[arm]:
                state, action = entry['state'], entry['action']
                if action['type'] == 'attack':
                    counts[arm]['attacks'] += 1
                    counts[arm]['face_attacks' if action['target'] == state['opponent']['hero']['entity_id'] else 'minion_attacks'] += 1
                if state['phase'] == 'main' and state['you']['max_mana'] == 2 and action['type'] == 'hero_power':
                    counts[arm]['two_mana_hero_power'] += 1
        for old, new in zip(records['Y1'], records['F2']):
            if public_key(old['state']) != public_key(new['state']):
                mismatches.append({'key': key, 'seq': old['state']['seq'], 'reason': 'Public state diverged before first own-action difference.'})
                break
            if old['action'] == new['action']:
                continue
            state = old['state']
            differences.append({'opponent': key[0], 'seed': key[1], 'seat': key[2],
                'actual_first': key[2] == arms['Y1'][key]['first_player'],
                'Y1_score': arms['Y1'][key]['score'], 'F2_score': arms['F2'][key]['score'],
                'max_mana': state['you']['max_mana'], 'category': category(state, old['action'], new['action']),
                'projection': projection(state), 'public_state_sha256': public_key(state),
                'state': state, 'Y1': {'action': old['action'], 'description': describe(state, old['action']), 'info': old['info']},
                'F2': {'action': new['action'], 'description': describe(state, new['action']), 'info': new['info']}})
            break
    categories = defaultdict(Counter)
    for record in differences:
        bucket = categories[record['category']]
        bucket['games'] += 1
        bucket['F2_only_wins'] += record['F2_score'] > record['Y1_score']
        bucket['Y1_only_wins'] += record['Y1_score'] > record['F2_score']
        bucket['early_2_to_4_mana'] += 2 <= record['max_mana'] <= 4
    for counts_arm in counts.values():
        counts_arm['face_attack_fraction'] = counts_arm['face_attacks'] / counts_arm['attacks']
    report = {'games_per_arm': len(arms['Y1']), 'attacks': counts, 'first_action_differences': len(differences),
              'categories': dict(categories), 'public_state_mismatches_before_own_difference': mismatches,
              'scope': 'Post-hoc descriptive trace diagnosis. The full frozen policies differ; a first-action category is not an isolated causal effect.'}
    write(D / 'behavior.json', report)
    # Selected own observations contain only legally visible information. Outcomes,
    # seed and proxy identity are separate audit labels, never policy features.
    with (D / 'first-differences.jsonl.gz').open('wb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as archive:
            for record in differences:
                archive.write((json.dumps(record) + '\n').encode())
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
