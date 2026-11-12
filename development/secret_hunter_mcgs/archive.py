"""Package a frozen research skill and a portable, consistent experiment snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile
from development.secret_hunter_mcgs.build import ROOT,HERE
from development.secret_hunter_dgm.deck_guard import check
from development.benchmarks.run import fingerprint


def package(candidate='M5-uct'):
    source=HERE/'candidates'/candidate
    guard=check(source)
    target=ROOT/'dist'/f'secret-hunter-krush-{candidate.lower()}-research.zip'
    target.parent.mkdir(exist_ok=True)
    name=target.stem
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source.rglob('*')):
            if p.is_file() and not {'__pycache__','scratch','game'}.intersection(p.relative_to(source).parts):
                z.write(p,str(Path(name)/p.relative_to(source)))
    assert target.stat().st_size<10_000_000
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(target) as z:z.extractall(tmp)
        restored=Path(tmp)/name
        from hs_arena.skill.loader import load_skill
        load_skill(restored);check(restored)
        assert fingerprint(restored)==fingerprint(source)
    result={'path':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'candidate':candidate,'candidate_fingerprint':fingerprint(source),'deck_guard':guard,
            'status':'research_only_not_promoted','recommended_release':'Y1'}
    (ROOT/'docs/secret_hunter_mcgs/package.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def snapshot(run):
    target=ROOT/'dist/secret-hunter-mcgs-research-data.zip'
    db=sqlite3.connect(run/'ledger.sqlite')
    with tempfile.TemporaryDirectory() as tmp:
        backup=Path(tmp)/'ledger.sqlite';copy=sqlite3.connect(backup);db.backup(copy)
        completed_attempts={r[0] for r in copy.execute("SELECT id FROM attempts WHERE status='done'")}
        completed_games={j['game'] for r in copy.execute("SELECT result FROM tasks WHERE status='done'")
                         if (j:=json.loads(r[0])).get('game')}
        copy.close()
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(backup,'run/ledger.sqlite')
            for p in sorted(run.rglob('*')):
                parts=p.relative_to(run).parts
                if parts[0]=='attempts' and p.suffix=='.json' and int(p.stem) not in completed_attempts:continue
                if 'games' in parts and len(parts)>parts.index('games')+1 and parts[parts.index('games')+1] not in completed_games:continue
                if p.is_file() and p.name not in ('ledger.sqlite','ledger.sqlite-wal','ledger.sqlite-shm','writer.lock') and not p.name.endswith('.tmp'):
                    z.write(p,str(Path('run')/p.relative_to(run)))
            for p in sorted((HERE/'candidates').glob('G*/*')):
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
            for p in sorted((HERE/'candidates').glob('G*/scripts/*')):
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
    db.close()
    result={'path':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'scope':'Consistent SQLite backup plus available raw logs. Historical unavailable cloud files are listed in storage-recovery.json. Running attempts remain charged and reconcile on resume.'}
    (ROOT/'docs/secret_hunter_mcgs/data-package.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def restore(source,run):
    assert not run.exists(), 'Restore requires a new run directory.'
    with zipfile.ZipFile(source) as z:
        for entry in z.infolist():
            parts=Path(entry.filename).parts
            assert '..' not in parts and not Path(entry.filename).is_absolute()
            if not parts or entry.is_dir():continue
            if parts[0]=='run':dest=run.joinpath(*parts[1:])
            elif parts[:3]==('development','secret_hunter_mcgs','candidates'):dest=ROOT/entry.filename
            else:raise ValueError(entry.filename)
            data=z.read(entry)
            if dest.exists():assert dest.read_bytes()==data,dest
            else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    db=sqlite3.connect(run/'ledger.sqlite')
    with db:
        for aid,path in db.execute('SELECT id,result_path FROM attempts').fetchall():
            db.execute('UPDATE attempts SET result_path=? WHERE id=?',(str((run/'attempts'/Path(path).name).resolve()),aid))
        db.execute("UPDATE meta SET value='null' WHERE key='pid'")
    db.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=Path('runs/krush-mcgs'))
    p.add_argument('--restore',type=Path);p.add_argument('--candidate',default='M5-uct');p.add_argument('--skill-only',action='store_true')
    a=p.parse_args();run=(ROOT/a.run).resolve()
    if a.restore:restore(a.restore,run);print(str(run));return
    print(json.dumps(package(a.candidate)))
    if not a.skill_only:print(json.dumps(snapshot(run)))


if __name__=='__main__':main()
