"""Grouped paired terminal labels and a deliberately small public decision rule."""
from collections import Counter,defaultdict
import argparse
import json
from pathlib import Path
from development.secret_hunter_turn_plans.study import RUN


def sequence(row):
    return [s['action'] for s in row['sequence']]


def endpoint(row):
    state=row.get('end_tested_turn')
    if state is None:return None
    def clean(x):
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k not in ('entity_id','name','text','playable','legal_actions','events','seq','game_id')}
        if isinstance(x,list):return [clean(v) for v in x]
        return x
    return clean({k:state[k] for k in ('you','opponent')})


def effect(base,alternate):
    assert base.keys()==alternate.keys(), 'Incomplete paired continuation set'
    keys=sorted(base)
    for k in keys:
        left=base[k]['audit_hidden_hypothesis'];right=alternate[k]['audit_hidden_hypothesis']
        assert left==right,('Different paired hidden hypothesis or RNG',k)
    return {'n':len(keys),'cases':len({k[0] for k in keys}),
            'source_seed_groups':len({base[k]['source_seed'] for k in keys}),
            'source_games':len({base[k]['source_game'] for k in keys}),
            'baseline_wins':sum(base[k]['win'] for k in keys),
            'route_wins':sum(alternate[k]['win'] for k in keys),
            'flips':sum(alternate[k]['win']>base[k]['win'] for k in keys),
            'regressions':sum(alternate[k]['win']<base[k]['win'] for k in keys),
            'changed_turns':sum(sequence(base[k])!=sequence(alternate[k]) for k in keys),
            'same_first_action_changed_turns':sum(sequence(base[k])!=sequence(alternate[k]) and sequence(base[k])[0]==sequence(alternate[k])[0] for k in keys),
            'changed_public_endpoints':sum(endpoint(base[k])!=endpoint(alternate[k]) for k in keys if endpoint(base[k]) is not None),
            'baseline_response_survival':sum(bool(base[k]['after_response']['survived']) for k in keys),
            'route_response_survival':sum(bool(alternate[k]['after_response']['survived']) for k in keys)}


def features(source):
    s=source['state'];y=s['you'];f=dict(source['public_features'])
    f.update(keeper_available=float(any(c['card_id']=='EX1_080' and c['cost']<=y['mana'] for c in y['hand'])),
             mana=y['mana'],own_hp=y['hero']['health']+y['hero'].get('armor',0))
    return f


def route_for(rule,f):
    if rule.get('feature') is None:return rule['route']
    return rule['low'] if f[rule['feature']]<=rule['threshold'] else rule['high']


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='continuations-v2');args=p.parse_args()
    folder=RUN/args.input;rows=[];errors=[]
    for path in sorted(folder.glob('*.json')):
        if '.request.' in path.name or path.name in ('schedule.json','analysis.json','paired-examples.json'):continue
        r=json.loads(path.read_text())
        if r.get('terminal'):rows.append(r)
        else:errors.append({'path':path.name,'error':r.get('error',r.get('execution_error','nonterminal'))})
    groups=defaultdict(lambda:defaultdict(dict));by_case=defaultdict(lambda:defaultdict(dict))
    for r in rows:
        key=(r['case'],r['sample'])
        target=groups[(r['kind'],r['split'],r['scenario'])][r['route']]
        assert key not in target;target[key]=r
        by_case[(r['case'],r['scenario'])][r['route']][key]=r
    summary={};case_effects=[];examples=[]
    for key,routes in groups.items():
        if 'replan' not in routes:continue
        summary['/'.join(key)]={route:effect(routes['replan'],rr) for route,rr in routes.items()}
    for (case,scenario),routes in sorted(by_case.items()):
        base=routes['replan']
        scores={route:effect(base,rr) for route,rr in routes.items()}
        case_effects.append({'case':case,'scenario':scenario,'effects':scores})
        if scenario!='natural':continue
        for route,rr in routes.items():
            for k in base:
                delta=rr[k]['win']-base[k]['win']
                if delta:
                    examples.append({'case':case,'sample':k[1],'route':route,'delta':delta,
                                     'baseline':base[k],'alternative':rr[k]})
    # Enumerate constants and one public-feature split. All labels below are
    # natural samples from TRAIN source-seed groups only. Validation is reporting.
    source_dir=json.loads((folder/'schedule.json').read_text()).get('sources','mined')
    sources={r['case']:r for p in (RUN/source_dir).glob('*.json') if p.name!='manifest.json' for r in [json.loads(p.read_text())]}
    fit={};validation={}
    allowed={'trap':['keeper_available','retained_burn','own_hp'],
             'knife_wolf':['knife_potential','mana'], 'amani':['amani_window','own_hp','mana']}
    for kind,feature_names in allowed.items():
        routes=groups[(kind,'train','natural')]
        if 'replan' not in routes:continue
        base=routes['replan'];names=sorted(routes)
        candidates=[{'route':r} for r in names]
        cases=sorted({k[0] for k in base})
        for feat in feature_names:
            values=sorted({features(sources[c])[feat] for c in cases})
            for a,b in zip(values,values[1:]):
                threshold=(a+b)/2
                if min(sum(features(sources[c])[feat]<=threshold for c in cases),sum(features(sources[c])[feat]>threshold for c in cases))<2:continue
                for low in names:
                    for high in names:
                        if low!=high:candidates.append({'feature':feat,'threshold':threshold,'low':low,'high':high})
        def evaluate(rule,rs):
            bb=rs['replan'];aa={k:rs[route_for(rule,features(sources[k[0]]))][k] for k in bb}
            return effect(bb,aa)
        trials=[(rule,evaluate(rule,routes)) for rule in candidates]
        # A one-split rule pays a one-win complexity penalty, and an override
        # needs at least two net training wins across paired terminal samples.
        trials.sort(key=lambda p:(p[1]['route_wins']-int('feature' in p[0]),-p[1]['regressions'],-p[1]['changed_turns']),reverse=True)
        best,metrics=trials[0]
        if metrics['route_wins']-metrics['baseline_wins']<2:best={'route':'replan'};metrics=evaluate(best,routes)
        fit[kind]={'rule':best,'train':metrics,'searched_rules':len(trials),'all_trials':[{'rule':r,'metrics':m} for r,m in trials]}
        if groups[(kind,'validation','natural')]:validation[kind]=evaluate(best,groups[(kind,'validation','natural')])
    report={'terminal_trajectories':len(rows),'excluded':errors,'summary':summary,'case_effects':case_effects,
            'fit':fit,'validation':validation,'forced_coil_played':sum(r['forced_coil_played'] for r in rows),
            'training_scope':'Natural samples only, source seed grouped; one-split public rule with complexity penalty. Small selected case study, not a population win-rate estimate.'}
    (folder/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep full reproducible positive and negative trajectories, favoring trace samples.
    examples.sort(key=lambda r:(not bool(r['baseline']['full_trace']),r['case'],r['sample']))
    chosen=[]
    for delta in (1,-1):
        chosen.extend([e for e in examples if e['delta']==delta][:3])
    (folder/'paired-examples.json').write_text(json.dumps(chosen,indent=2)+'\n')
    print(json.dumps({'terminal_trajectories':len(rows),'excluded':len(errors),'errors':Counter(e['error'].splitlines()[-1] for e in errors),
                     'fit':{k:{x:v for x,v in r.items() if x!='all_trials'} for k,r in fit.items()},'validation':validation},indent=2))


if __name__=='__main__':main()
