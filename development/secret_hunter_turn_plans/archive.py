"""Preserve compact auditable rows and a complete local research-data archive."""
import gzip
import hashlib
import json
import shutil
import sqlite3
import tarfile
from pathlib import Path

from development.secret_hunter_turn_plans.study import ROOT,RUN


def main():
    docs=ROOT/'docs/secret_hunter_turn_plans';data=docs/'data';data.mkdir(exist_ok=True)
    final=json.loads((docs/'final-results.json').read_text())
    assert all(v['complete'] for v in final['batches'].values())
    copied=[]
    def save(path,payload):
        with path.open('wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:zipped.write(payload)
        copied.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for batch in ('final-core','final-guard'):
        for arm in final['freeze']['arms']:
            path=RUN/'batches'/batch/arm/'results.jsonl'
            save(data/(batch+'-'+arm+'.jsonl.gz'),path.read_bytes())
    continuation_folders=['continuations-v4','recovered-golem-continuations','strict-coil-v2','amani-explicit-diagnostic','amani-no-coil-control']
    counts={};compact=[]
    for folder in continuation_folders:
        rows=[];errors=[]
        for path in sorted((RUN/folder).glob('*.json')):
            if '.request.' in path.name or path.name in ('schedule.json','analysis.json','paired-examples.json'):continue
            row=json.loads(path.read_text())
            if row.get('terminal'):
                rows.append(row)
                compact.append({**{k:v for k,v in row.items() if k!='full_trace'},'dataset':folder,
                                'full_trace_available':bool(row.get('full_trace'))})
            else:errors.append(path.name)
        counts[folder]={'terminal':len(rows),'excluded_or_failed':len(errors),
                        'attempt_logs':len(list((RUN/folder).glob('*.log')))}
        shutil.copyfile(RUN/folder/'analysis.json',docs/(folder+'-analysis.json'))
    save(data/'continuation-rows.jsonl.gz',''.join(json.dumps(r)+'\n' for r in compact).encode())
    source_rows=[]
    for folder in ('mined-v4','mined-replay','mined-amani-diagnostic'):
        for p in sorted((RUN/folder).glob('*.json')):
            if p.name!='manifest.json':source_rows.append({'dataset':folder,**json.loads(p.read_text())})
    save(data/'public-source-cases.jsonl.gz',''.join(json.dumps(r)+'\n' for r in source_rows).encode())
    artifacts=RUN/'artifacts';artifacts.mkdir(exist_ok=True)
    source_db=sqlite3.connect(f'file:{RUN}/ledger.sqlite?mode=ro',uri=True)
    backup=artifacts/'ledger.sqlite'
    with sqlite3.connect(backup) as dest_db:source_db.backup(dest_db)
    source_db.close()
    archive=artifacts/'research-evidence.tar.gz'
    files=0
    with tarfile.open(archive,'w:gz',compresslevel=6) as output:
        for path in sorted(RUN.rglob('*')):
            relative=path.relative_to(RUN)
            if not path.is_file() or relative.parts[0]=='artifacts':continue
            if path.name in ('writer.lock','ledger.sqlite','ledger.sqlite-wal','ledger.sqlite-shm'):continue
            output.add(path,arcname=str(path.relative_to(ROOT)),recursive=False);files+=1
        output.add(backup,arcname=str((RUN/'ledger.sqlite').relative_to(ROOT)),recursive=False);files+=1
    # Interrupted and superseded jobs remain in the full archive, separately
    # named. They are never mixed into the corrected final continuation rows.
    attempts={p.name:len(list(p.glob('*.log'))) for p in RUN.iterdir()
              if p.is_dir() and p.name!='attempts' and list(p.glob('*.request.json'))}
    manifest={'complete_archive':{'path':str(archive.relative_to(ROOT)),'bytes':archive.stat().st_size,
        'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':files,
        'contents':'Full local run, immutable provenance, raw CLI observations, continuation requests/results/traces, consistent SQLite backup. Extract at repository root.'},
        'compact_files':copied,'corrected_continuations':counts,'all_offline_attempt_logs':attempts,
        'all_offline_attempt_count':sum(attempts.values()),
        'scope':'Compact files are committed; full local research archive is outside submission ZIPs and contains offline sampled hidden-card audit labels.'}
    (docs/'data-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
