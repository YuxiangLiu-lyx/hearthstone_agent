"""Cold full CLI, complex public states, worker faults and updated observations."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from development.secret_hunter_mcgs.runtime import probe
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import RUN,ROOT
from development.secret_hunter_program.common import quantiles


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='R4-canonical-cache')
    p.add_argument('--isolated-stale',action='store_true');args=p.parse_args()
    candidate=Y1 if args.candidate=='Y1' else HERE/'candidates'/args.candidate
    states=[json.loads(p.read_text())['state'] for p in (RUN/'mined').glob('*.json') if p.name!='manifest.json']
    states.sort(key=lambda s:len(s['you']['board'])*len(s['opponent']['board'])+len(s['you']['hand']),reverse=True)
    hang='import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n'
    crash='def decide(*args,**kwargs):\n raise RuntimeError("injected crash")\n'
    published='import time\nfrom secret_policy import rank\ndef decide(state,config,publish=None,**kwargs):\n a=rank(state,config)[0][1]\n publish(a,{"fallback":False,"reason":"published_before_hang"})\n time.sleep(20)\n'
    records=[]
    if not args.isolated_stale:
        for c in (Y1,candidate):
            for s in states[:12]:records.append(probe(c,s,'cold'))
        with ThreadPoolExecutor(max_workers=3) as pool:
            records.extend(pool.map(lambda i:probe(candidate,states[i],'concurrent'),range(6)))
        for tag,body in [('hang',hang),('crash',crash),('published_hang',published)]:
            records.append(probe(candidate,states[0],tag,body))
    for c in (Y1,candidate):
        for i in range(4):records.append(probe(c,states[0],'stale-'+str(i),hang,stale=True))
    summary={'candidate':args.candidate,'isolated_stale':args.isolated_stale,'n':len(records),
             'invalid':sum(not r['valid'] for r in records),'over_2s':sum(r['elapsed_s']>2 for r in records),
             'latency_s':quantiles([r['elapsed_s'] for r in records]),
             'ordinary_latency_s':quantiles([r['elapsed_s'] for r in records if r['tag'] in ('cold','concurrent')]),
             'ordinary_fallbacks':sum(bool(r['fallback']) for r in records if r['tag'] in ('cold','concurrent')),
             'injected_fault_fallbacks':sum(bool(r['fallback']) for r in records if r['tag'] in ('hang','crash','published_hang')),
             'records':records}
    out=ROOT/'docs/secret_hunter_turn_plans'/('runtime-'+args.candidate+('-isolated' if args.isolated_stale else '')+'.json')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
    assert summary['invalid']==summary['over_2s']==0


if __name__=='__main__':main()
