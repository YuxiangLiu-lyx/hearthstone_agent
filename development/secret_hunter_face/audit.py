"""Compare public decisions on stratified, already-used development observations."""
import argparse
import collections
import json
import sys
from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.accounting import reserve, finish


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', default='F1', choices=['F1', 'F2'])
    args = parser.parse_args()
    name = 'face-preference-public-audit-'+args.candidate
    reserve(name, short=500, seconds=300)
    candidate = ROOT/'development/secret_hunter_face/candidates'/args.candidate
    sys.path.insert(0, str(candidate/'scripts'))
    from program_policy import decide
    from action_validator import legal
    from face_preference import ordinary_small_minion, pressure_window
    config = json.loads((candidate/'config.json').read_text())
    baseline = {**config, 'face_preference': False}
    source = ROOT/'experiments/secret-hunter-response-y1-response-data'
    counts = collections.Counter(); buckets = collections.defaultdict(list)
    rows = sorted(readlines(source/'results.jsonl'), key=lambda r: (r['opponent'], r['seed'], r['seat']))
    for row in rows:
        assert 960000 <= row['seed'] < 960040
        records = readlines(source/'games'/row['game']/f"p{row['seat']}/observations.jsonl")
        for record in records:
            state, action = record['state'], record['action']
            if state['phase'] != 'main' or action['type'] != 'attack':
                continue
            counts['all_attack_decisions'] += 1
            enemy = state['opponent']
            if action['target'] == enemy['hero']['entity_id']:
                counts['face_attacks'] += 1
                continue
            counts['minion_attacks'] += 1
            face = {**action, 'target': enemy['hero']['entity_id']}
            if not legal(state, face):
                continue
            counts['trade_with_legal_face_alternative'] += 1
            target = next(m for m in enemy['board'] if m['entity_id'] == action['target'])
            ordinary = ordinary_small_minion(target)
            safe = pressure_window(state, config)
            if ordinary and safe:
                counts['safe_ordinary_trade_opportunities'] += 1
            key = (row['opponent'], row['seat'] == row['first_player'], bool(row['score']), ordinary and safe)
            if len(buckets[key]) < 2:
                buckets[key].append({'state': state, 'recorded_action': action,
                                     'audit': {k: row[k] for k in ('opponent', 'seed', 'seat', 'first_player', 'score')},
                                     'ordinary_safe': ordinary and safe})
    selected = [entry for key in sorted(buckets) for entry in buckets[key]]
    results = []
    for entry in selected:
        state = entry['state']
        old, old_info = decide(state, baseline)
        new, new_info = decide(state, config)
        assert legal(state, old) and legal(state, new)
        assert not old_info.get('error') and not new_info.get('error')
        hero = state['opponent']['hero']['entity_id']
        results.append({**entry, 'Y1': {'action': old, 'info': old_info},
                        args.candidate: {'action': new, 'info': new_info}, 'changed': old != new,
                        'trade_to_face': old['type'] == new['type'] == 'attack' and old['target'] != hero and new['target'] == hero,
                        'same_attacker_trade_to_face': old['type'] == new['type'] == 'attack' and old['target'] != hero and new['target'] == hero and old['attacker'] == new['attacker'],
                        'recorded_baseline_reproduced': old == entry['recorded_action']})
    D = ROOT/'docs/secret_hunter_face'
    with (D/(args.candidate.lower()+'-public-decisions.jsonl')).open('w') as output:
        for row in results:
            output.write(json.dumps(row)+'\n')
    report = {'candidate': args.candidate, 'source_games': len(rows), 'inventory': dict(counts), 'selected': len(results),
              'source_seed_groups': len({r['audit']['seed'] for r in results}),
              'changed': sum(r['changed'] for r in results),
              'trade_to_face': sum(r['trade_to_face'] for r in results),
              'same_attacker_trade_to_face': sum(r['same_attacker_trade_to_face'] for r in results),
              'recorded_baseline_reproduced': sum(r['recorded_baseline_reproduced'] for r in results),
              'illegal': 0, 'policy_errors': 0, 'full_games': 0,
              'selection': 'Up to two per opponent, actual turn order, source outcome and safe-ordinary category. Audit metadata is never a policy input.',
              'limitation': 'Selected historical trade states, not an unbiased policy distribution. Changed decisions are not proven better and no win-rate estimate is made.'}
    write(D/(args.candidate.lower()+'-audit.json'), report)
    finish(name, actual_short=2*len(results), full_games=0)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
