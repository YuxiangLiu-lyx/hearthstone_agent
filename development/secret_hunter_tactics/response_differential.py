"""Test reply projections on historical public end-turn states against the official engine."""
import copy,json,sys
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_tactics.accounting import record_cases
sys.path.insert(0,str(ROOT/'development/secret_hunter_tactics/working/scripts'))
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
from tactical_model import supported,prepare
from public_response import prepare_reply,attack,attacks
from development.secret_hunter_es.differential import projection

def project(s):
    p=projection(s);p.pop('mana');p.pop('hand');return p

def main():
    folder=ROOT/'experiments/es-b0-confirmation'
    specs={x['name']:x for x in json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())['opponents']}
    rows=readlines(folder/'results.jsonl')
    selected=[r for r in rows if not r['score']][:12]+[r for r in rows if r['score']][:8]
    cases=[];unsupported=0;prefix=0
    for row in selected:
        seat=row['seat'];g=folder/'games'/row['game'];obs={p:readlines(g/f'p{p}/observations.jsonl') for p in (1,2)};indices={1:0,2:0}
        own=load_deck(ROOT/'secret-hunter-program/deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        while not e.over:
            who,_=e.pending();z=obs[who][indices[who]];s=z['state']
            if who==seat and z['action']['type']=='end_turn' and supported(s):
                r=prepare_reply(prepare(s));b=copy.deepcopy(e);b.step(who,z['action'])
                if r is not None and not b.over:
                    for a in list(attacks(r))[:10]:
                        predicted=attack(r,a)
                        if predicted is None:unsupported+=1;continue
                        branch=copy.deepcopy(b);ok=branch.step(3-seat,a).accepted
                        left,right=project(predicted),project(branch.view(seat))
                        cases.append({'game':row['game'],'seq':s['seq'],'action':a,'equal':ok and left==right,'accepted':ok,
                          'expected':None if left==right else left,'actual':None if left==right else right})
            assert e.step(who,z['action']).accepted
            indices[who]+=1;prefix+=1
    record_cases('historical public response differential',len(cases))
    report={'cases':len(cases),'matches':sum(x['equal'] for x in cases),'unsupported':unsupported,'prefix_actions':prefix,'details':cases}
    write(ROOT/'docs/secret_hunter_tactics/response-differential.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='details'}))
    for x in cases:
        if not x['equal']:print(json.dumps(x))
if __name__=='__main__':main()
