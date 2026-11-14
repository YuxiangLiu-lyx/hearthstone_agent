"""Coverage gate for a same-budget endpoint-generation change."""
import argparse
import json
import subprocess
import sys
from development.secret_hunter_final.study import HERE,RUN,ROOT
from development.secret_hunter_mcgs import train

def main():
    p=argparse.ArgumentParser();p.add_argument('--arm');a=p.parse_args()
    if a.arm:
        sys.path.insert(0,str(HERE/'candidates'/a.arm/'scripts'))
        from program_policy import decide
        from action_validator import legal
        cfg=json.loads((HERE/'candidates'/a.arm/'config.json').read_text());rows=[]
        manifest=json.loads((RUN/'early-sources/manifest.json').read_text())
        for cid in manifest['cases']:
            source=json.loads((RUN/'early-sources'/(cid+'.json')).read_text())
            action,info=decide(source['state'],cfg);assert legal(source['state'],action)
            rows.append({'case':cid,'seed':source['seed'],'action':action,'info':info})
        train.atomic(RUN/f'endpoint-screen-{a.arm}.json',rows);return
    for arm in ['ML2','T']:
        subprocess.run([sys.executable,'-m','development.secret_hunter_final.endpoint_screen','--arm',arm],check=True)
    base={r['case']:r for r in json.loads((RUN/'endpoint-screen-ML2.json').read_text())}
    changed=[];counts={'states':len(base),'same_first_alternates':0,'response_endpoints':0,'guard_rejections':{},'chance_after_guard':0}
    for r in json.loads((RUN/'endpoint-screen-T.json').read_text()):
        info=r['info'];ts=info.get('turn_search',{});f=ts.get('endpoint_funnel',{})
        counts['same_first_alternates']+=f.get('same_first_alternates',0)
        counts['response_endpoints']+=ts.get('reply',{}).get('candidates',0)
        if ts.get('reason'):
            reason=ts['reason'];counts['guard_rejections'][reason]=counts['guard_rejections'].get(reason,0)+1
            counts['chance_after_guard']+=bool(info.get('chance'))
        if r['action']!=base[r['case']]['action']:
            changed.append({'case':r['case'],'seed':r['seed'],'baseline':base[r['case']]['action'],
                            'candidate':r['action'],'funnel':f})
    counts.update(changed_actions=len(changed),changed_seed_groups=len({r['seed'] for r in changed}),changes=changed,
                  gate='Full-game pilot only if >= 5 changed public roots across >= 3 seed groups; no promotion from action changes alone.')
    train.atomic(ROOT/'docs/secret_hunter_final/endpoint-coverage.json',counts)
    print(json.dumps(counts))

if __name__=='__main__':main()
