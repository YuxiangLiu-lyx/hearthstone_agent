"""Verify frozen boundaries, scheduled pairs, packaged bytes, reliability and accounting."""
import hashlib
import json
from pathlib import Path
import zipfile

import hs_arena
from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check
from development.secret_hunter_program.common import ROOT, sha, readlines, write
from development.teacher_eval.run import snapshot
from .analyze import D, folder


def main():
    frozen = json.loads((D / 'freeze.json').read_text())
    plan = json.loads((D / 'plan.json').read_text())
    assert sha(D / 'plan.json') == frozen['plan_sha256']
    assert sha(ROOT / frozen['old_budget_path']) == frozen['old_budget_sha256']
    protected = json.loads((ROOT / 'docs/secret_hunter_response/protected.json').read_text())
    assert all(sha(ROOT / path) == digest for path, digest in protected.items())
    engine_files = json.loads((ROOT / 'docs/secret_hunter_program/runtime.json').read_text())['installed_files']
    engine = Path(hs_arena.__file__).parent
    assert all(sha(engine / path) == digest for path, digest in engine_files.items())
    for arm, path in frozen['source_paths'].items():
        check(ROOT / path)
        assert fingerprint(ROOT / path) == frozen['source_hashes'][arm]
        assert sha(ROOT / path / 'deck.json') == frozen['deck_sha256']
    assert fingerprint(ROOT / 'development/secret_hunter_face/candidates/F2') == frozen['source_hashes']['F2']
    manifest = json.loads((ROOT / 'dist/secret-hunter-krush-face-f2.manifest.json').read_text())
    assert sha(ROOT / frozen['zip']) == frozen['zip_sha256'] == manifest['zip_sha256']
    with zipfile.ZipFile(ROOT / frozen['zip']) as archive:
        prefix = Path(manifest['extracted']).name + '/'
        assert set(archive.namelist()) == {prefix + name for name in manifest['files']}
        for filename, digest in manifest['files'].items():
            assert hashlib.sha256(archive.read(prefix + filename)).hexdigest() == digest
            assert sha(ROOT / manifest['extracted'] / filename) == digest
    all_rows, runs = [], {}
    for population, schedule in plan['schedules'].items():
        popfile = ROOT / f'development/teacher_eval/{population}.json'
        pop = json.loads(popfile.read_text())
        assert sha(popfile) == frozen['populations'][population]['sha256']
        assert snapshot(pop) == frozen['populations'][population]['opponents']
        for arm in ('Y1', 'F2'):
            path = folder(arm, population)
            config = json.loads((path / 'config.json').read_text())
            rows = readlines(path / 'results.jsonl')
            expected = {(o['name'], seed, seat) for o in pop
                        for seed in range(schedule['start'], schedule['start'] + schedule['seeds']) for seat in (1, 2)}
            assert len(rows) == len(expected) == config['planned_games']
            assert {(r['opponent'], r['seed'], r['seat']) for r in rows} == expected
            assert config['candidate_sha256'] == frozen['source_hashes'][arm]
            assert config['freeze_sha256'] == sha(D / 'freeze.json')
            assert all(r['public_only'] and not r.get('harness_error') and not r['policy_errors'] and not r['opponent_errors']
                       and not r['course_failure'] and not r['result']['reason'].startswith('forfeit') for r in rows)
            all_rows.extend(rows)
            runs[str(path.relative_to(ROOT))] = {'games': len(rows), 'results_sha256': sha(path / 'results.jsonl')}
    normal = {'games': len(all_rows), 'own_decisions': sum(len(r['decision_times']) for r in all_rows),
              'illegal_both_players': sum(sum(r['result']['illegal_counts'].values()) for r in all_rows),
              'timeouts_both_players': sum(sum(r['result']['timeouts'].values()) for r in all_rows),
              'fallbacks': sum(r['fallbacks'] for r in all_rows), 'over_2s': sum(r['over_2s'] for r in all_rows)}
    assert not any(normal[k] for k in ('illegal_both_players', 'timeouts_both_players', 'fallbacks', 'over_2s'))
    runtime = json.loads((D / 'runtime-f2.json').read_text())
    assert runtime['illegal'] == runtime['over_2s'] == 0
    faults = {}
    for arm in ('y1', 'f2'):
        fault = json.loads((D / f'{arm}-isolated-stale.json').read_text())
        assert len(fault['cases']) == 8
        assert all(r['refresh_required'] and not r['stale_action'] and not r['outer_timeout'] and r['elapsed_s'] < 2 for r in fault['cases'])
        faults[arm] = {'cases': 8, 'max_s': fault['latency_s']['max']}
    client = json.loads((D / 'client-audit.json').read_text())
    assert client['games'] == 2 and client['relay_deviations'] == 0
    assert all(not r['worker_errors'] and not r['fallbacks'] and not any(r['result']['illegal_counts'].values())
               and not any(r['result']['timeouts'].values()) for r in client['reports'])
    cases = json.loads((D / 'cases.json').read_text())
    repeated = json.loads((D / 'cases-repeated.json').read_text())
    assert cases == repeated and cases['reproduced_terminal_outcomes'] == 6
    ledger = json.loads((D / 'budget.json').read_text())
    assert all(r['status'] == 'completed' for r in ledger['runs'])
    totals = {'full_attempts_charged': sum(r['full'] for r in ledger['runs']),
              'short_charged': sum(r['short'] for r in ledger['runs']),
              'experiment_wall_s_sum': sum(r['elapsed_s'] for r in ledger['runs'])}
    assert totals['full_attempts_charged'] <= ledger['limits']['full_games']
    assert totals['short_charged'] <= ledger['limits']['short_branches']
    assert totals['experiment_wall_s_sum'] <= ledger['limits']['experiment_seconds']
    prior = json.loads((ROOT / 'docs/secret_hunter_winrate/checkpoint.json').read_text())['used_seed_values']
    new = set(range(985000, 985040)) | set(range(986000, 986010)) | {987000, 987001}
    assert not set(prior) & new
    paired = json.loads((D / 'paired.json').read_text())
    promoted = paired['decision']['performance_gates_pass']
    report = {'protected_inherited_files': len(protected), 'installed_engine_files': len(engine_files),
              'old_budget_unchanged': True, 'ordered_decks_and_frozen_policies_unchanged': True,
              'zip_sha256': frozen['zip_sha256'], 'normal': normal, 'budget': totals,
              'runtime_cases': runtime['cases'], 'isolated_faults': faults,
              'client_games': client['games'], 'client_decisions': client['decisions'],
              'replayed_game_executions': 12, 'distinct_recorded_games': 6,
              'reliability_pass': True, 'promoted': promoted, 'recommended': 'F2' if promoted else 'Y1', 'runs': runs}
    write(D / 'integrity.json', report)
    write(D / 'archive.json', {'parent_archive': 'docs/secret_hunter_face/archive.json',
        'Y1': {'status': 'recommended_baseline', 'source_hash': frozen['source_hashes']['Y1']},
        'F2': {'parent': 'F1', 'status': 'rejected_after_frozen_validation', 'source_hash': frozen['source_hashes']['F2'],
               'primary_gain': paired['core']['hard_family_macro']['gain'], 'evidence': 'docs/secret_hunter_face_validation/paired.json',
               'next_hypothesis': 'Limit aggression preferences to comparable attack allocations after development; separately value persistent pressure and remove abrupt endpoint gating. This is untested and would require new development data and another untouched holdout.'}})
    write(D / 'checkpoint.json', {'parent_checkpoint': 'docs/secret_hunter_face/checkpoint.json',
        'seed_history_parent': 'docs/secret_hunter_winrate/checkpoint.json', 'new_used_seed_values': sorted(new),
        'budget': 'docs/secret_hunter_face_validation/budget.json', 'old_budget_preserved': frozen['old_budget_sha256'],
        'no_policy_tuning_on_validation_seeds': True, 'recommended_baseline': report['recommended'],
        'candidate_hashes': frozen['source_hashes'], 'next': 'F2 is rejected. These validation seeds must become development if used to design another candidate.'})
    print(json.dumps({k: v for k, v in report.items() if k != 'runs'}, indent=2))


if __name__ == '__main__':
    main()
