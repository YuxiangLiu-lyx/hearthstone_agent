"""Audit frozen code, raw paired results, installed engine, client relay and budget."""
import json
from pathlib import Path
import zipfile
from development.secret_hunter_program.common import ROOT, sha, readlines, write
from development.secret_hunter_program.relay_audit import audit
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
from development.secret_hunter_dgm.deck_guard import check

D = ROOT/'docs/secret_hunter_winrate'


def main():
    inherited = ROOT/'docs/secret_hunter_response'
    protected = json.loads((inherited/'protected.json').read_text())
    assert all(sha(ROOT/p) == digest for p, digest in protected.items())
    import hs_arena
    engine = Path(hs_arena.__file__).parent
    engine_files = json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text())['installed_files']
    assert all(sha(engine/p) == digest for p, digest in engine_files.items())
    parent_freeze = json.loads((inherited/'final-freeze.json').read_text())
    for arm, digest in parent_freeze['source_hashes'].items():
        assert fingerprint(ROOT/'development/secret_hunter_response/candidates'/arm) == digest
    for pop, record in json.loads((inherited/'freeze.json').read_text())['populations'].items():
        file = ROOT/f'development/teacher_eval/{pop}.json'
        assert sha(file) == record['sha256'] and snapshot(json.loads(file.read_text())) == record['opponents']
    frozen = json.loads((D/'final-freeze.json').read_text())
    assert sha(D/'plan.json') == frozen['plan_sha256']
    for arm, path in frozen['source_paths'].items():
        check(ROOT/path)
        assert fingerprint(ROOT/path) == frozen['source_hashes'][arm]
    archive = json.loads((D/'archive.json').read_text())
    for arm, record in archive.items():
        candidate = ROOT/'development/secret_hunter_winrate/candidates'/arm
        assert fingerprint(candidate) == record['source_hash']
        check(candidate)
    manifest = json.loads((ROOT/'dist/secret-hunter-krush-winrate-w3.manifest.json').read_text())
    assert sha(ROOT/manifest['zip']) == manifest['zip_sha256']
    assert fingerprint(ROOT/manifest['extracted']) == frozen['source_hashes']['W3']
    with zipfile.ZipFile(ROOT/manifest['zip']) as z:
        assert len(z.infolist()) == len(manifest['files'])
        for info in z.infolist():
            assert Path(info.filename).suffix in ('.json', '.py', '.md')
            assert not any(p in info.filename for p in ('scratch/', 'game/', '__pycache__', 'offline'))
        assert sum(i.file_size for i in z.infolist()) < 10_000_000
    rows = []; runs = {}
    patterns = ('secret-hunter-response-winrate-*-dev', 'secret-hunter-winrate-*-final-*')
    for pattern in patterns:
        for folder in sorted((ROOT/'experiments').glob(pattern)):
            rs = readlines(folder/'results.jsonl')
            config = json.loads((folder/'config.json').read_text())
            expected = {(o['name'], s, seat) for o in config['population']
                        for s in range(config['start'], config['start']+config['seeds']) for seat in (1, 2)}
            assert {(r['opponent'], r['seed'], r['seat']) for r in rs} == expected
            assert len(rs) == config['planned_games'] == len(expected)
            assert all(r['public_only'] and not r.get('harness_error') and not r['policy_errors'] for r in rs)
            assert config['candidate_sha256'] == fingerprint(ROOT/config['candidate'])
            rows += rs
            runs[str(folder.relative_to(ROOT))] = {'games': len(rs), 'results_sha256': sha(folder/'results.jsonl')}
    normal = {'games': len(rows), 'own_decisions': sum(len(r['decision_times']) for r in rows),
              'illegal_both_players': sum(sum(r['result']['illegal_counts'].values()) for r in rows),
              'timeouts_both_players': sum(sum(r['result']['timeouts'].values()) for r in rows),
              'fallbacks': sum(r['fallbacks'] for r in rows), 'over_2s': sum(r['over_2s'] for r in rows)}
    assert not any(normal[k] for k in ('illegal_both_players', 'timeouts_both_players', 'fallbacks', 'over_2s'))
    clients = [audit(p, 1) for p in sorted((ROOT/'experiments/secret-hunter-winrate-client').glob('g_*'))]
    assert len(clients) == 2
    assert all(not r['worker_errors'] and not r['relay_deviations'] and not r['fallbacks'] for r in clients)
    assert all(not any(r['result']['illegal_counts'].values()) and not any(r['result']['timeouts'].values()) for r in clients)
    client = {'games': 2, 'decisions': sum(r['decisions'] for r in clients),
              'relay_deviations': sum(r['relay_deviations'] for r in clients), 'reports': clients,
              'scope': 'No-model official local client against existing Greedy; not a host-model evaluation.'}
    write(D/'client-audit.json', client)
    runtime = json.loads((D/'runtime-release.json').read_text())
    fault = json.loads((inherited/'winrate-release-isolated-stale.json').read_text())
    assert runtime['illegal'] == runtime['over_2s'] == 0
    assert all(r['refresh_required'] and not r['stale_action'] and not r['outer_timeout'] and r['elapsed_s'] < 2 for r in fault['cases'])
    budget = json.loads((inherited/'budget.json').read_text())
    assert all(r['status'] != 'reserved' for r in budget['runs'])
    totals = {'full_attempts_charged': sum(r['full'] for r in budget['runs']),
              'short_charged': sum(r['short'] for r in budget['runs']),
              'experiment_wall_s_sum': sum(r['elapsed_s'] for r in budget['runs'])}
    assert totals['full_attempts_charged'] <= 16000 and totals['short_charged'] <= 80000
    assert totals['experiment_wall_s_sum'] <= 21600
    used = set(json.loads((inherited/'checkpoint.json').read_text())['used_seed_values'])
    new = set(range(981000, 981040)) | set(range(982000, 982002)) | set(range(983000, 983012)) | set(range(984000, 984002))
    assert not used & new
    report = {'protected_inherited_files': len(protected), 'installed_engine_files': len(engine_files),
              'all_frozen_policies_and_decks_unchanged': True, 'new_seed_blocks_disjoint': True,
              'normal': normal, 'budget': totals, 'artifact': manifest,
              'client': {k: v for k, v in client.items() if k != 'reports'},
              'runtime_cases': runtime['cases'], 'isolated_stale_cases': len(fault['cases']),
              'reliability_pass': True, 'runs': runs}
    write(D/'integrity.json', report)
    archive['W3']['status'] = 'stepping_stone_not_promoted'
    for arm in archive:
        archive[arm]['development'] = f'experiments/secret-hunter-response-winrate-{arm.lower()}-dev'
    archive['W3']['final'] = ['experiments/secret-hunter-winrate-w3-final-core', 'experiments/secret-hunter-winrate-w3-final-guard']
    write(D/'archive.json', archive)
    write(D/'checkpoint.json', {'parent_checkpoint': 'docs/secret_hunter_response/checkpoint.json',
        'archive': 'docs/secret_hunter_winrate/archive.json', 'budget': 'docs/secret_hunter_response/budget.json',
        'used_seed_values': sorted(used | new), 'final_opened': True, 'full_game_budget_remaining': 16000-totals['full_attempts_charged'],
        'recommended_baseline': 'Y1', 'candidate_hashes': {k: v['source_hash'] for k, v in archive.items()},
        'next_hypothesis': 'Admit complete random development sequences with equal baseline/alternative coverage before broadening reply evaluation. The narrow W3 fix changed only one first action in the 480-game final; wider W1/W2 regressions remain unresolved.'})
    print(json.dumps({k: v for k, v in report.items() if k not in ('artifact', 'runs')}, indent=2))


if __name__ == '__main__':
    main()
