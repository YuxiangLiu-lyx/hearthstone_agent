"""One small public opening rule, locked before held-out source labels open."""
import argparse
from collections import defaultdict
import inspect
import json
from pathlib import Path
import statistics
from development.secret_hunter_long.study import HERE,RUN
from development.secret_hunter_long import mulligan
from development.secret_hunter_long.build import clone,audit
from development.secret_hunter_long.cfqueue import connect
from development.secret_hunter_mcgs import train

def dataset(manifest,split):
    data=[];db=connect()
    for case in manifest['cases']:
        src=json.loads((RUN/'mulligan-sources'/(case+'.json')).read_text())
        if src['split']!=split:continue
        rows=db.execute("select * from cf_jobs where kind='mulligan' and key like ?",(case+'-a%',)).fetchall()
        assert rows and all(r['status']=='done' for r in rows),('incomplete opening source',case)
        outcomes={}
        for r in rows:
            result=json.loads(Path(r['result_path']).read_text());assert result['terminal'] and not result.get('error')
            for name in result['job']['aliases']:outcomes[name]=result
        assert 'baseline' in outcomes
        data.append({'source':src,'outcomes':outcomes})
    return data

def match(f,rule):
    if rule.get('feature') is None:return True
    return (f[rule['feature']]>=rule['threshold']) if rule['op']=='>=' else (f[rule['feature']]<rule['threshold'])

def evaluate(data,rule):
    byseed=defaultdict(list);flips=reg=changed=0;positive=set();negative=set();basewins=wins=0
    for row in data:
        base=row['outcomes']['baseline'];chosen=base;src=row['source']
        if rule.get('route') and match(src['features'],rule):chosen=row['outcomes'].get(rule['route'],base)
        delta=chosen['win']-base['win'];byseed[src['seed']].append(delta)
        basewins+=base['win'];wins+=chosen['win'];flips+=delta>0;reg+=delta<0
        changed+=chosen['job']['replace']!=base['job']['replace']
        if delta>0:positive.add(src['seed'])
        if delta<0:negative.add(src['seed'])
    return {'n':len(data),'seed_groups':len(byseed),'baseline_wins':basewins,'chosen_wins':wins,
        'flips':flips,'regressions':reg,'net':flips-reg,'changed_openings':changed,
        'positive_seed_groups':len(positive),'negative_seed_groups':len(negative),
        'seed_equal_gain':statistics.mean(statistics.mean(v) for v in byseed.values()) if byseed else 0}

def run(arm,start):
    manifest=json.loads((RUN/'mulligan-sources'/f'manifest-{arm}-{start}.json').read_text())
    lock=RUN/f'mulligan-rule-freeze-{arm}-{start}.json';training=dataset(manifest,'train')
    if not lock.exists():
        routes=sorted({k for r in training for k in r['outcomes']} - {'baseline','all_replace'})
        options=[{'route':None,'feature':None}]
        # Predefined feature conditions; the exact same table is used at runtime.
        for route in routes:
            options.append({'route':route,'feature':None})
            for feature,values in {'second':[1],'warlock':[1],'hunter':[1],'low':[1,2],'ones':[1],'keeper':[1],'bow':[1],'hyena':[1],'juggler':[1]}.items():
                for t in values:
                    for op in ('>=','<'):options.append({'route':route,'feature':feature,'threshold':t,'op':op})
        scored=[];attempted=[]
        for rule in options:
            result=evaluate(training,rule);attempted.append({'rule':rule,'result':result})
            if rule['route'] and (result['net']<3 or result['positive_seed_groups']<3 or result['changed_openings']<8):continue
            penalty=(2+bool(rule.get('feature')))/max(1,len(training)) if rule['route'] else 0
            scored.append((result['seed_equal_gain']-penalty,rule,result))
        score,rule,result=max(scored,key=lambda x:x[0])
        train.atomic(lock,{'arm':arm,'start':start,'rule':rule,'training':result,'penalized_score':score,
          'tried':len(options),'eligible':len(scored),'criterion':'training source-seed equal gain minus 2/3-label complexity penalty',
          'heldout_gate':'net >=2, positive source groups >=2; then unselected full games required'})
        train.atomic(RUN/f'mulligan-training-search-{arm}-{start}.json',attempted)
    frozen=json.loads(lock.read_text());validation=dataset(manifest,'validation');v=evaluate(validation,frozen['rule'])
    passed=bool(frozen['rule']['route'] and v['net']>=2 and v['positive_seed_groups']>=2)
    diagnostics={route:{split:evaluate(data,{'route':route,'feature':None}) for split,data in [('train',training),('validation',validation)]}
                 for route in sorted({k for r in training+validation for k in r['outcomes']} - {'baseline'})}
    result={**frozen,'validation':v,'passed':passed,'manifest':manifest,'route_diagnostics_not_selection':diagnostics,
       'scope':'matched-opening conditional result; natural frequencies and global gains must come from unselected full-game tests'}
    if passed:
        name=f'{arm}M1'
        def edit(dest):
            # Reuse pure public feature/option functions, with baseline passed in
            # to avoid importing the modified mulligan function recursively.
            code='from collections import Counter\n\n'+inspect.getsource(mulligan.features)+'\n'+inspect.getsource(mulligan.options)
            code=code.replace('def options(s):','def options(s, base):').replace('    from tactics_rank import mulligan\n','').replace("    base=mulligan(s);f=features(s);",'    f=features(s);')
            code+='\nRULE = '+repr(frozen['rule'])+'\n\n'+inspect.getsource(match)
            code+='\ndef apply(s, baseline):\n    if not match(features(s),RULE):return baseline\n    return options(s,baseline).get(RULE["route"],baseline)\n'
            (dest/'scripts/learned_mulligan.py').write_text(code)
            p=dest/'scripts/tactics_rank.py';s=p.read_text()
            old="    return {'type':'mulligan','replace':[c['entity_id'] for c in hand if c['entity_id'] not in keep]}"
            new="    from learned_mulligan import apply\n    return apply(state, {'type':'mulligan','replace':[c['entity_id'] for c in hand if c['entity_id'] not in keep]})"
            assert s.count(old)==1;p.write_text(s.replace(old,new))
        p=clone(name,arm,edit=edit,hypothesis='Train-only learned opening rule, independent label gate passed: '+str(frozen['rule']),generation=2)
        result['candidate']=name;result['audit']=audit(p)
    train.atomic(RUN/f'mulligan-learning-{arm}-{start}.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('manifest','route_diagnostics_not_selection','audit')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--start',type=int,required=True)
    a=p.parse_args();run(a.arm,a.start)
