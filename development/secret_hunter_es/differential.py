"""Official-engine one-step comparisons from development replays only."""
import copy,json,sys,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines
from development.secret_hunter_es.accounting import record_cases
sys.path.insert(0,str(ROOT/'development/secret_hunter_es/working/scripts'))
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
from tactical_model import supported,prepare,transition,options
from action_validator import legal
from state_features import with_public_history


def projection(s):
    out={}
    for side in ('you','opponent'):
        x=s[side]
        out[side]={'hero':[x['hero']['health'],x['hero'].get('armor',0)],
                   'board':[[m['card_id'],m['attack'],m['health'],bool(m.get('taunt')),bool(m.get('divine_shield')),bool(m.get('frozen')),bool(m.get('stealth'))] for m in x['board']],
                   'secrets':[c['card_id'] for c in x.get('secrets',[])],
                   'weapon':[(x.get('weapon') or {}).get(k) for k in ('card_id','attack','durability')]}
    out['mana']=s['you']['mana'];out['hand']=[c['entity_id'] for c in s['you']['hand']]
    return out


def main():
    folder=ROOT/'experiments/program-f2-confirmation';specs={o['name']:o for o in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
    rows=readlines(folder/'results.jsonl');cases=[];prefix=0
    for row in [r for r in rows if not r["score"]]:
        seat=row['seat'];g=folder/'games'/row['game'];obs={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};indices={1:0,2:0};history=[]
        own=load_deck(ROOT/'secret-hunter-program/deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed']);selected=0
        while not e.over:
            who,_=e.pending();z=obs[who][indices[who]];actual=e.view(who)
            if who==seat:
                s=z['state']  # Recorded official public observation, including public turn history.
                if supported(s) and s.get('turn',0)>=6 and selected<8:
                    initial=prepare(s)
                    # Public legal templates are the only root action source.
                    actions=[z['action']]+list(options(initial))
                    done=set();tested=0
                    for a in actions:
                        key=json.dumps(a,sort_keys=True)
                        if key in done or not legal(s,a):continue
                        done.add(key);projected=transition(initial,a)
                        if projected is None:continue
                        branch=copy.deepcopy(e);accepted=branch.step(who,a).accepted
                        engine=branch.view(who);left,right=projection(projected),projection(engine)
                        cases.append({'game':row['game'],'seq':z['state']['seq'],'action':a,'accepted':accepted,'equal':left==right,'expected':left if left!=right else None,'actual':right if left!=right else None})
                        tested+=1
                        if tested==3:break
                    if tested:selected+=1
            assert e.step(who,z['action']).accepted
            indices[who]+=1;prefix+=1
    record_cases('public-projector-differential',len(cases))
    result={'cases':len(cases),'matches':sum(c['equal'] for c in cases),'mismatches':sum(not c['equal'] for c in cases),'replayed_prefix_actions':prefix,'details':cases}
    write(ROOT/'docs/secret_hunter_es/differential.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='details'}))
    for c in cases:
        if not c['equal']:print(json.dumps(c))
if __name__=='__main__':main()
