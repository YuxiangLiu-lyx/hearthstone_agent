"""Freeze exact ZIPs before evaluation, then deliver only the selected artifact."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from development.secret_hunter_final.study import ROOT,RUN,HERE,register
from development.secret_hunter_final.audit import deck_audit
from development.secret_hunter_mcgs import train
from development.benchmarks.run import fingerprint

def pack(source,path):
    with ZipFile(path,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(source.rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts:continue
            assert p.suffix in ('.py','.json','.md'), p
            member=ZipInfo('secret-hunter/'+p.relative_to(source).as_posix(),(1980,1,1,0,0,0))
            member.compress_type=ZIP_DEFLATED;member.external_attr=0o644<<16
            z.writestr(member,p.read_bytes())
    with ZipFile(path) as z:
        assert sum(x.file_size for x in z.infolist())<=10_000_000
        assert {p.filename.split('/')[0] for p in z.infolist()}=={'secret-hunter'}
        assert 'secret-hunter/SKILL.md' in z.namelist()
    assert path.stat().st_size<=10_000_000

def prepare(challenger):
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=train.connect(RUN);assert not train.meta(db,'final_opened',False)
        assert not (RUN/'final-freeze.json').exists()
        cs=register(db);records=[];dest=RUN/'frozen';dest.mkdir(exist_ok=True)
        for name in ['B',challenger]:
            source=HERE/'candidates'/name;path=dest/(name+'.zip');pack(source,path)
            extracted=dest/name
            assert not extracted.exists();extracted.mkdir()
            with ZipFile(path) as z:z.extractall(extracted)
            exact=extracted/'secret-hunter';assert fingerprint(exact)==cs[name]['sha256']
            audit=deck_audit(exact);cs[name]['path']=str(exact.relative_to(ROOT))
            records.append({'name':name,'path':str(path.relative_to(ROOT)),
                            'zip_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
                            'source_sha256':fingerprint(exact),'extracted':str(exact.relative_to(ROOT)),
                            'deck_audit':audit})
        train.setmeta(db,'candidates',cs);train.atomic(RUN/'release-candidates.json',records)
        print(json.dumps(records))

def recommend():
    freeze=json.loads((RUN/'final-freeze.json').read_text());challenger=freeze['arms'][1]
    core=json.loads((RUN/'batches/final-core/report.json').read_text())
    guard=json.loads((RUN/'batches/final-guard/report.json').read_text())
    core_n=(freeze['seeds']['final_core'][1]-freeze['seeds']['final_core'][0]+1)*12
    guard_n=(freeze['seeds']['final_guard'][1]-freeze['seeds']['final_guard'][0]+1)*28
    assert all(core['arms'][a]['all']['n']==core_n and guard['arms'][a]['all']['n']==guard_n for a in freeze['arms'])
    main=core['comparisons'][challenger]['primary'];guard_gain=guard['comparisons'][challenger]['all']['gain']
    families={g:core['comparisons'][challenger]['by_group'][g]['gain'] for g in ['astra','bot2','bot1']}
    reliability={}
    for arm in freeze['arms']:
        reliability[arm]=all(not block['arms'][arm]['all'][k] for block in [core,guard]
                            for k in ('illegal','timeouts','forfeits','harness_errors','opponent_errors','policy_errors','fallbacks','over_2s','public_input_violations'))
    statistical=main['gain']>0 and main['gain_seed_cluster_95'][0]>0 and min(families.values())>=-.025 and guard_gain>=-.02
    correction=challenger=='L2' and min(families.values())>=0 and guard_gain>=0
    promoted=reliability[challenger] and (statistical or correction)
    recommended=challenger if promoted else 'B';assert reliability[recommended]
    record=next(r for r in json.loads((RUN/'release-candidates.json').read_text()) if r['name']==recommended)
    source=ROOT/record['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==record['zip_sha256']
    output=ROOT/'dist/secret-hunter-final-20261113.zip';shutil.copy2(source,output)
    result={'recommended':recommended,'challenger':challenger,'promoted':promoted,
            'statistical_gate':statistical,'correction_gate':correction,'reliability':reliability,
            'primary':main,'family_gains':families,'guard_gain':guard_gain,
            'zip':str(output),'zip_sha256':record['zip_sha256'],'bytes':record['bytes'],
            'source_sha256':record['source_sha256'],'final_exact_unpacked_path':record['extracted'],
            'scope':'Frozen local pools only; final tests do not alter the known C2 course score of 10.'}
    train.atomic(ROOT/'docs/secret_hunter_final/recommendation.json',result)
    print(json.dumps(result,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','recommend']);p.add_argument('--challenger');a=p.parse_args()
    if a.command=='prepare':prepare(a.challenger)
    else:recommend()

if __name__=='__main__':main()
