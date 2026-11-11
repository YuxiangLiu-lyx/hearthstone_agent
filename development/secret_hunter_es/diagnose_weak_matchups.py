"""Earliest public-state divergences with legal official-engine continuations."""
import copy,json,sys
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines
from development.secret_hunter_es.accounting import record_cases
sys.path.insert(0,str(ROOT/'development/secret_hunter_es/working/scripts'))
from program_policy import decide
from state_features import with_public_history
from hs_arena.engine import Engine
from hs_arena.deck import load_deck


def main():
    folder=ROOT/'experiments/es-b0-confirmation';opps={o['name']:o for o in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
    baseline=json.loads((ROOT/'development/secret_hunter_es/candidates/C2/config.json').read_text())
    candidate_rows=readlines(ROOT/'experiments/es-final-confirmation/results.jsonl')
    losses={(r['opponent'],r['seed'],r['seat']) for r in candidate_rows if not r['score']}
    candidate=json.loads((ROOT/'development/secret_hunter_es/candidates/C2/config.json').read_text())
    cases=[];branches=0;prefix=0
    counts={}
    for row in readlines(folder/'results.jsonl'):
        if not row['score'] or (row['opponent'],row['seed'],row['seat']) not in losses:continue
        if row['opponent'] not in ('adversarial-zoo','search-paladin','control-mage') or counts.get(row['opponent'],0)>=4:continue
        seat=row['seat'];g=folder/'games'/row['game'];obs={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};indices={1:0,2:0}
        own=load_deck(ROOT/'secret-hunter-program/deck.json');other=load_deck(ROOT/opps[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        while not e.over:
            who,_=e.pending();z=obs[who][indices[who]]
            if who==seat and z['state']['phase']=='main':
                alternative,info=decide(z['state'],candidate)
                if alternative!=z['action']:
                    results=[]
                    for action in (z['action'],alternative):
                        branch=copy.deepcopy(e);assert branch.step(seat,action).accepted;steps=1
                        hero_available=z['state'].get('hero_attack_available',z['state']['you']['hero'].get('can_attack',False))
                        if action.get('attacker')==z['state']['you']['hero']['entity_id']:hero_available=False
                        # Same extended-coverage continuation on both branches isolates the changed action.
                        while not branch.over and branch.pending()[0]==seat and steps<20:
                            s=branch.view(seat);s['player']=seat
                            s['hero_attack_available']=hero_available
                            a,_=decide(s,baseline);assert branch.step(seat,a).accepted;steps+=1
                            if a.get('attacker')==s['you']['hero']['entity_id']:hero_available=False
                        view=branch.view(seat);y,o=view['you'],view['opponent']
                        results.append({'action':action,'steps':steps,'terminal':branch.over,'winner':branch.winner if branch.over else None,
                            'own_hp':y['hero']['health'],'enemy_hp':o['hero']['health'],'own_board':[(m['card_id'],m['attack'],m['health']) for m in y['board']],
                            'enemy_board':[(m['card_id'],m['attack'],m['health']) for m in o['board']],'own_secrets':[c['card_id'] for c in y.get('secrets',[])],'own_hand':[c['card_id'] for c in y['hand']],'mana_left':y['mana']})
                        branches+=1
                    cid=next((c['card_id'] for c in z['state']['you']['hand'] if c['entity_id']==alternative.get('card')),None)
                    category='secret_timing' if cid in ('EX1_610','EX1_611','EX1_554','EX1_533') else 'trade_or_placement' if alternative['type']=='attack' else 'combo_order' if cid=='DS1_070' else 'resource_use'
                    c={'game':row['game'],'opponent':row['opponent'],'source_seq':z['state']['seq'],'turn':z['state']['turn'],'state':z['state'],
                       'category':category,'current':z['action'],'alternative':alternative,'search':info.get('turn_search'),
                       'counterfactual':results,'evidence':'Official-engine legal continuation through the current turn under the same extended-coverage continuation policy. Nonterminal board differences do not prove a match win.'}
                    cases.append(c);counts[row['opponent']]=counts.get(row['opponent'],0)+1;break
            assert e.step(who,z['action']).accepted;indices[who]+=1;prefix+=1
        if len(cases)>=12:break
    categories=['rules_or_simulation','missed_lethal','avoidable_death','trade_or_placement','secret_timing','resource_use','combo_order','mulligan','compute_budget','draw_or_random_variance']
    report={'cases':cases,'short_continuations':branches,'prefix_actions':prefix,'taxonomy':{k:{'status':'screened; attribution requires case evidence','cases':sum(c['category']==k for c in cases)} for k in categories},'scope':'Earliest observed C2-versus-recorded-F2 decision divergence in selected new candidate regressions (F2 win, C2 loss), inspected after frozen confirmation; no further tuning, not a complete causal classification of every loss.'}
    record_cases('earliest-loss-counterfactuals',branches);write(ROOT/'docs/secret_hunter_es/weak-matchup-regressions.json',report)
    print(json.dumps({'cases':len(cases),'branches':branches,'prefix_actions':prefix}))
    for c in cases:print(c['game'],c['turn'],c['current'],c['alternative'],[(r['own_hp'],r['enemy_hp'],r['terminal']) for r in c['counterfactual']])
if __name__=='__main__':main()
