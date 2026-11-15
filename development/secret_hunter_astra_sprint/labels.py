"""Paired terminal evidence, with explicit source/world holdout access."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import time
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger

def read(split='train', worlds=(0,1), lock=None, case_ids=None):
    if split!='train' or 2 in worlds:
        assert lock and Path(lock).exists(), 'Lock a concrete hypothesis before opening held-out labels'
        record=json.loads(Path(lock).read_text())
        assert record['hypothesis'] and record['source_sha256'] and record['created']<=time.time()
    db=ledger.connect(RUN);data=defaultdict(dict);sources={}
    extra_path=RUN/'tactical-extra-routes.json'
    extra=json.loads(extra_path.read_text())['routes_by_case'] if extra_path.exists() else {}
    for r in db.execute("select job,status,result_path from cf_jobs where kind='tactical'"):
        job=json.loads(r['job'])
        if job['sample'] not in worlds or job.get('policy_arm'):continue
        case=job['case']
        if case_ids is not None and case not in case_ids:continue
        if case not in sources:sources[case]=json.loads((RUN/'tactical-sources'/(case+'.json')).read_text())
        if sources[case]['split']!=split:continue
        assert r['status']=='done', ('incomplete label',job,r['status'])
        result=json.loads(Path(r['result_path']).read_text())
        assert result.get('terminal') and not result.get('error') and result['job']==job
        data[case][job['sample'],job['route']]=result
    assert data
    pairs=[]
    for case,labels in data.items():
        src=sources[case]
        for world in worlds:
            baseline=labels[world,'baseline']
            assert baseline['root_digest']==src['state_digest']
            if world==0:assert baseline['win']==src['source_score']
            for route in src['routes'][1:]+extra.get(case,[]):
                other=labels[world,route]
                assert other['audit_hidden']==baseline['audit_hidden'], ('unpaired hidden world',case,world,route)
                assert other['root_digest']==baseline['root_digest']
                pairs.append({'case':case,'seed':src['seed'],'opponent':src['opponent_spec']['name'],
                    'seat':src['seat'],'actual_first':src['actual_first'],'seq':src['seq'],
                    'world':world,'route':route,'baseline':baseline['win'],'alternative':other['win'],
                    'delta':other['win']-baseline['win'],'changed':other['actions_changed'],
                    'first_changed':other['first_changed'],'later_changed':other['later_changed'],
                    'features':src['features'],'source_score':src['source_score']})
    return pairs,sources

def summarize(pairs):
    seeds=defaultdict(float)
    for r in pairs:seeds[r['seed']]+=r['delta']
    return {'paired_world_routes':len(pairs),'roots':len({r['case'] for r in pairs}),
            'source_seeds':len(seeds),'baseline_wins':sum(r['baseline'] for r in pairs),
            'alternative_wins':sum(r['alternative'] for r in pairs),
            'rescues':sum(r['delta']>0 for r in pairs),'regressions':sum(r['delta']<0 for r in pairs),
            'net':sum(r['delta'] for r in pairs),
            'positive_source_seeds':sum(v>0 for v in seeds.values()),
            'negative_source_seeds':sum(v<0 for v in seeds.values()),
            'no_action_change':sum(not r['changed'] for r in pairs),
            'first_action_changed':sum(r['first_changed'] for r in pairs),
            'later_action_changed':sum(r['later_changed'] for r in pairs)}

def report(split='train', worlds=(0,1), lock=None, manifest=None):
    case_ids=set(json.loads(manifest.read_text())['cases']) if manifest else None
    pairs,sources=read(split,worlds,lock,case_ids)
    routes=sorted({r['route'] for r in pairs})
    result={'created':time.time(),'split':split,'worlds':list(worlds),'hypothesis_lock':str(lock) if lock else None,
        'total':summarize(pairs),
        'by_route':{route:summarize([r for r in pairs if r['route']==route]) for route in routes},
        'by_route_proxy':{route:{o:summarize([r for r in pairs if r['route']==route and r['opponent']==o])
            for o in sorted({r['opponent'] for r in pairs if r['route']==route})} for route in routes},
        'by_route_mana':{route:{str(m):summarize([r for r in pairs if r['route']==route and r['features']['mana']==m])
            for m in sorted({r['features']['mana'] for r in pairs if r['route']==route})} for route in routes},
        'pairs':pairs,
        'warning':'Outcome-stratified conditional sample, not a natural-frequency full-game gain. Routes share roots/worlds; do not treat pairs as independent observations.'}
    prefix='labels-' if manifest is None else 'labels-'+manifest.stem+'-'
    path=RUN/f"{prefix}{split}-worlds-{''.join(map(str,worlds))}.json"
    if path.exists():
        saved=json.loads(path.read_text())
        assert {k:v for k,v in saved.items() if k!='created'}=={k:v for k,v in result.items() if k!='created'}, 'Immutable label report changed; use an explicit source manifest'
        result=saved
    else:ledger.atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('pairs','by_route_proxy','by_route_mana')},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['train','validation'],default='train')
    p.add_argument('--worlds',type=int,nargs='+',default=[0,1]);p.add_argument('--lock',type=Path)
    p.add_argument('--manifest',type=Path)
    a=p.parse_args();report(a.split,tuple(a.worlds),a.lock,a.manifest)
