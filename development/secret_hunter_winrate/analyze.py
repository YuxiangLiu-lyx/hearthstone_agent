"""Analyze the frozen follow-up and retain every paired outcome and decision change."""
import argparse
import json
import statistics
from development.secret_hunter_program.common import ROOT, write, readlines
from development.teacher_eval.compare import compare, paired, index
from development.secret_hunter_response.counterfactual import public_key

D = ROOT/'docs/secret_hunter_winrate'
E = ROOT/'experiments'


def path(arm, population):
    return E/f'secret-hunter-winrate-{arm.lower()}-final-{population}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics-only', action='store_true', help='Use committed result rows without ignored match logs')
    parser.add_argument('--out', help='Optional output JSON path')
    args = parser.parse_args()
    out = {'summaries': {}, 'paired': {}, 'development': {}}
    for arm in ('W1', 'W2', 'W3'):
        out['development'][arm] = json.loads((D/f'{arm.lower()}-development.json').read_text())
    changes = []; activations = []
    for population in ('core', 'guard'):
        folders = [path(arm, population) for arm in ('Y1', 'W3')]
        rows = [readlines(p/'results.jsonl') for p in folders]
        result = compare(*folders)
        for p, arm in zip(folders, ('Y1', 'W3')):
            out['summaries'][arm+'-'+population] = json.loads((p/'summary.json').read_text())
        result['by_opponent'] = {n: paired(*[[r for r in rs if r['opponent'] == n] for rs in rows])
                                 for n in sorted({r['opponent'] for r in rows[0]})}
        result['by_actual_first'] = {str(first): paired(*[
            [{**r, 'seat': 1} for r in rs if (r['seat'] == r['first_player']) == first]
            for rs in rows]) for first in (True, False)}
        out['paired'][population] = result
        a, b = map(index, rows)
        for key in ([] if args.metrics_only else sorted(a)):
            records = [readlines(p/'games'/r['game']/f"p{r['seat']}/observations.jsonl")
                       for p, r in zip(folders, (a[key], b[key]))]
            active = [r for r in records[1] if r['info'].get('turn_search', {}).get('standalone_juggler_comparison')]
            if active:
                activations.append({'population': population, 'key': key,
                                    'decisions': len(active), 'score': b[key]['score']})
            first = next(((x, y) for x, y in zip(*records) if x['action'] != y['action']), None)
            if first:
                x, y = first
                changes.append({'population': population, 'key': key,
                                'same_public_start': public_key(x['state']) == public_key(y['state']),
                                'scores': [a[key]['score'], b[key]['score']],
                                'baseline': x, 'candidate': y})
    primary = out['paired']['core']['hard_family_macro']
    out['coverage'] = {'activated_decisions': sum(r['decisions'] for r in activations),
                       'activated_games': len(activations),
                       'changed_action_traces': len(changes),
                       'changed_first_actions_with_gate_active': sum(bool(r['candidate']['info'].get('turn_search', {}).get('standalone_juggler_comparison')) for r in changes),
                       'other_first_divergences_with_different_bounded_search': sum(not r['candidate']['info'].get('turn_search', {}).get('standalone_juggler_comparison', False) for r in changes),
                       'changed_outcomes': out['paired']['core']['all']['a_only_wins'] + out['paired']['core']['all']['b_only_wins'],
                       'activations': activations,
                       'changed_keys': [{k: v for k, v in r.items() if k not in ('baseline', 'candidate')} for r in changes]}
    if args.metrics_only:
        out['coverage'] = {'not_recomputed': 'Metrics-only mode uses committed result rows; consult the archived full audit for decision traces.'}
    out['conditional_bow'] = json.loads((D/'continuation-bow.json').read_text())
    out['conditional_bow'] = {'source_case': 33, 'n_per_plan': 12,
                              'wins': {p['id']: sum(x['win'] for x in p['outcomes']) for p in out['conditional_bow']['plans']},
                              'purpose': 'Post-freeze conditional diagnosis; not full-game generalization evidence.'}
    out['decision'] = {'recommendation': 'Retain Y1; W3 is a research artifact.',
                       'promotion': False, 'reason': 'No observed gain in fresh paired wins or the family-balanced primary metric.',
                       'primary_gain': primary['gain'], 'paired_seed_interval': primary['gain_seed_cluster_95'],
                       'interval_caveat': 'A degenerate bootstrap interval from identical observed outcomes does not establish equivalence or eliminate uncertainty on other seeds.',
                       'final_used_for_tuning': False}
    destination = ROOT/args.out if args.out else D/('metrics-only.json' if args.metrics_only else 'final-results.json')
    write(destination, out)
    if not args.metrics_only:
        write(D/'final-decision-changes.json', changes)
    print(json.dumps({'primary': primary, 'coverage': {k: v for k, v in out['coverage'].items() if k not in ('activations', 'changed_keys')},
                      'conditional': out['conditional_bow'], 'decision': out['decision']}, indent=2))


if __name__ == '__main__':
    main()
