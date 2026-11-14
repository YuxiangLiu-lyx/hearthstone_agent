"""Check an executable learned policy against the same held-out terminal worlds."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from development.secret_hunter_long.cfqueue import connect
from development.secret_hunter_long.learn_tactical import confidence
from development.secret_hunter_long.study import RUN
from development.secret_hunter_mcgs import train


def summarize(pairs):
    groups = defaultdict(list)
    for source, baseline, candidate in pairs:
        groups[source['seed']].append(candidate['win'] - baseline['win'])
    rescued = sum(c['win'] > b['win'] for _, b, c in pairs)
    regressed = sum(c['win'] < b['win'] for _, b, c in pairs)
    return {
        'futures': len(pairs), 'source_seed_groups': len(groups),
        'roots': len({s['case'] for s, _, _ in pairs}),
        'baseline_wins': sum(b['win'] for _, b, _ in pairs),
        'candidate_wins': sum(c['win'] for _, _, c in pairs),
        'rescued': rescued, 'lost_old_wins': regressed, 'net': rescued - regressed,
        'positive_seed_groups': sum(any(x > 0 for x in xs) for xs in groups.values()),
        'root_turn_changed_roots': len({s['case'] for s, _, c in pairs if c['actions_changed']}),
        'root_turn_changed_futures': sum(bool(c['actions_changed']) for _, _, c in pairs),
        'root_turn_changed_actions': sum(c['actions_changed'] for _, _, c in pairs),
        'all_own_decisions': sum(c['own_decisions'] for _, _, c in pairs),
        'whole_continuation_policy_changed_actions': sum(c['policy_changed_actions'] for _, _, c in pairs),
        'terminal_gain': (rescued - regressed) / len(pairs),
        'gain_seed_cluster_95': confidence(groups),
    }


def run(batch, arm):
    learning = json.loads((RUN / f'tactical-learning-{batch}-{arm}.json').read_text())
    assert learning['passed_fixed_route_label_gate'], 'No accepted fixed rule to evaluate'
    candidate = learning['candidate']
    manifest = json.loads((RUN / 'tactical-sources' / f'manifest-{batch}-{arm}.json').read_text())
    db = connect()
    pairs = []
    for case in manifest['cases']:
        source = json.loads((RUN / 'tactical-sources' / (case + '.json')).read_text())
        if source['split'] != 'validation':
            continue
        for sample in range(manifest['samples']):
            outcomes = []
            for suffix in ('baseline', 'policy-' + candidate):
                row = db.execute('select * from cf_jobs where key=?', (f'{case}-w{sample}-{suffix}',)).fetchone()
                assert row and row['status'] == 'done', (case, sample, suffix)
                result = json.loads(Path(row['result_path']).read_text())
                assert result['terminal'] and result['winner'] in (1, 2) and not result.get('error')
                outcomes.append(result)
            baseline, actual = outcomes
            assert actual['fallbacks'] == 0
            assert baseline['root_digest'] == actual['root_digest']
            assert baseline['audit_hidden'] == actual['audit_hidden']
            assert baseline['prefix_verified_steps'] == actual['prefix_verified_steps']
            if sample == 0:
                assert baseline['win'] == source['source_score']
            pairs.append((source, baseline, actual))
    summary = summarize(pairs)
    result = {
        'batch': batch, 'parent': arm, 'candidate': candidate,
        'rule': learning['rule'], 'actual_policy': summary,
        'original_world': summarize([p for p in pairs if p[1]['sample'] == 0]),
        'by_family': {family: summarize([p for p in pairs if p[0]['opponent_spec']['group'] == family])
                      for family in sorted({p[0]['opponent_spec']['group'] for p in pairs})},
        'by_actual_first': {str(first): summarize([p for p in pairs if p[0]['actual_first'] == first])
                            for first in (True, False)},
        'passed_actual_policy_gate': summary['net'] >= 3 and summary['positive_seed_groups'] >= 3
                                     and summary['root_turn_changed_roots'] > 0,
        'gate': 'Predeclared fixed-rule gate repeated for actual stateless continuations: net >=3, >=3 positive source groups, actual action changes and all jobs terminal without errors.',
        'scope': 'Conditional early-root holdout, with paired hidden worlds and fixed original hidden hands. Candidate runs at every subsequent decision; these are not natural-frequency full games. Independent full-game testing remains required.',
    }
    train.atomic(RUN / f'tactical-policy-{batch}-{arm}.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    parser.add_argument('--arm', required=True)
    args = parser.parse_args()
    run(args.batch, args.arm)
