"""Public chance projections checked on recorded development prefixes."""
import copy,json,sys
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_chance.accounting import reserve,finish
C=ROOT/'development/secret_hunter_chance/candidates/C2';sys.path.insert(0,str(C/'scripts'))
import tactical_model as m
import chance_model as chance
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
from action_validator import legal


def project(s):
    return {k:{'hero':(s[k]['hero']['health'],s[k]['hero'].get('armor',0)),
               'board':[(x['card_id'],x['attack'],x['health'],x.get('max_health'),bool(x.get('taunt')),bool(x.get('divine_shield')),bool(x.get('frozen')),bool(x.get('silenced'))) for x in s[k]['board']],
               'hand_count':len(s[k]['hand']) if k=='you' else s[k].get('hand_size')} for k in ('you','opponent')}


def main():
    reserve('chance-development-differential',full=40,short=2500)
    src=ROOT/'experiments/secret-hunter-chance-m1-screen';specs={s['name']:s for s in json.loads((src/'config.json').read_text())['population']}
    rows=sorted(readlines(src/'results.jsonl'),key=lambda r:(r['score'],r['opponent'],r['seed'],r['seat']))
    cases=[];excluded=[];prefix=0;terminal=0
    for row in rows:
        if len(cases)>=160:break
        seat=row['seat'];own=load_deck(C/'deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
        obs={i:readlines(src/'games'/row['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0}
        while not e.over:
            who,_=e.pending();z=obs[who][idx[who]];s=z['state']
            if s.get('turn',0)>14 or idx[who]+2>=len(obs[who]):break
            if who==seat and s['phase']=='main' and m.supported(s) and any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in s['you']['board']):
                initial=m.prepare({**s,'planning_mode':'proof'})
                choices=[a for a in m.options(initial) if a['type']=='play_card'][:4]
                for action in choices:
                    if not legal(s,action):continue
                    b=copy.deepcopy(e);targets=[];base=b.game.random.sample
                    def sample(pop,k,**kw):
                        selected=base(pop,k,**kw)
                        if k==1 and selected and hasattr(selected[0],'entity_id'):targets.append(selected[0].entity_id)
                        return selected
                    b.game.random.sample=sample
                    accepted=b.step(who,action).accepted;terminal+=int(b.over);tape=();error=None
                    try:
                        while True:
                            try:pred=chance.project(initial,action,tape);break
                            except chance.NeedChoice as need:tape+=(need.labels.index(targets[len(tape)]),)
                    except (ValueError,IndexError) as exc:pred=None;error=str(exc)
                    if pred is None and error is None:
                        excluded.append({'game':row['game'],'seq':s['seq'],'action':action,'reason':'unsupported_effect'});continue
                    actual=b.view(seat);left=project(pred) if pred else None;right=project(actual)
                    cases.append({'game':row['game'],'seq':s['seq'],'action':action,'tape':tape,'equal':accepted and left==right,'error':error,'predicted':left if left!=right else None,'actual':right if left!=right else None})
            assert e.step(who,z['action']).accepted;idx[who]+=1;prefix+=1
            if len(cases)>=160:break
    report={'cases':cases,'excluded':excluded,'n':len(cases),'matches':sum(c['equal'] for c in cases),'prefix_actions':prefix,'terminal_branches':terminal}
    write(ROOT/'docs/secret_hunter_chance/development-differential.json',report)
    finish('chance-development-differential',actual_short=len(cases)+len(excluded),completed_terminal=terminal)
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','excluded')}))
    for c in cases:
        if not c['equal']:print(json.dumps(c))
    assert all(c['equal'] for c in cases)
if __name__=='__main__':main()
