"""Build and validate the frozen F2 preference artifact with deterministic ZIP metadata."""
import json
import subprocess
import zipfile
from pathlib import Path
from development.secret_hunter_program.common import ROOT, write, sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check


def main():
    docs = ROOT/'docs/secret_hunter_face'
    freeze = json.loads((docs/'artifact-freeze.json').read_text())
    source = ROOT/freeze['source_paths']['F2']
    check(source)
    assert fingerprint(source) == freeze['source_hashes']['F2']
    files = [source/n for n in ('SKILL.md', 'deck.json', 'config.json', 'client.py')]
    files += sorted((source/'scripts').glob('*.py'))
    target = ROOT/'dist/secret-hunter-krush-face-f2.zip'
    extract = ROOT/'development/secret_hunter_face/release'
    folder = 'secret-hunter-face-f2'
    assert not target.exists() and not extract.exists()
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            member = zipfile.ZipInfo((Path(folder)/path.relative_to(source)).as_posix(),
                                     date_time=(2026, 11, 11, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o100644 << 16
            archive.writestr(member, path.read_bytes())
    with zipfile.ZipFile(target) as archive:
        unpacked = sum(i.file_size for i in archive.infolist())
        assert unpacked < 10_000_000 and target.stat().st_size < 10_000_000
        archive.extractall(extract)
    tree = extract/folder
    check(tree)
    assert fingerprint(tree) == freeze['source_hashes']['F2']
    result = subprocess.run([str(ROOT/'.venv/bin/hs-arena'), 'validate', str(tree), '--no-game'],
                            capture_output=True, text=True, check=True)
    (docs/'zip-validation.txt').write_text(result.stdout+result.stderr)
    manifest = {'zip': str(target.relative_to(ROOT)), 'zip_sha256': sha(target),
                'source': str(source.relative_to(ROOT)), 'source_sha256': fingerprint(source),
                'extracted': str(tree.relative_to(ROOT)), 'bytes': target.stat().st_size,
                'unpacked_bytes': unpacked,
                'files': {p.relative_to(source).as_posix(): sha(p) for p in files},
                'course_assignment_sha256': json.loads((ROOT/'docs/secret_hunter_response/source-hashes.json').read_text())['hw2.md'],
                'scope': 'Preference research artifact; no new match or terminal continuation evaluation. Do not promote as a win-rate improvement.'}
    write(target.with_suffix('.manifest.json'), manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
