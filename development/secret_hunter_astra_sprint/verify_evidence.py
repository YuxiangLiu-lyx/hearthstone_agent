"""Recompute completed development contrasts and audit a portable evidence bundle."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
from development.secret_hunter_astra_sprint.statistics import paired
from development.secret_hunter_astra_sprint.tactical import digest
from development.secret_hunter_program.common import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_run.resolve()
    index_path = source / 'evidence-index.json'
    indexed = 0
    if index_path.exists():
        index = json.loads(index_path.read_text())
        for relative, expected in index['files'].items():
            path = source / relative
            assert path.is_relative_to(source) and '..' not in Path(relative).parts
            assert sha(path) == expected, relative
            indexed += 1
        assert sha(source / 'ledger.sqlite') == index['ledger_sqlite_sha256']
    db = sqlite3.connect((source / 'ledger.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
    manifest = json.loads((source / 'manifest.json').read_text())
    batches = list(db.execute('select * from batches order by start'))
    for left, right in zip(batches, batches[1:]):
        assert left['start'] + left['seeds'] <= right['start'], 'Overlapping source blocks'
    totals = {table: db.execute('select count(*) from ' + table).fetchone()[0]
              for table in ('attempts', 'auxiliary_games', 'cf_attempts')}
    assert totals['attempts'] + totals['auxiliary_games'] <= manifest['limits']['full_games']
    assert totals['cf_attempts'] <= manifest['limits']['continuations']
    contrasts = {}
    for batch, arm in [('round1-recall', 'RJC'), ('round2-ranker', 'PRR'),
                       ('round3-arcane', 'DA2'), ('round4-hand-resource', 'EHC')]:
        status = db.execute('select status from batches where id=?', (batch,)).fetchone()
        assert status and status[0] == 'done'
        rows = {name: [json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=? and status=\'done\'', (batch, name))]
                for name in ('DARCL2', arm)}
        assert all(len(v) == 480 for v in rows.values())
        primary = paired(*[[r for r in rows[name] if r['group'] == 'astra'] for name in ('DARCL2', arm)])
        report = json.loads((source / 'batches' / batch / 'report.json').read_text())
        assert primary == report['comparisons'][arm]['primary'], batch
        contrasts[arm] = {k: primary[k] for k in ('a_wins', 'b_wins', 'gain', 'gain_seed_cluster_95', 'gain_one_sided_90_lower')}
    roots = {}
    partitions = {}
    for path in (source / 'tactical-sources').glob('*.json'):
        root = json.loads(path.read_text())
        if path.name.startswith('manifest-'):
            assert 'cases' in root and 'roots' in root
            continue
        assert digest(root['state']) == root['state_digest']
        assert root['split'] in ('train', 'validation')
        assert partitions.setdefault(root['seed'], root['split']) == root['split']
        bounds = manifest['seed_blocks']['development' if root['split'] == 'train' else 'label_holdout']
        assert bounds[0] <= root['seed'] <= bounds[1]
        roots[root['case']] = root
        game = Path(root['game_path'])
        assert game.parts[:2] == ('runs', 'astra-sprint-20261114')
        for seat in (1, 2):
            assert (source / Path(*game.parts[2:]) / f'p{seat}/observations.jsonl').exists()
    worlds, label_counts = {}, Counter()
    for row in db.execute('select * from cf_jobs'):
        assert row['status'] == 'done'
        original = Path(row['result_path'])
        path = source / original.parent.name / original.name
        label = json.loads(path.read_text())
        label_counts[row['kind']] += 1
        if row['kind'] != 'tactical':
            continue
        job = json.loads(row['job'])
        assert label['job'] == job and label['terminal'] and not label.get('error')
        root = roots[label['case']]
        assert label['source_seed'] == root['seed'] and label['split'] == root['split']
        assert label['root_digest'] == root['state_digest'] and label['prefix_verified_steps'] >= 0
        world = json.dumps(label['audit_hidden'], sort_keys=True)
        key = (label['case'], label['sample'])
        assert worlds.setdefault(key, world) == world, 'Routes did not start from the same hidden world'
        request = json.loads(path.with_suffix('.request.json').read_text())
        assert request['job'] == job
        execution = label['harness_execution']
        assert execution['archived_source_executed']
        expected = execution['kind_source_sha256']
        archive = json.loads((source / 'harness-by-sha' / (expected + '.json')).read_text())
        assert hashlib.sha256(archive['utf8_source'].encode()).hexdigest() == expected
        if label['sample'] == 0 and label['route'] == 'baseline' and not job.get('policy_arm'):
            assert label['win'] == root['source_score'], 'Original terminal outcome did not reproduce'
    print(json.dumps({'verified': True, 'indexed_files': indexed, 'charged_attempts': totals,
                      'development_contrasts_recomputed': contrasts, 'roots': len(roots),
                      'source_partitions': dict(Counter(partitions.values())),
                      'paired_root_worlds': len(worlds), 'continuation_labels': dict(label_counts),
                      'scope': 'Integrity and recomputation of completed development evidence only. Partial confirmation and resource-pilot outcomes are not inspected; no missing final sample is manufactured.'}, indent=2))


if __name__ == '__main__':
    main()
