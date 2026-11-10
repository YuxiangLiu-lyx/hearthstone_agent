"""Visible-state diagnostics; labels are screening signals, not causal loss proofs."""
import argparse
import json
import sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('experiment');p.add_argument('--out',required=True);args=p.parse_args()
    sys.path.insert(0,str(Path('development/candidates/v2-search/scripts').resolve()))
    from planner import lethal_plan,supported
    rows=[json.loads(l) for l in (Path(args.experiment)/'games.jsonl').read_text().splitlines()]
    stats={'games':len(rows),'decisions':0,'supported_lethal_checks':0,'end_turn_possible_lethals':[],
           'unused_mana_turns':0,'unused_mana_total':0,'loss_cases':[],'disclaimer':
           'Conservative search covers a subset of effects. No flag does not prove no missed lethal. Loss labels are hypotheses.'}
    for g in rows:
        if not g.get('observations'):continue
        timeline=[json.loads(l) for l in Path(g['observations']).read_text().splitlines()]
        last=None
        for row in timeline:
            s,a=row['state'],row['action'];stats['decisions']+=1
            if s['phase']!='main':continue
            last=s
            if a['type']=='end_turn':
                stats['unused_mana_total']+=s['you']['mana'];stats['unused_mana_turns']+=1
                if supported(s):
                    stats['supported_lethal_checks']+=1
                    plan=lethal_plan(s,budget_s=.03,max_nodes=800)
                    if plan:stats['end_turn_possible_lethals'].append({'observations':g['observations'],'seq':s['seq'],'plan':plan})
        if not g['score'] and last:
            enemy_attack=sum(m['attack'] for m in last['opponent']['board'])
            own_attack=sum(m['attack'] for m in last['you']['board'])
            labels=[]
            if enemy_attack>own_attack:labels.append('board_deficit')
            if len(last['you']['hand'])<=1:labels.append('resource_exhaustion')
            if enemy_attack>=last['you']['hero']['health']+last['you']['hero'].get('armor',0):labels.append('visible_lethal_threat')
            if not labels:labels=['other_or_hidden_response']
            stats['loss_cases'].append({'seed':g['seed'],'opponent':g['opponent'],'replay':g['replay'],
                'last_seq':last['seq'],'labels':labels,'own_health':last['you']['hero']['health'],
                'enemy_health':last['opponent']['hero']['health'],'own_attack':own_attack,'enemy_attack':enemy_attack})
    Path(args.out).write_text(json.dumps(stats,indent=2));print(json.dumps({k:v for k,v in stats.items() if k not in ('loss_cases','end_turn_possible_lethals')},indent=2))
    print('possible missed lethals',len(stats['end_turn_possible_lethals']),'loss cases',len(stats['loss_cases']))

if __name__=='__main__':main()
