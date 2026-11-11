"""Audit recorded win/loss decisions, with no claims of counterfactual match outcomes."""
import argparse
from collections import Counter
import json
from pathlib import Path

from development.secret_hunter_program.common import ROOT, write, readlines
from development.teacher_eval.compare import index


def inspect(folder):
    rows=readlines(folder/'results.jsonl')
    counters=Counter();cases=[]
    for row in rows:
        observations=readlines(folder/'games'/row['game']/f'p{row["seat"]}'/'observations.jsonl')
        trapped=set();casts=[];ending=None
        for record in observations:
            state,action=record['state'],record.get('action') or {}
            if state['phase']!='main':continue
            y,o=state['you'],state['opponent']
            if action['type']=='play_card':
                card=next(c for c in y['hand'] if c['entity_id']==action['card'])
                if card['card_id']=='DS1_185':
                    target=next((m for m in o['board']+[o['hero']] if m['entity_id']==action.get('target')), {})
                    kind='face' if action.get('target')==o['hero']['entity_id'] else 'minion'
                    counters['arcane_'+kind]+=1
                    casts.append({'seq':state['seq'],'turn':state['turn'],'target':target.get('name'),'kind':kind})
            if action['type']=='end_turn':
                ending=record
                trapped.update(c['card_id'] for c in y['hand'] if c['cost']>y['max_mana'] and c['card_id'] in ('EX1_543','EX1_534'))
        if row['score']==0:
            counters['losses']+=1
            counters['losses_with_unaffordable_krush_observed']+=('EX1_543' in trapped)
            counters['losses_with_unaffordable_highmane_observed']+=('EX1_534' in trapped)
        else:counters['wins']+=1
        if ending and len(cases)<12 and row['score']==0:
            state=ending['state']
            cases.append({'game':row['game'],'seed':row['seed'],'seat':row['seat'],'opponent':row['opponent'],
                          'observation':str((folder/'games'/row['game']/f'p{row["seat"]}'/'observations.jsonl').relative_to(ROOT)),
                          'last_end_turn_seq':state['seq'],'last_end_turn':state['turn'],
                          'own_health':state['you']['hero']['health'],'enemy_health':state['opponent']['hero']['health'],
                          'own_board':len(state['you']['board']),'enemy_board':len(state['opponent']['board']),
                          'hand':[c['card_id'] for c in state['you']['hand']], 'arcane_casts':casts})
    return {'counts':dict(counters),'loss_examples':cases}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('baseline');parser.add_argument('candidate')
    parser.add_argument('--out',required=True);args=parser.parse_args()
    folders=[ROOT/args.baseline,ROOT/args.candidate]
    a,b=[index(readlines(p/'results.jsonl')) for p in folders]
    assert a.keys()==b.keys()
    discordant=[{'opponent':k[0],'seed':k[1],'seat':k[2],'baseline_win':a[k]['score'],
                 'candidate_win':b[k]['score'],'baseline_game':a[k]['game'],'candidate_game':b[k]['game']}
                for k in sorted(a) if a[k]['score']!=b[k]['score']]
    write(ROOT/args.out,{'baseline':inspect(folders[0]),'candidate':inspect(folders[1]),
          'changed_winners':discordant,'limitation':'Descriptive observations only. Deck substitutions change shuffle/draw trajectories even on shared seeds. A stranded card or different action does not prove a cause of defeat or a forced alternative win.'})


if __name__=='__main__':
    main()
