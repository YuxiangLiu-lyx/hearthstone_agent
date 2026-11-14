"""Freeze ZIPs before opening final seeds, then apply the preregistered gate."""
import argparse
import fcntl
import json
import shutil
from zipfile import ZipFile
from development.secret_hunter_long.study import ROOT,RUN,HERE,register,ZIP_SHA
from development.secret_hunter_long.build import audit
from development.secret_hunter_final.release import pack
from development.secret_hunter_program.common import sha
from development.secret_hunter_mcgs import train
from development.benchmarks.run import fingerprint

def prepare(challenger):
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=train.connect(RUN);assert not train.meta(db,'final_opened',False)
        assert not (RUN/'final-freeze.json').exists()
        selection=json.loads((RUN/'selection-decision.json').read_text());assert challenger==selection['challenger']
        cs=register(db);records=[];dest=RUN/'frozen';dest.mkdir(exist_ok=True)
        assert all(cs[x]['sha256']==selection['fingerprints'][x] for x in dict.fromkeys(['B',challenger]))
        for name in dict.fromkeys(['B',challenger]):
            source=HERE/'candidates'/name;path=dest/(name+'.zip')
            if name=='B':
                shutil.copy2(ROOT/'dist/secret-hunter-final-20261113.zip',path);assert sha(path)==ZIP_SHA
            else:pack(source,path)
            extracted=dest/name;assert not extracted.exists();extracted.mkdir()
            with ZipFile(path) as z:z.extractall(extracted)
            exact=extracted/'secret-hunter';assert fingerprint(exact)==cs[name]['sha256']
            validation=audit(exact);cs[name]['path']=str(exact.relative_to(ROOT))
            records.append({'name':name,'path':str(path.relative_to(ROOT)),'zip_sha256':sha(path),'bytes':path.stat().st_size,
                'source_sha256':fingerprint(exact),'extracted':str(exact.relative_to(ROOT)),'deck_audit':validation})
        train.setmeta(db,'candidates',cs);train.atomic(RUN/'release-candidates.json',records)
        print(json.dumps([{k:v for k,v in r.items() if k!='deck_audit'} for r in records]))

def recommend():
    freeze=json.loads((RUN/'final-freeze.json').read_text());challenger=freeze['arms'][-1]
    core=json.loads((RUN/'batches/final-core/report.json').read_text());guard=json.loads((RUN/'batches/final-guard/report.json').read_text())
    core_n=(freeze['seeds']['final_core'][1]-freeze['seeds']['final_core'][0]+1)*12
    guard_n=(freeze['seeds']['final_guard'][1]-freeze['seeds']['final_guard'][0]+1)*28
    assert all(core['arms'][a]['all']['n']==core_n and guard['arms'][a]['all']['n']==guard_n for a in freeze['arms'])
    reliability={arm:all(not b['arms'][arm]['all'][k] for b in (core,guard) for k in (
       'illegal','timeouts','forfeits','harness_errors','opponent_errors','policy_errors','fallbacks','over_2s','public_input_violations')) for arm in freeze['arms']}
    runtime={}
    for arm in freeze['arms']:
        runtime[arm]=json.loads((ROOT/f'docs/secret_hunter_long/runtime-{arm}.json').read_text())
        assert runtime[arm]['source_sha256']==freeze['fingerprints'][arm]
        assert str((ROOT/next(r['extracted'] for r in json.loads((RUN/'release-candidates.json').read_text()) if r['name']==arm)).resolve())==runtime[arm]['candidate']
        reliability[arm]&=all(runtime[arm][k]==0 for k in ('invalid','over_2s','ordinary_fallbacks')) and runtime[arm]['actual_host_stale_seq_rejected']
    main=None;family={};guard_gain=0;statistical=False;correction=False
    if challenger!='B' and challenger in core['comparisons'] and challenger in guard['comparisons']:
        main=core['comparisons'][challenger]['primary'];guard_gain=guard['comparisons'][challenger]['all']['gain']
        family={g:core['comparisons'][challenger]['by_group'][g]['gain'] for g in ('astra','bot2','bot1')}
        # Numerical tolerance enforces the mathematical inclusive regression
        # limits and prevents floating-point roundoff around zero promotion.
        statistical=main['gain_seed_cluster_95'][0]>1e-12 and min(family.values())>=-.025-1e-12 and guard_gain>=-.02-1e-12
        correction=challenger=='BL2' and min(family.values())>=-1e-12 and guard_gain>=-1e-12
    elif challenger!='B':guard_gain=None
    promoted=challenger!='B' and reliability[challenger] and (statistical or correction)
    recommended=challenger if promoted else 'B';assert reliability[recommended]
    record=next(r for r in json.loads((RUN/'release-candidates.json').read_text()) if r['name']==recommended)
    source=ROOT/record['path'];assert sha(source)==record['zip_sha256']
    output=ROOT/'dist/secret-hunter-long-20261114.zip';shutil.copy2(source,output)
    train.atomic(ROOT/'docs/secret_hunter_long/runtime.json',runtime[recommended])
    result={'recommended':recommended,'challenger':challenger,'promoted':promoted,'statistical_gate':statistical,
       'correction_gate':correction,'reliability':reliability,'primary':main,'family_gains':family,'guard_gain':guard_gain,
       'zip':str(output),'zip_sha256':record['zip_sha256'],'bytes':record['bytes'],'source_sha256':record['source_sha256'],
       'final_exact_unpacked_path':record['extracted'],'deck':record['deck_audit'],
       'scope':'Local frozen proxies only; C2 formal score remains separate and unchanged.'}
    train.atomic(ROOT/'docs/secret_hunter_long/recommendation.json',result);train.setmeta(train.connect(RUN),'recommendation',recommended)
    print(json.dumps({k:v for k,v in result.items() if k!='deck'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','recommend']);p.add_argument('--challenger');a=p.parse_args()
    prepare(a.challenger) if a.command=='prepare' else recommend()
