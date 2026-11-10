"""Describe visible failure patterns; associations are not causal proofs."""
import argparse,json,statistics
from collections import Counter,defaultdict
from pathlib import Path

def audit(paths):
    groups=defaultdict(list);cases=[];cards=defaultdict(Counter)
    for path in paths:
        for line in (Path(path)/'games.jsonl').read_text().splitlines():
            g=json.loads(line)
            rows=[json.loads(l) for l in Path(g['observations']).read_text().splitlines()]
            main=[r for r in rows if r['state']['phase']=='main']
            ends=[r for r in main if r['action']['type']=='end_turn']
            if not main:continue
            last=main[-1]['state'];y,o=last['you'],last['opponent']
            events=[json.loads(l) for l in Path(g['replay']).read_text().splitlines()]
            seat=g['candidate_seat']
            aoe=Counter(e['name'] for e in events if e['event']=='play_card' and e['player']!=seat and e.get('card_id') in ('CS2_032','CS2_093','CS1_112','CS2_062','CS2_025','CS2_028'))
            # End-turn stalls with legal attacks blocked by a taunt, where total ready
            # damage could at least remove it; a signal to inspect, not a lethal proof.
            stalls=[]
            for r in ends:
                s=r['state'];taunts=[m for m in s['opponent']['board'] if m.get('taunt') and not m.get('stealth')]
                attackers=[m for m in s['you']['board'] if m.get('can_attack') and m['attack']>0]
                if taunts and len(attackers)>=2 and sum(m['attack'] for m in attackers)>=min(m['health']+(min(x['attack'] for x in attackers) if m.get('divine_shield') else 0) for m in taunts):
                    stalls.append(s['seq'])
            label='win' if g['score'] else 'loss'
            for c in y['hand']:cards[label][c['name']]+=1
            item={'seed':g['seed'],'seat':seat,'opponent':g['opponent'],'score':g['score'],
                  'turns':g['turns'],'own_hp':y['hero']['health'],'enemy_hp':o['hero']['health'],
                  'own_board_attack':sum(m['attack'] for m in y['board']),
                  'enemy_board_attack':sum(m['attack'] for m in o['board']),
                  'hand_size':len(y['hand']),'hand':[c['name'] for c in y['hand']],
                  'taunt_stall_seqs':stalls,'enemy_aoe':dict(aoe),
                  'tap_count':sum(r['action']['type']=='hero_power' for r in main),
                  'unspent_late_mana':sum(r['state']['you']['mana'] for r in ends if r['state']['you']['max_mana']>=6),
                  'replay':g['replay'],'observations':g['observations']}
            groups[label].append(item)
            if not g['score']:cases.append(item)
    metrics={}
    for label,rows in groups.items():
        metrics[label]={'games':len(rows),'mean_turns':statistics.mean(r['turns'] for r in rows),
          'board_deficit':sum(r['enemy_board_attack']>r['own_board_attack'] for r in rows),
          'hand_at_most_one':sum(r['hand_size']<=1 for r in rows),
          'enemy_hp_above_10':sum(r['enemy_hp']>10 for r in rows),
          'enemy_aoe_games':sum(bool(r['enemy_aoe']) for r in rows),
          'taunt_stall_games':sum(bool(r['taunt_stall_seqs']) for r in rows),
          'taunt_stalls':sum(len(r['taunt_stall_seqs']) for r in rows),
          'mean_unspent_late_mana':statistics.mean(r['unspent_late_mana'] for r in rows),
          'final_hand_cards':dict(cards[label]),
          'by_opponent':dict(Counter(r['opponent'] for r in rows))}
    return {'inputs':paths,'metrics':metrics,'loss_cases':cases,
            'interpretation':'Descriptive signals only. Prior holdout is now development evidence; future claims require fresh seeds.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiments',nargs='+');p.add_argument('--out',required=True);a=p.parse_args()
    result=audit(a.experiments);Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['metrics'],indent=2))
