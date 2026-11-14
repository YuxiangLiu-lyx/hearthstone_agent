"""Source-cluster uncertainty and descriptive opening development diagnostics."""
import argparse
from collections import defaultdict
import json
import random
import statistics
from development.secret_hunter_long.study import RUN
from development.secret_hunter_long.learn_mulligan import dataset,evaluate,match
from development.secret_hunter_mcgs import train

def interval(data,rule):
    groups=defaultdict(list)
    for row in data:
        base=row['outcomes']['baseline'];chosen=base
        if rule.get('route') and match(row['source']['features'],rule):chosen=row['outcomes'].get(rule['route'],base)
        groups[row['source']['seed']].append(chosen['win']-base['win'])
    pairs=[(sum(x),len(x)) for x in groups.values()];rng=random.Random(20261114)
    samples=[]
    for _ in range(10000):
        chosen=rng.choices(pairs,k=len(pairs));samples.append(sum(x[0] for x in chosen)/sum(x[1] for x in chosen))
    samples.sort()
    return {'gain':sum(x[0] for x in pairs)/sum(x[1] for x in pairs),
            'gain_seed_cluster_95':[samples[250],samples[9749]],'source_seed_groups':len(pairs),
            'scope':'Conditional public-opening sample; whole-source-seed ratio bootstrap, not global gain'}

def opening(rows):
    result={'n':len(rows),'turns':{}}
    for t in ('1','2','3'):
        xs=[r['opening'][t] for r in rows if t in r['opening']]
        result['turns'][t]={'reached':len(xs),'with_end_observation':sum('end_board' in x for x in xs),
            **{k:statistics.mean(x[k] for x in xs if k in x) if any(k in x for x in xs) else None
               for k in ('hp','board','board_attack','enemy_attack','end_board','end_attack','unused_mana')},
            'end_empty':sum(x.get('end_board')==0 for x in xs)}
    coin_games=coin_used=0;late=timely=0
    for r in rows:
        hand=r.get('post_mulligan_hand') or []
        coins=[str(i) for i,c in hand if c=='GAME_005'];coin_games+=bool(coins)
        coin_used+=any(i in r['first_play_mana_turn'] for i in coins)
        for i,c in hand:
            if c=='GAME_005':continue
            t=r['first_play_mana_turn'].get(str(i));timely+=t is not None and t<=3;late+=t is None or t>3
    result.update(coin_in_first_main=coin_games,coin_ever_played=coin_used,
       first_main_hand_cards_played_by_T3=timely,first_main_hand_cards_not_played_by_T3=late,
       note='First-main hand includes that turn draw. End mana is descriptive, not proof Coin was wasted. Start T3 board attack/health are measured before our T3 actions.')
    return result

def details(data,rule):
    pairs=[]
    for row in data:
        b=row['outcomes']['baseline'];c=b
        if rule.get('route') and match(row['source']['features'],rule):c=row['outcomes'].get(rule['route'],b)
        pairs.append((b,c))
    return {'terminal':evaluate(data,rule),'uncertainty':interval(data,rule),
            'baseline_opening':opening([b for b,c in pairs]),'candidate_opening':opening([c for b,c in pairs])}

def run(arm,start,confirmation=False):
    manifest=json.loads((RUN/'mulligan-sources'/f'manifest-{arm}-{start}.json').read_text())
    if confirmation:
        plan=json.loads((RUN/'mulligan-confirmation-plan.json').read_text());assert arm in plan['arms'] and start==plan['seeds'][0]
        rule=plan['rule'];data=dataset(manifest,'train')+dataset(manifest,'validation')
        r=evaluate(data,rule);passed=r['net']>=3 and r['positive_seed_groups']>=3
        result={'arm':arm,'start':start,'locked_rule':rule,'manifest':manifest,'confirmation':details(data,rule),'passed':passed,
          'by_actual_first':{str(not second):details([r for r in data if bool(r['source']['features']['second'])==second],rule) for second in (False,True)},
          'next':'unselected full-game parent comparison' if passed else 'retain parent; no retuning on confirmation'}
        path=RUN/f'mulligan-confirmation-{arm}.json'
    else:
        learning=json.loads((RUN/f'mulligan-learning-{arm}-{start}.json').read_text());rule=learning['rule']
        result={'arm':arm,'start':start,'locked_rule':rule,'splits':{s:details(dataset(manifest,s),rule) for s in ('train','validation')}}
        path=RUN/'analysis'/f'mulligan-{arm}-{start}-details.json'
    train.atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('manifest','by_actual_first','splits')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--confirmation',action='store_true')
    a=p.parse_args();run(a.arm,a.start,a.confirmation)
