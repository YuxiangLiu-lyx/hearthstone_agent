"""Strict paired seed-group inference and prespecified promotion gates."""
import json

from development.secret_hunter_program.common import ROOT, readlines, write, quantiles
from development.teacher_eval.compare import compare, index, paired

D = ROOT / 'docs/secret_hunter_face_validation'


def folder(arm, population):
    return ROOT / 'experiments' / f'secret-hunter-face-validation-{arm.lower()}-{population}'


def main():
    reports = {}
    for population in ('core', 'guardrail'):
        left, right = [folder(arm, population) for arm in ('Y1', 'F2')]
        rows = [readlines(p / 'results.jsonl') for p in (left, right)]
        report = compare(left, right)
        mappings = [index(rs) for rs in rows]
        assert all(mappings[0][k]['first_player'] == mappings[1][k]['first_player'] for k in mappings[0])
        report['by_opponent'] = {
            opponent: paired(*[[r for r in rs if r['opponent'] == opponent] for rs in rows])
            for opponent in sorted({r['opponent'] for r in rows[0]})}
        report['by_actual_first'] = {}
        for first in (True, False):
            # Normalize physical seat after filtering on actual turn order. Every
            # seed retains one observation per opponent in this subgroup.
            selected = [[{**r, 'seat': 1} for r in rs if (r['seat'] == r['first_player']) == first] for rs in rows]
            report['by_actual_first'][str(first)] = paired(*selected)
        report['reliability'] = {}
        for arm, rs in zip(('Y1', 'F2'), rows):
            report['reliability'][arm] = {
                'games': len(rs), 'own_decisions': sum(len(r['decision_times']) for r in rs),
                'illegal_both_players': sum(sum(r['result']['illegal_counts'].values()) for r in rs),
                'timeouts_both_players': sum(sum(r['result']['timeouts'].values()) for r in rs),
                'policy_errors': sum(len(r['policy_errors']) for r in rs),
                'opponent_errors': sum(len(r['opponent_errors']) for r in rs),
                'fallbacks': sum(r['fallbacks'] for r in rs), 'over_2s': sum(r['over_2s'] for r in rs),
                'public_input_violations': sum(not r['public_only'] for r in rs),
                'policy_latency_s': quantiles([t for r in rs for t in r['decision_times']])}
        report['outcome_changes'] = [
            {'opponent': k[0], 'seed': k[1], 'seat': k[2],
             'actual_first': mappings[0][k]['first_player'] == k[2],
             'Y1_score': mappings[0][k]['score'], 'F2_score': mappings[1][k]['score'],
             'Y1_game': mappings[0][k]['game'], 'F2_game': mappings[1][k]['game']}
            for k in sorted(mappings[0]) if mappings[0][k]['score'] != mappings[1][k]['score']]
        reports[population] = report
    plan = json.loads((D / 'plan.json').read_text())
    thresholds = plan['promotion_gates']
    primary = reports['core']['hard_family_macro']
    errors = ('illegal_both_players', 'timeouts_both_players', 'policy_errors', 'opponent_errors',
              'fallbacks', 'over_2s', 'public_input_violations')
    gates = {
        'primary_gain': primary['gain'] >= thresholds['primary_gain_at_least'],
        'primary_positive_interval': primary['gain_seed_cluster_95'][0] > thresholds['primary_paired_95_lower_above'],
        'family_regression': all(reports['core']['by_group'][g]['gain'] >= thresholds['minimum_family_gain']
                                 for g in ('astra', 'bot2')),
        'guardrail_overall': reports['guardrail']['all']['gain'] >= thresholds['minimum_guardrail_overall_gain'],
        'guardrail_opponents': all(r['gain'] >= thresholds['minimum_guardrail_opponent_gain'] - 1e-12
                                  for r in reports['guardrail']['by_opponent'].values()),
        'normal_reliability': all(not r[k] for report in reports.values()
                                  for r in report['reliability'].values() for k in errors)}
    reports['decision'] = {'gates': gates, 'performance_gates_pass': all(gates.values()),
                           'release_status': 'Requires separate complete CLI and artifact integrity checks.',
                           'scope': 'Frozen local proxy pools; no claim of real Astra performance or guaranteed improvement.'}
    write(D / 'paired.json', reports)
    print(json.dumps({population: {k: reports[population][k] for k in ('all', 'by_actual_first')}
                      for population in ('core', 'guardrail')}, indent=2))
    print(json.dumps({'primary': primary, 'decision': reports['decision']}, indent=2))


if __name__ == '__main__':
    main()
