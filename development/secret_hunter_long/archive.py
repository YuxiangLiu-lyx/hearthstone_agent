"""Seal a stopped run with a consistent SQLite backup and file-level hashes."""
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tarfile
import time

from development.secret_hunter_long.study import ROOT, RUN, check
from development.secret_hunter_mcgs import train


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    db = train.connect(RUN)
    assert not train.meta(db, 'pid') and not train.meta(db, 'cf_pid'), 'Stop experiment writers before sealing'
    assert train.meta(db, 'recommendation'), 'Complete frozen validation and recommendation first'
    for table in ('attempts', 'cf_attempts', 'auxiliary_games'):
        assert not db.execute(f"select count(*) from {table} where status='running'").fetchone()[0]
    assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
    check(train.meta(db, 'manifest'))
    backup = RUN / 'ledger-backup.sqlite'
    assert not backup.exists(), 'Never overwrite a sealed backup'
    destination = sqlite3.connect(backup)
    db.backup(destination)
    assert destination.execute('pragma integrity_check').fetchone()[0] == 'ok'
    destination.close()
    git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    # Per-file hashes exclude the live SQLite WAL set. The self-contained backup
    # is authoritative and must be copied to ledger.sqlite when restoring.
    files = [p for p in sorted(RUN.rglob('*')) if p.is_file() and not p.is_symlink()
             and '__pycache__' not in p.parts and 'relay-bin' not in p.parts
             and p.name not in ('ledger.sqlite', 'ledger.sqlite-shm', 'ledger.sqlite-wal',
                                'evidence-file-manifest.json')]
    manifest = {'created': time.time(), 'git_sha': git_sha,
                'sqlite_restore': 'Copy ledger-backup.sqlite to ledger.sqlite; source path relocation must be explicit.',
                'files': {str(p.relative_to(RUN)): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files}}
    manifest_path = RUN / 'evidence-file-manifest.json'
    train.atomic(manifest_path, manifest)
    files.append(manifest_path)
    archive = ROOT / 'dist/secret-hunter-long-20261114-evidence.tar.gz'
    assert not archive.exists(), 'Never overwrite a sealed evidence archive'
    with archive.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=3) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as tar:
            for p in sorted(files):
                tar.add(p, arcname=str(Path('long-20261114') / p.relative_to(RUN)), recursive=False)
    code = ROOT / 'dist/secret-hunter-long-20261114-source.tar.gz'
    assert not code.exists()
    subprocess.run(['git', 'archive', '--format=tar.gz', '--output=' + str(code), git_sha], cwd=ROOT, check=True)
    result = {'created': time.time(), 'git_sha': git_sha, 'files': len(files),
              'evidence': {'path': str(archive), 'bytes': archive.stat().st_size, 'sha256': digest(archive)},
              'source': {'path': str(code), 'bytes': code.stat().st_size, 'sha256': digest(code)},
              'sqlite_backup_sha256': digest(backup), 'file_manifest_sha256': digest(manifest_path)}
    train.atomic(ROOT / 'docs/secret_hunter_long/archives.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
