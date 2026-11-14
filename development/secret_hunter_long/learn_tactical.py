"""Terminal-label rule fit, held-out teacher advice, then actual-policy replay."""
import argparse
from collections import defaultdict
import inspect
import json
from pathlib import Path
import random
import statistics
from development.secret_hunter_long.study import HERE,RUN
from development.secret_hunter_long.build import clone,audit
from development.secret_hunter_long.cfqueue import connect,reserve
from development.secret_hunter_mcgs import train

THRESHOLDS={'mana':[2,3,4],'current_mana':[2,3,4],'incoming':[3,5,7],'own_empty':[1],
    'coin':[1],'enemy_hand':[2,4],'juggler':[1],'wolf':[1],'health':[12,20],'opponent_hunter':[1]}
DEPLOYABLE={'bow_clear','kill_juggler','kill_wolf','develop','hold_coin','trap','preserve_burn','face','power'}

def confidence(groups):
    pairs=[(sum(v),len(v)) for v in groups.values()];rng=random.Random(20261114);samples=[]
    for _ in range(10000):
        chosen=rng.choices(pairs,k=len(pairs));samples.append(sum(x[0] for x in chosen)/sum(x[1] for x in chosen))
    samples.sort();return [samples[250],samples[9749]]

def match(f,rule):
    if not rule.get('feature'):return True
    return f[rule['feature']]>=rule['threshold'] if rule['op']=='>=' else f[rule['feature']]<rule['threshold']

def dataset(manifest,split):
    db=connect();data=[]
    for cid in manifest['cases']:
        src=json.loads((RUN/'tactical-sources'/(cid+'.json')).read_text())
        if src['split']!=split:continue
        for sample in range(manifest['samples']):
            outcomes={}
            for route in src['routes']:
                key=f'{cid}-w{sample}-{route}';row=db.execute('select * from cf_jobs where key=?',(key,)).fetchone()
                assert row and row['status']=='done',('incomplete tactical pair',key)
                r=json.loads(Path(row['result_path']).read_text());assert r['terminal'] and not r.get('error');outcomes[route]=r
            b=outcomes['baseline'];assert all(r['root_digest']==b['root_digest'] and r['audit_hidden']==b['audit_hidden'] for r in outcomes.values())
            data.append({'source':src,'sample':sample,'outcomes':outcomes})
    return data

def evaluate(data,rule,with_interval=False):
    byseed=defaultdict(list);flips=reg=first=later=0;basewins=wins=0;support=set();positive=set();negative=set()
    for p in data:
        src=p['source'];b=p['outcomes']['baseline'];chosen=b
        if rule.get('route') and match(src['features'],rule):chosen=p['outcomes'].get(rule['route'],b)
        delta=chosen['win']-b['win'];byseed[src['seed']].append(delta);basewins+=b['win'];wins+=chosen['win']
        flips+=delta>0;reg+=delta<0
        if delta>0:positive.add(src['seed'])
        if delta<0:negative.add(src['seed'])
        if chosen is not b and chosen['actions_changed']:
            support.add(src['case']);first+=chosen['first_changed'];later+=chosen['later_changed']
    result={'n':len(data),'seed_groups':len(byseed),'baseline_wins':basewins,'chosen_wins':wins,'flips':flips,'regressions':reg,
       'net':flips-reg,'changed_roots':len(support),'first_changed_futures':first,'later_changed_futures':later,
       'positive_seed_groups':len(positive),'negative_seed_groups':len(negative),
       'seed_equal_gain':statistics.mean(statistics.mean(v) for v in byseed.values()) if byseed else 0}
    if with_interval:result['gain_seed_cluster_95']=confidence(byseed)
    return result

def teacher(data):
    sources=defaultdict(dict)
    for p in data:sources[p['source']['case']][p['sample']]=p
    choices=[];a=b=flips=reg=0
    for cid,worlds in sources.items():
        assert 0 in worlds
        src=worlds[0]['source'];alternates=[p for s,p in worlds.items() if s!=0]
        if not alternates:continue
        scores={r:statistics.mean(p['outcomes'][r]['win'] for p in alternates) for r in src['routes']}
        best=max(src['routes'],key=lambda r:(scores[r],r=='baseline'))
        base=worlds[0]['outcomes']['baseline'];chosen=worlds[0]['outcomes'][best]
        a+=base['win'];b+=chosen['win'];flips+=chosen['win']>base['win'];reg+=chosen['win']<base['win']
        choices.append({'case':cid,'source_seed':src['seed'],'route':best,'selection_worlds':[s for s in worlds if s!=0],
            'heldout_world':0,'baseline_win':base['win'],'teacher_win':chosen['win']})
    grouped=defaultdict(list)
    for c in choices:grouped[c['source_seed']].append(c['teacher_win']-c['baseline_win'])
    return {'n':len(choices),'baseline_wins':a,'teacher_wins':b,'flips':flips,'regressions':reg,'net':flips-reg,'choices':choices,
        'source_seed_groups':len(grouped),'gain_seed_cluster_95':confidence(grouped),
        'scope':'Offline teacher selects from alternate deck-order/RNG worlds1+, then evaluated on untouched original-world outcome0. Original simulated hidden hands remain fixed; not an executable public-only online oracle.'}

