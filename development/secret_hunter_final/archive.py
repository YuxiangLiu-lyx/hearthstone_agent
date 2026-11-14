"""Checkpoint the finished ledger and preserve raw evidence outside the Skill ZIP."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tarfile
import time
from development.secret_hunter_final.study import ROOT,RUN,HERE,register
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import sha
from development.teacher_eval.run import snapshot


def main():
    db=train.connect(RUN);manifest=train.meta(db,'manifest');register(db)
    from development.secret_hunter_final.integrity import check
    check()
    assert train.meta(db,'pid') is None
    assert not db.execute('select 1 from tasks where status!="done"').fetchone()
    assert not db.execute('select 1 from cf_jobs where status!="done"').fetchone()
    assert not db.execute('select 1 from auxiliary_games where status!="done"').fetchone()
    assert all(sha(ROOT/p)==h for p,h in manifest['protected'].items())
    assert all(sha(Path(p))==h for p,h in manifest['engine'].items())
    assert all(snapshot(json.loads((ROOT/p).read_text()))==v for p,v in manifest['opponents'].items())
    train.setmeta(db,'study_complete',{'time':time.time(),'recommendation':'docs/secret_hunter_final/recommendation.json'})
    with sqlite3.connect(RUN/'ledger.snapshot.sqlite') as target:db.backup(target)
    integrity=db.execute('pragma integrity_check').fetchone()[0];assert integrity=='ok'
    db.execute('pragma wal_checkpoint(TRUNCATE)');db.close()
    output=RUN/'artifacts/raw-evidence.tar.gz';output.parent.mkdir(exist_ok=True)
    files=[p for p in RUN.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
           'sources' not in p.relative_to(RUN).parts and p.relative_to(RUN).parts[0]!='artifacts' and p.suffix!='.lock' and
           not (p.suffix=='.log' and p.stat().st_size==0) and
           not p.name.endswith(('-wal','-shm'))]
    # The submitted Skill ZIP is separate. This research archive can include
    # frozen controls, hidden offline labels and execution records.
    with tarfile.open(output,'w:gz',compresslevel=6) as archive:
        for p in sorted(files):archive.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    record={'path':str(output.relative_to(ROOT)),'bytes':output.stat().st_size,'sha256':sha(output),
            'files':len(files),'ledger_sha256':sha(RUN/'ledger.snapshot.sqlite'),'sqlite_integrity':integrity,
            'protected_engine_and_opponents_unchanged':True,
            'scope':'Research evidence only, never submit as the Skill ZIP. External source downloads and empty worker logs excluded; hashes and citations retained in docs.',
            'run':str(RUN.relative_to(ROOT))}
    train.atomic(ROOT/'docs/secret_hunter_final/data-manifest.json',record)
    print(json.dumps(record))


if __name__=='__main__':main()
