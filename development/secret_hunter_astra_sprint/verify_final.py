"""Recompute the complete frozen final pools from a read-only exported ledger."""
import argparse
import json
from pathlib import Path
import sqlite3
from development.secret_hunter_astra_sprint.study import ROOT
from development.secret_hunter_astra_sprint.statistics import compare
from development.teacher_eval.run import summarize, snapshot
from development.secret_hunter_program.common import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_run.resolve()
    freeze = json.loads((source / 'final-freeze.json').read_text())
    manifest = json.loads((source / 'manifest.json').read_text())
    assert sha(source / 'manifest.json') == freeze['manifest_sha256']
    assert all(sha(ROOT / p) == h for p, h in freeze['analysis_sources'].items())
    assert all(snapshot(json.loads((ROOT / p).read_text())) == value for p, value in manifest['opponents'].items())
    db = sqlite3.connect((source / 'ledger.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
    # Check both pools before fetching any outcome, including in this verifier.
    assert all(db.execute('select status from batches where id=?', (b,)).fetchone()[0] == 'done'
               for b in ('final-core', 'final-guard'))
    evidence = json.loads((source / 'final-validation.json').read_text())
    assert evidence['final_pools_complete']
    assert evidence['paired_final_validation_complete'] == (len(freeze['arms']) == 2)
    results = {}
    for batch, pool, block in [('final-core', 'core', 'final_core'), ('final-guard', 'guardrail', 'final_guard')]:
        lo, hi = freeze['seeds'][block]
        opponents = json.loads((ROOT / f'development/teacher_eval/{pool}.json').read_text())
        expected = {(o['name'], seed, seat) for o in opponents for seed in range(lo, hi + 1) for seat in (1, 2)}
        report_path = source / 'batches' / batch / 'report.json'
        report = json.loads(report_path.read_text())
        assert sha(report_path) == evidence['pools'][batch]['report_sha256']
        rows = {}
        for arm in freeze['arms']:
            records = list(db.execute('select * from tasks where batch=? and candidate=? order by seed,opponent,seat', (batch, arm)))
            assert all(r['status'] == 'done' for r in records)
            rows[arm] = [json.loads(r['result']) for r in records]
            keys = [(r['opponent'], r['seed'], r['seat']) for r in rows[arm]]
            assert len(keys) == len(expected) and set(keys) == expected
            assert all(r['execution'] == 'full_cli' for r in rows[arm])
            assert summarize(rows[arm]) == report['arms'][arm]
            runtime = json.loads((source / f'runtime-{arm}.json').read_text())
            assert runtime['source_sha256'] == freeze['fingerprints'][arm]
            assert runtime['stress_cases_sha256'] == freeze['runtime_stress_sha256']
        contrasts = {}
        for arm in freeze['arms'][1:]:
            contrast = compare(rows['DARCL2'], rows[arm])
            assert contrast == report['comparisons'][arm], (batch, arm)
            contrasts[arm] = {'primary': contrast['primary'], 'all': contrast['all']}
        results[batch] = {'groups': hi - lo + 1, 'games_per_arm': len(expected),
                          'wins': {arm: report['arms'][arm]['all']['wins'] for arm in freeze['arms']},
                          'comparisons_recomputed': contrasts}
    acceptance = json.loads((source / 'final-acceptance.json').read_text())
    recommendation = evidence['recommendation']
    assert acceptance['candidate'] == recommendation['recommended']
    assert acceptance['source_sha256'] == freeze['fingerprints'][recommendation['recommended']]
    package = source / 'frozen' / (recommendation['recommended'] + '.zip')
    assert sha(package) == recommendation['zip_sha256']
    print(json.dumps({'verified': True, 'arms': freeze['arms'], 'pools': results,
                      'recommended': recommendation['recommended'], 'promoted': recommendation['promoted'],
                      'scope': 'Both final pools fully recomputed from the exported task ledger, including all opponent/seat strata and paired source-seed intervals when two arms exist. This is replication of seen evidence, not a new holdout.'}, indent=2))


if __name__ == '__main__':
    main()
