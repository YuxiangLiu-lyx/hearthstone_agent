"""Earliest actionable loss divergences, with paired legal current-turn continuations."""
import argparse,copy,json,sys
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_tactics.accounting import record_cases
from hs_arena.engine import Engine
from hs_arena.deck import load_deck

def label(state,a):
    objects={x['entity_id']:x['card_id'] for side in ('you','opponent') for x in state[side]['board']+[state[side]['hero']]}
    objects.update({x['entity_id']:x['card_id'] for x in state['you']['hand']})
    return {k:objects.get(v,v) if k in ('card','attacker','target') else v for k,v in a.items()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',default='experiments/tactics-b0-development');p.add_argument('--candidate',default='development/secret_hunter_tactics/candidates/H4')
    p.add_argument('--out',default='docs/secret_hunter_tactics/losses.json');p.add_argument('--limit',type=int,default=12);args=p.parse_args()
    candidate=ROOT/args.candidate;sys.path.insert(0,str(candidate/'scripts'))
    from program_policy import decide
    cfg=json.loads((candidate/'config.json').read_text());folder=ROOT/args.folder
    specs={o['name']:o for o in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
    cases=[];branches=0;prefix=0
    for row in readlines(folder/'results.jsonl'):
        if row['score']:continue
        seat=row['seat'];g=folder/'games'/row['game'];obs={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};indices={1:0,2:0}
        own=load_deck(candidate/'deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        while not e.over:
            who,_=e.pending();z=obs[who][indices[who]]
            if who==seat and z['state']['phase']=='main':
                alternative,info=decide(z['state'],cfg)
                if alternative!=z['action']:
                    results=[]
                    for action in (z['action'],alternative):
                        b=copy.deepcopy(e);assert b.step(seat,action).accepted;steps=1;line=[label(z['state'],action)]
                        available=z['state'].get('hero_attack_available',z['state']['you']['hero'].get('can_attack',False))
                        if action.get('attacker')==z['state']['you']['hero']['entity_id']:available=False
                        while not b.over and b.pending()[0]==seat and steps<30:
                            s=b.view(seat);s['player']=seat;s['hero_attack_available']=available
                            a,_=decide(s,cfg);line.append(label(s,a));assert b.step(seat,a).accepted;steps+=1
                            if a.get('attacker')==s['you']['hero']['entity_id']:available=False
                        view=b.view(seat);y,o=view['you'],view['opponent'];branches+=1
                        results.append({'action':label(z['state'],action),'line':line,'terminal':b.over,'winner':b.winner if b.over else None,
                          'own_hp':y['hero']['health'],'enemy_hp':o['hero']['health'],
                          'own_board':[(m['card_id'],m['attack'],m['health']) for m in y['board']],
                          'enemy_board':[(m['card_id'],m['attack'],m['health']) for m in o['board']],
                          'own_secrets':[x['card_id'] for x in y.get('secrets',[])],'mana_left':y['mana']})
                    action_label=label(z['state'],alternative);cid=action_label.get('card')
                    category='missed_lethal' if info.get('reason')=='guaranteed_lethal' else 'secret_timing' if cid in ('EX1_610','EX1_611','EX1_554','EX1_533') else 'trade_or_placement' if alternative['type']=='attack' else 'combo_order' if cid in ('EX1_531','NEW1_019','EX1_538','DS1_070') else 'resource_use'
                    cases.append({'game':row['game'],'opponent':row['opponent'],'source_seq':z['state']['seq'],'turn':z['state']['turn'],
                        'category':category,'state':z['state'],'current':label(z['state'],z['action']),'alternative':action_label,'info':info,
                        'counterfactual':results,'scope':'Actual engine clones with the same candidate continuation through this turn only; nonterminal differences do not establish a changed match winner.'})
                    break
            assert e.step(who,z['action']).accepted;indices[who]+=1;prefix+=1
        if len(cases)>=args.limit:break
    record_cases(args.out,branches)
    taxonomy=['rules_or_simulation','missed_lethal','avoidable_death','trade_or_placement','secret_timing','resource_use','combo_order','mulligan','compute_budget','draw_or_random_variance']
    report={'source':args.folder,'candidate':args.candidate,'cases':cases,'branches':branches,'prefix_actions':prefix,
       'taxonomy':{k:sum(c['category']==k for c in cases) for k in taxonomy},'attribution':'Screened earliest differing main-turn decisions in losses, not a causal assignment of every defeat.'}
    write(ROOT/args.out,report)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
    for c in cases:print(c['game'],c['turn'],c['current'],c['alternative'],[(r['own_hp'],r['enemy_hp'],r['own_secrets'],r['terminal']) for r in c['counterfactual']])
if __name__=='__main__':main()