def run(batch,arm,candidate_name=None):
    manifest=json.loads((RUN/'tactical-sources'/f'manifest-{batch}-{arm}.json').read_text());lock=RUN/f'tactical-rule-freeze-{batch}-{arm}.json'
    training=dataset(manifest,'train')
    if not lock.exists():
        options=[{'route':None,'feature':None}]
        routes=sorted(({r for p in training for r in p['outcomes']}-{'baseline'}) & DEPLOYABLE)
        for route in routes:
            options.append({'route':route,'feature':None})
            for f,ts in THRESHOLDS.items():
                for t in ts:
                    for op in ('>=','<'):options.append({'route':route,'feature':f,'threshold':t,'op':op})
        scored=[];search=[]
        for rule in options:
            r=evaluate(training,rule);search.append({'rule':rule,'result':r})
            if rule['route'] and (r['net']<5 or r['positive_seed_groups']<4 or r['changed_roots']<10):continue
            penalty=(3+bool(rule.get('feature')))/max(1,len(training)) if rule['route'] else 0
            scored.append((r['seed_equal_gain']-penalty,rule,r))
        score,rule,r=max(scored,key=lambda p:p[0])
        train.atomic(lock,{'rule':rule,'training':r,'penalized_score':score,'tried':len(options),'eligible':len(scored),
          'validation_gate':'net >=3 and >=3 positive source seed groups, then actual stateless policy source replays before independent full games'})
        train.atomic(RUN/f'tactical-training-search-{batch}-{arm}.json',search)
    frozen=json.loads(lock.read_text());validation=dataset(manifest,'validation');valid=evaluate(validation,frozen['rule'],True)
    passed=bool(frozen['rule']['route'] and valid['net']>=3 and valid['positive_seed_groups']>=3)
    result={**frozen,'validation':valid,'teacher':teacher(validation),'passed_fixed_route_label_gate':passed,
       'route_diagnostics_not_selection':{r:{split:evaluate(ps,{'route':r,'feature':None}) for split,ps in [('train',training),('validation',validation)]} for r in sorted({r for p in training+validation for r in p['outcomes']}-{'baseline'})}}
    if passed:
        name=candidate_name or arm+'T1'
        def edit(dest):
            # Pure visible route helpers only. No audit labels, source keys, seed,
            # opponent config, or hidden world sampler enters the submission.
            from development.secret_hunter_long import tactical
            tactical.setup(arm)
            from development.secret_hunter_final import early_routes
            code=inspect.getsource(early_routes).replace('ROUTES=', 'OFFLINE_UNUSED_ROUTES=')
            (dest/'scripts/route_primitives.py').write_text(code)
            code=inspect.getsource(tactical.propose).replace('from development.secret_hunter_final.early_routes import propose as old','from route_primitives import propose as old')
            code='from route_primitives import features\n\n'+code+'\n'+inspect.getsource(match)+'\nRULE='+repr(frozen['rule'])+'\n'
            code+='\ndef choose(state,baseline):\n    if state.get("phase")!="main" or not 1<=state["you"]["max_mana"]<=5 or not match(features(state),RULE):return None\n    return propose(state,RULE["route"],{},baseline)\n'
            (dest/'scripts/learned_tactics.py').write_text(code)
            p=dest/'scripts/program_policy.py';s=p.read_text();old="    info['elapsed_s']=time.monotonic()-start"
            new="""    if state.get('phase')=='main' and info.get('reason')!='guaranteed_lethal':
        from learned_tactics import choose
        alternative=choose(state,best)
        if alternative is not None and alternative!=best and legal(state,alternative):
            info['learned_parent_action']=best
            info['learned_rule_changed']=True
            save(alternative,'learned_public_rule')
    info['elapsed_s']=time.monotonic()-start"""
            assert s.count(old)==1;p.write_text(s.replace(old,new))
        p=clone(name,arm,edit=edit,hypothesis='Training-only public terminal-gain rule; fixed-route label gate passed, actual stateless rollout still required',generation=2)
        result['candidate']=name;result['audit']=audit(p)
        jobs=[]
        for cid in manifest['cases']:
            src=json.loads((RUN/'tactical-sources'/(cid+'.json')).read_text())
            if src['split']!='validation':continue
            for sample in range(manifest['samples']):
                jobs.append((f'{cid}-w{sample}-policy-{name}',{'case':cid,'sample':sample,'route':'baseline','arm':arm,'policy_arm':name}))
        reserve('tactical',jobs);result['actual_policy_jobs']=len(jobs)
    else:result['actual_short_policy']='unchanged parent; actual terminal labels identical to baseline by exact source fingerprint'
    train.atomic(RUN/f'tactical-learning-{batch}-{arm}.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('route_diagnostics_not_selection','audit','teacher')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--arm',default='B');p.add_argument('--candidate-name')
    a=p.parse_args();run(a.batch,a.arm,a.candidate_name)
