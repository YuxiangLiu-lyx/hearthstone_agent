"""Verify original fallback bytes and environment without inventing final games."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import tempfile
from zipfile import ZipFile
import hs_arena
from development.secret_hunter_astra_sprint.study import ROOT, ZIP_SHA, BASE_SHA
from development.secret_hunter_astra_sprint.build import audit
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--extract', type=Path)
    args = parser.parse_args()
    source = args.source_run.resolve()
    manifest = json.loads((source / 'manifest.json').read_text())
    assert all(importlib.metadata.version(k) == v for k, v in manifest['versions'].items())
    assert all(sha(ROOT / p) == h for p, h in manifest['protected'].items())
    expected = {}
    for p, h in manifest['engine'].items():
        parts = Path(p).parts
        expected[str(Path(*parts[parts.index('hs_arena') + 1:]))] = h
    engine = Path(hs_arena.__file__).parent
    actual = {str(p.relative_to(engine)): sha(p) for p in engine.rglob('*')
              if p.is_file() and p.suffix in ('.py', '.json', '.xml', '.txt')}
    assert expected == actual
    freeze_path = source / 'delivery-freeze.json'
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text())
        assert all(sha(ROOT / p) == h for p, h in freeze['analysis_sources'].items())
        assert not freeze['paired_final_validation_complete'] and not freeze['final_seeds_opened']
    package = source / 'frozen/DARCL2.zip'
    assert sha(package) == ZIP_SHA and package.stat().st_size <= 10_000_000
    with tempfile.TemporaryDirectory(prefix='verify-astra-fallback-') as temporary:
        folder = Path(temporary)
        with ZipFile(package) as archive:
            members = archive.infolist()
            assert {m.filename.split('/')[0] for m in members} == {'secret-hunter'}
            assert 'secret-hunter/SKILL.md' in archive.namelist()
            assert all(not m.filename.startswith('/') and '..' not in Path(m.filename).parts for m in members)
            assert all(m.filename.endswith(('.py', '.json', '.md')) for m in members)
            assert sum(m.file_size for m in members) <= 10_000_000
            archive.extractall(folder)
        exact = folder / 'secret-hunter'
        assert fingerprint(exact) == BASE_SHA
        validation = audit(exact)
        if args.extract:
            destination = args.extract.resolve()
            assert not destination.exists(), 'Use a new extraction directory'
            shutil.copytree(folder, destination)
            assert fingerprint(destination / 'secret-hunter') == BASE_SHA
    print(json.dumps({'verified': True, 'zip_sha256': ZIP_SHA, 'source_sha256': BASE_SHA,
                      'engine_resources': len(actual), 'static_and_submit_deck_valid': validation['valid'],
                      'submit_deck_cli_s': validation['elapsed_s'],
                      'extracted': str(args.extract.resolve()) if args.extract else None,
                      'scope': 'Original fallback identity and environment only. This command does not manufacture or rerun a final paired comparison.'}, indent=2))


if __name__ == '__main__':
    main()
