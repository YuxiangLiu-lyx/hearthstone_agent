"""Exact ZIP freezing and the preregistered Astra promotion rule."""
import argparse
import fcntl
import json
import shutil
import time
from zipfile import ZipFile
from development.secret_hunter_astra_sprint.study import ROOT,RUN,HERE,register,ZIP_SHA,ANCHOR
from development.secret_hunter_astra_sprint.build import audit
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_final.release import pack
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

ERRORS=('illegal','timeouts','forfeits','harness_errors','opponent_errors','policy_errors',
        'fallbacks','over_2s','public_input_violations')

def prepare(challenger):
    with (RUN/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        db=ledger.connect(RUN)
        assert not ledger.meta(db,'final_opened',False) and not (RUN/'final-freeze.json').exists()
        selection=json.loads((RUN/'selection-decision.json').read_text())
        assert challenger==selection['challenger']
        cs=register(db);records=[];dest=RUN/'frozen';dest.mkdir(exist_ok=True)
        for name in dict.fromkeys(['DARCL2',challenger]):
            assert cs[name]['sha256']==selection['fingerprints'][name]
            source=HERE/'candidates'/name;path=dest/(name+'.zip')
            if name=='DARCL2':
                assert sha(RUN/'DARCL2-fallback.zip')==ZIP_SHA
                shutil.copy2(RUN/'DARCL2-fallback.zip',path)
            else:pack(source,path)
            extracted=dest/name
            if not extracted.exists():
                extracted.mkdir()
                with ZipFile(path) as z:z.extractall(extracted)
            exact=extracted/'secret-hunter'
            assert fingerprint(exact)==cs[name]['sha256']
            with ZipFile(path) as z:
                assert {p.filename.split('/')[0] for p in z.infolist()}=={'secret-hunter'}
                assert 'secret-hunter/SKILL.md' in z.namelist()
                assert all(p.filename.endswith(('.py','.json','.md')) for p in z.infolist())
                assert sum(p.file_size for p in z.infolist())<=10_000_000
            assert path.stat().st_size<=10_000_000
            validation=audit(exact);cs[name]['path']=str(exact.relative_to(ROOT))
            records.append({'name':name,'path':str(path.relative_to(ROOT)),'zip_sha256':sha(path),
                'bytes':path.stat().st_size,'source_sha256':fingerprint(exact),
                'extracted':str(exact.relative_to(ROOT)),'deck_audit':validation})
        ledger.setmeta(db,'candidates',cs);ledger.atomic(RUN/'release-candidates.json',records)
        print(json.dumps([{k:v for k,v in r.items() if k!='deck_audit'} for r in records]))

def raw_reliability(db,batch,arm):
    rows=[json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=?',(batch,arm))]
    return bool(rows) and all(r.get('execution')=='full_cli' and not r.get('harness_error')
        and r['result']['reason']=='hero_death' and r['result']['winner'] in (1,2)
        and all(not count for field in ('illegal_counts','restarts','timeouts') for count in r['result'][field].values())
        for r in rows)

def recommend():
    db=ledger.connect(RUN);freeze=json.loads((RUN/'final-freeze.json').read_text())
    challenger=freeze['arms'][-1]
    for batch in ('final-core','final-guard'):
        row=db.execute('select status from batches where id=?',(batch,)).fetchone()
        assert row and row['status']=='done', 'Final outcomes stay closed until BOTH pools finish'
    core=json.loads((RUN/'batches/final-core/report.json').read_text())
    guard=json.loads((RUN/'batches/final-guard/report.json').read_text())
    sizes={'final-core':12*(freeze['seeds']['final_core'][1]-freeze['seeds']['final_core'][0]+1),
           'final-guard':28*(freeze['seeds']['final_guard'][1]-freeze['seeds']['final_guard'][0]+1)}
    records=json.loads((RUN/'release-candidates.json').read_text());runtime={};reliability={}
    for arm in freeze['arms']:
        reliability[arm]=all(b['arms'][arm]['all']['n']==sizes[name]
            and all(not b['arms'][arm]['all'][k] for k in ERRORS) and raw_reliability(db,name,arm)
            for name,b in [('final-core',core),('final-guard',guard)])
        runtime[arm]=json.loads((ROOT/f'docs/secret_hunter_astra_sprint/runtime-{arm}.json').read_text())
        record=next(r for r in records if r['name']==arm)
        assert runtime[arm]['source_sha256']==freeze['fingerprints'][arm]
        assert runtime[arm]['candidate']==str((ROOT/record['extracted']).resolve())
        reliability[arm]&=all(runtime[arm][k]==0 for k in ('invalid','over_2s','ordinary_fallbacks'))
        reliability[arm]&=runtime[arm]['actual_host_stale_seq_rejected']
        reliability[arm]&=all(r['actions_identical'] for r in runtime[arm]['concurrency_action_stability'])
    main=None;families={};proxies={};guard_gain=None;gates={'has_challenger':challenger!='DARCL2'}
    if challenger!='DARCL2':
        comparison=core['comparisons'][challenger];main=comparison['primary']
        families={g:comparison['by_group'][g]['gain'] for g in ('astra','bot1','bot2')}
        proxies={o:v['gain'] for o,v in comparison['by_opponent'].items() if o.startswith('astra-')}
        guard_gain=guard['comparisons'][challenger]['all']['gain']
        gates.update(astra_gain_at_least_2pp=main['gain']>=.02-1e-12,
            one_sided_90_lower_positive=main['gain_one_sided_90_lower']>1e-12,
            two_proxies_nonnegative=sum(v>=-1e-12 for v in proxies.values())>=2,
            bot1_within_2pp=families['bot1']>=-.02-1e-12,
            bot2_within_3pp=families['bot2']>=-.03-1e-12,
            guard_within_2pp=guard_gain>=-.02-1e-12,
            baseline_reliable=reliability['DARCL2'],challenger_reliable=reliability[challenger])
    promoted=all(gates.values());recommended=challenger if promoted else 'DARCL2'
    record=next(r for r in records if r['name']==recommended)
    source=ROOT/record['path'];assert sha(source)==record['zip_sha256']
    output=ROOT/('dist/secret-hunter-astra-sprint.zip' if promoted else 'dist/secret-hunter-long-20261114.zip')
    if promoted:shutil.copy2(source,output)
    else:assert sha(output)==ZIP_SHA==record['zip_sha256']
    result={'created':time.time(),'recommended':recommended,'challenger':challenger,'promoted':promoted,
        'final_pools_complete':True,'paired_final_validation_complete':challenger!='DARCL2',
        'source_anchor_commit':ANCHOR,'frozen_research_commit':freeze['git_sha'],
        'gates':gates,'reliability':reliability,'primary':main,'family_gains':families,
        'astra_proxy_gains':proxies,'guard_gain':guard_gain,'zip':str(output),
        'zip_sha256':record['zip_sha256'],'bytes':record['bytes'],'source_sha256':record['source_sha256'],
        'final_exact_unpacked_path':record['extracted'],'deck':record['deck_audit'],
        'scope':'Local fixed proxies only. Historical formal score 10 is unchanged. User submits to Slack.'}
    if challenger=='DARCL2':
        result['reason']='All challengers failed their registered full-game checks. Complete frozen single-arm DARCL2 core/guard validation provides execution and observed-rate evidence, but no candidate paired gain.'
    ledger.atomic(ROOT/'docs/secret_hunter_astra_sprint/recommendation.json',result)
    ledger.atomic(ROOT/'docs/secret_hunter_astra_sprint/runtime.json',runtime[recommended])
    ledger.setmeta(db,'recommendation',recommended)
    print(json.dumps({k:v for k,v in result.items() if k!='deck'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','recommend'])
    p.add_argument('--challenger');a=p.parse_args()
    prepare(a.challenger) if a.command=='prepare' else recommend()
