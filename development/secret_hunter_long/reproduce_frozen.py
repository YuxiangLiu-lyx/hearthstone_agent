"""Create a fresh ledger for exact frozen-package replication, never retune."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile
import time
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    source = args.source_run.resolve()
    if not args.verify_only:
        assert args.run, 'Specify a new --run directory'
        destination = args.run.resolve()
        assert not destination.exists(), 'Never overwrite or reopen an existing ledger'
        assert destination != source
        os.environ['HUNTER_LONG_RUN'] = str(destination)

    import hs_arena
    from development.secret_hunter_long.study import ROOT, RUN, initialize, register, check
    from development.secret_hunter_long.build import audit
    from development.secret_hunter_long.cfqueue import connect
    from development.secret_hunter_mcgs import train
    from development.secret_hunter_program.common import sha
    from development.benchmarks.run import fingerprint

    old = json.loads((source / 'manifest.json').read_text())
    freeze = json.loads((source / 'final-freeze.json').read_text())
    records = json.loads((source / 'release-candidates.json').read_text())
    assert [r['name'] for r in records] == freeze['arms']
    assert all(importlib.metadata.version(k) == v for k, v in old['versions'].items())
    assert all(sha(ROOT / p) == h for p, h in old['protected'].items())
    engine_root = Path(hs_arena.__file__).parent
    expected = {}
    for path, digest in old['engine'].items():
        parts = Path(path).parts
        relative = Path(*parts[parts.index('hs_arena') + 1:])
        expected[str(relative)] = digest
    actual = {str(p.relative_to(engine_root)): sha(p) for p in engine_root.rglob('*')
              if p.is_file() and p.suffix in ('.py', '.json', '.xml', '.txt')}
    assert actual == expected, 'Installed course engine/resources differ from archived evidence'

    with tempfile.TemporaryDirectory(prefix='frozen-reproduction-') as temporary:
        temporary = Path(temporary)
        validated = []
        for record in records:
            arm = record['name']
            package = source / 'frozen' / (arm + '.zip')
            assert sha(package) == record['zip_sha256']
            extracted = temporary / arm
            with ZipFile(package) as archive:
                members = archive.infolist()
                assert {m.filename.split('/')[0] for m in members} == {'secret-hunter'}
                assert all(not m.filename.startswith('/') and '..' not in Path(m.filename).parts for m in members)
                assert sum(m.file_size for m in members) <= 10_000_000
                archive.extractall(extracted)
            exact = extracted / 'secret-hunter'
            assert fingerprint(exact) == freeze['fingerprints'][arm]
            validated.append((record, package, extracted, audit(exact)))
        if args.verify_only:
            print(json.dumps({'verified': True, 'arms': freeze['arms'], 'seeds': freeze['seeds'],
                              'engine_resources': len(actual), 'ledger_created': False}, indent=2))
            return

        assert RUN.is_relative_to(ROOT), 'The new run must be within this isolated source worktree'
        assert not RUN.exists()
        db = connect()
        db.execute('CREATE TABLE auxiliary_games (key TEXT PRIMARY KEY,status TEXT,started REAL,finished REAL,result TEXT)')
        db.commit()
        initialize(db)
        candidates = register(db)
        manifest = train.meta(db, 'manifest')
        for key, bounds in freeze['seeds'].items():
            manifest['seed_blocks'][key] = bounds
        core_groups = freeze['seeds']['final_core'][1] - freeze['seeds']['final_core'][0] + 1
        guard_groups = freeze['seeds']['final_guard'][1] - freeze['seeds']['final_guard'][0] + 1
        manifest['final_target'] = dict(per_arm_core=core_groups * 12, per_arm_guard=guard_groups * 28,
                                        seeds_core=core_groups, seeds_guard=guard_groups)
        manifest['reproduction'] = {'source_run': str(source), 'original_freeze_sha256': sha(source / 'final-freeze.json'),
                                    'original_manifest_sha256': sha(source / 'manifest.json'),
                                    'engine_path_relocated_by_verified_relative_hashes': True}
        check(manifest)
        train.atomic(RUN / 'manifest.json', manifest)
        train.setmeta(db, 'manifest', manifest)
        new_records = []
        for record, package, extracted, validation in validated:
            arm = record['name']
            (RUN / 'frozen').mkdir(exist_ok=True)
            new_package = RUN / 'frozen' / package.name
            shutil.copy2(package, new_package)
            shutil.copytree(extracted, RUN / 'frozen' / arm)
            exact = RUN / 'frozen' / arm / 'secret-hunter'
            candidates[arm]['path'] = str(exact.relative_to(ROOT))
            new_records.append({**record, 'path': str(new_package.relative_to(ROOT)),
                                'extracted': str(exact.relative_to(ROOT)), 'deck_audit': validation})
        train.setmeta(db, 'candidates', candidates)
        train.setmeta(db, 'selection_opened', True)
        train.setmeta(db, 'selected_challenger', freeze['arms'][-1])
        train.atomic(RUN / 'release-candidates.json', new_records)
        train.atomic(RUN / 'final-freeze.json', freeze)
        # These are already-seen public states for phase/latency checks only.
        shutil.copytree(source / 'tactical-sources', RUN / 'tactical-sources')
        commands = []
        for pool, key, batch in [('core', 'final_core', 'final-core'), ('guardrail', 'final_guard', 'final-guard')]:
            lo, hi = freeze['seeds'][key]
            command = ['env', 'HUNTER_LONG_RUN=' + str(RUN), '.venv/bin/python', '-m',
                       'development.secret_hunter_long.study', 'run', '--batch', batch,
                       '--arms', *freeze['arms'], '--start', str(lo), '--seeds', str(hi - lo + 1),
                       '--pool', pool, '--workers', '6', '--final']
            commands.append(command)
        record = {'created': time.time(), 'new_run': str(RUN), **manifest['reproduction'],
                  'arms': freeze['arms'], 'commands': commands,
                  'scope': 'Replication of the original frozen comparison; these seeds are now seen and are not a new holdout.'}
        train.atomic(RUN / 'reproduction.json', record)
        db.close()
        print(json.dumps(record, indent=2))
        print('\n'.join(shlex.join(command) for command in commands))


if __name__ == '__main__':
    main()
