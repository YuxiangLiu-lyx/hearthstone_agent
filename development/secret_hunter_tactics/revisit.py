"""Revisit specific prior-round regressions without treating them as unseen evidence."""
import json,copy,sys
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_tactics.accounting import record_cases
from development.secret_hunter_tactics.diagnose import label
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
src=ROOT/'development/secret_hunter_tactics/release/secret-hunter-program';sys.path.insert(0,str(src/'scripts'))
from program_policy import decide
cfg=json.loads((src/'config.json').read_text());folder=ROOT/'experiments/es-b0-confirmation'
rows={r['game']:r for r in readlines(folder/'results.jsonl')}
specs={r['name']:r for r in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
selected={'268393d8aff7447c','fc6bd930cf9548ab','12a99366782242d1','49779cdeafd3459b'}
cases=[];branches=0
for path in ['regressions.json','weak-matchup-regressions.json']:
    for case in json.loads((ROOT/'docs/secret_hunter_es'/path).read_text())['cases']:
        if case['game'] not in selected:continue
        row=rows[case['game']];seat=row['seat'];own=load_deck(src/'deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        g=folder/'games'/row['game'];obs={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};idx={1:0,2:0}
        while True:
            who,_=e.pending();z=obs[who][idx[who]]
            if who==seat and z['state']['seq']==case['source_seq']:break
            assert e.step(who,z['action']).accepted;idx[who]+=1
        state=z['state'];new,info=decide(state,cfg);out=[]
        for name,action in [('F2',case['current']),('C2',case['alternative']),('H7',new)]:
            b=copy.deepcopy(e);assert b.step(seat,action).accepted;line=[label(state,action)]
            available=state.get('hero_attack_available',state['you']['hero'].get('can_attack',False))
            if action.get('attacker')==state['you']['hero']['entity_id']:available=False
            while not b.over and b.pending()[0]==seat and len(line)<30:
                s=b.view(seat);s['hero_attack_available']=available
                a,_=decide(s,cfg);line.append(label(s,a));assert b.step(seat,a).accepted
                if a.get('attacker')==s['you']['hero']['entity_id']:available=False
            view=b.view(seat);y,o=view['you'],view['opponent'];branches+=1
            out.append({'forced_first_action_from':name,'line':line,'terminal':b.over,'winner':b.winner if b.over else None,
              'own_hp':y['hero']['health'],'enemy_hp':o['hero']['health'],'own_secrets':[c['card_id'] for c in y.get('secrets',[])],
              'own_board':[(m['card_id'],m['attack'],m['health']) for m in y['board']],
              'enemy_board':[(m['card_id'],m['attack'],m['health']) for m in o['board']]})
        cases.append({'source':f'docs/secret_hunter_es/{path}','game':case['game'],'turn':case['turn'],'state':state,'counterfactual':out})
report={'cases':cases,'branches':branches,'scope':'Prior-round holdouts are used development data. Same H7 current-turn continuation after each forced root action. All nonterminal endpoints are not counterfactual full-match wins.'}
record_cases('prior loss case revisits',branches);write(ROOT/'docs/secret_hunter_tactics/revisited-cases.json',report)
for c in cases:
 print(c['game'],c['turn'])
 for r in c['counterfactual']:print(r)
