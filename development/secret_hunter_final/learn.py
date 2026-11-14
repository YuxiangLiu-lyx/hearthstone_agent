"""Fit one public-feature rule on training seed groups, then open held-out labels."""
from collections import defaultdict
import json
import statistics
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train

THRESHOLDS={'mana':[1,2,3,4],'current_mana':[1,2,3,4], 'incoming':[2,4,6,8],
            'own_empty':[1],'enemy_hand':[0,2,4],'coin':[1],'own_low_health':[1,2],
            'juggler':[1],'wolf':[1],'amani':[1],'opponent_hunter':[1],'our_secret':[1]}

def match(f,rule):
    if rule.get('feature') is None:return True
    x=f[rule['feature']];t=rule['threshold']
    return x>=t if rule['op']=='>=' else x<t

def dataset(split):
    manifest=json.loads((RUN/'early-sources/manifest.json').read_text());pairs=[];missing=[]
    for cid in manifest['cases']:
        source=json.loads((RUN/'early-sources'/(cid+'.json')).read_text())
        if source['split']!=split or source.get('kind')=='late_cheap_defense':continue
        for sample in range(3):
            outcomes={}
            for route in source['routes']:
                path=RUN/'early-labels'/f'{cid}-{sample}-{route}.json'
                if not path.exists():missing.append(str(path));continue
                r=json.loads(path.read_text())
                assert not r.get('error'),(path,r.get('error'))
                outcomes[route]=r
            if len(outcomes)!=len(source['routes']):continue
            b=outcomes['baseline']
            assert all(r['root_digest']==b['root_digest'] and r['audit_hidden']==b['audit_hidden'] for r in outcomes.values())
            pairs.append({'source':source,'sample':sample,'outcomes':outcomes})
    assert not missing, ('incomplete labels',len(missing))
    return pairs

def evaluate(pairs,rule):
    by_seed=defaultdict(list);changes=0;first=0;later=0;flips=0;regressions=0;a_wins=0;b_wins=0
    support=set();positive=set();negative=set();wins_reg=0
    for p in pairs:
        src=p['source'];base=p['outcomes']['baseline'];chosen=base
        route=rule.get('route')
        if route and match(src['features'],rule):chosen=p['outcomes'].get(route,base)
        delta=chosen['win']-base['win'];by_seed[src['seed']].append(delta)
        a_wins+=base['win'];b_wins+=chosen['win'];flips+=delta>0;regressions+=delta<0
        if delta>0:positive.add(src['seed'])
        if delta<0:negative.add(src['seed'])
        wins_reg+=int(src['source_score'] and delta<0)
        if chosen['actions_changed'] and chosen is not base:
            changes+=1;support.add(src['case']);first+=chosen['first_changed'];later+=chosen['later_changed']
    return {'n':len(pairs),'seed_groups':len(by_seed),'baseline_wins':a_wins,'route_wins':b_wins,
            'flips':flips,'regressions':regressions,'net':flips-regressions,'changed_futures':changes,
            'changed_sources':len(support),'first_changed':first,'later_changed':later,
            'positive_seed_groups':len(positive),'negative_seed_groups':len(negative),
            'known_win_regressions':wins_reg,
            'seed_equal_gain':statistics.mean(statistics.mean(v) for v in by_seed.values()) if by_seed else 0}

def main():
    train_pairs=dataset('train');lock=RUN/'early-rule-freeze.json'
    if not lock.exists():
        options=[{'route':None,'feature':None}]
        routes=sorted({r for p in train_pairs for r in p['outcomes']} - {'baseline'})
        for route in routes:
            options.append({'route':route,'feature':None})
            for feature,thresholds in THRESHOLDS.items():
                for threshold in thresholds:
                    for op in ('>=','<'):options.append({'route':route,'feature':feature,'op':op,'threshold':threshold})
        scored=[]
        for rule in options:
            result=evaluate(train_pairs,rule)
            if rule['route'] and (result['net']<3 or result['positive_seed_groups']<3 or result['changed_sources']<6):continue
            penalty=(1+bool(rule.get('feature')))/max(1,len(train_pairs)) if rule['route'] else 0
            scored.append((result['seed_equal_gain']-penalty,rule,result))
        score,rule,result=max(scored,key=lambda x:x[0])
        train.atomic(lock,{'rule':rule,'training':result,'penalized_score':score,
                          'tried_rules':len(options),'eligible_rules':len(scored),
                          'features':'public only','selection':'train only, source-seed equal gain minus one/two-future complexity penalty',
                          'validation_gate':'net >= 3, >= 3 positive source-seed groups, no net regression on original winning-source futures; then independent whole-game screen required',
                          'label_scope':'three futures per source; sample 0 exact original world, samples 1/2 shuffled remaining orders, same frozen policies'})
    frozen=json.loads(lock.read_text());valid_pairs=dataset('validation')
    validation=evaluate(valid_pairs,frozen['rule'])
    winning=evaluate([p for p in valid_pairs if p['source']['source_score']],frozen['rule'])
    passed=bool(frozen['rule']['route'] and validation['net']>=3 and validation['positive_seed_groups']>=3 and winning['net']>=0)
    table={}
    for route in sorted({r for p in train_pairs+valid_pairs for r in p['outcomes']} - {'baseline'}):
        table[route]={split:evaluate(ps,{'route':route,'feature':None}) for split,ps in [('train',train_pairs),('validation',valid_pairs)]}
    result={**frozen,'validation':validation,'validation_original_wins':winning,'passes_whole_game_screen_gate':passed,
            'route_diagnostics_not_selection':table,'decision':'build frozen rule and screen on new whole-game seeds' if passed else 'reject learned policy; retain labels as research evidence'}
    train.atomic(ROOT/'docs/secret_hunter_final/early-learning.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='route_diagnostics_not_selection'}))

if __name__=='__main__':main()
