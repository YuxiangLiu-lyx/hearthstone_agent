"""Differential chance traces against official-engine RNG outcomes, offline only."""
import json,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_dgm.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
import tactical_model as m
import chance_model as chance


def projection(s):
    return {k:{'hero':(s[k]['hero']['health'],s[k]['hero'].get('armor',0)),
               'board':[(x['card_id'],x['attack'],x['health'],x['max_health'],bool(x.get('taunt')),bool(x.get('divine_shield')),bool(x.get('silenced'))) for x in s[k]['board']]} for k in ('you','opponent')}


def main():
    reserve('chance-'+Path(c.ARGS.out).stem,full=10,short=1200)
    rows=[];terminals=0
    worlds=[(['NEW1_019'],['CS2_172']),(['NEW1_019'],['EX1_008']),
            (['NEW1_019'],['EX1_393','EX1_162']),(['NEW1_019','EX1_162'],['EX1_556','CS2_172']),
            (['NEW1_019','NEW1_019'],['CS2_172','CS2_172']),
            (['NEW1_019','EX1_531'],['EX1_029','EX1_598','EX1_598']),
            (['NEW1_019']+['EX1_598']*5,['CS2_172']*5),
            (['NEW1_019','EX1_531'],['EX1_534','EX1_531'])]
    for wi,(own,enemy) in enumerate(worlds):
      for cid in ('EX1_538','EX1_029','DS1_070','NEW1_019'):
       for seed in (71,72,73):
        e,i=c.fixture(own=own,enemy=enemy,hand=[cid],seed=seed)
        e.player(3-i).hero.armor=2
        # The damaged deathrattle world tests pending death and token ordering.
        if wi==7:e.player(3-i).field[0].damage=4
        s=m.prepare({**e.view(i),'planning_mode':'proof'})
        hand=s['you']['hand'][0];a={'type':'play_card','card':hand['entity_id']}
        if cid!='EX1_538':a['position']=len(own)
        if cid=='DS1_070':
            beasts=[x for x in s['you']['board'] if m.is_beast(x)]
            if beasts:a['target']=beasts[0]['entity_id']
        targets=[];base=e.game.random.sample
        def sample(pop,k,**kw):
            result=base(pop,k,**kw)
            if k==1 and result and hasattr(result[0],'entity_id'):targets.append(result[0].entity_id)
            return result
        e.game.random.sample=sample
        assert e.step(i,a).accepted
        terminals+=int(e.over)
        tape=();error=None
        try:
            while True:
                try:pred=chance.project(s,a,tape);break
                except chance.NeedChoice as need:
                    tape+=(need.labels.index(targets[len(tape)]),)
        except (ValueError,IndexError) as exc:pred=None;error=str(exc)
        actual=e.view(i)
        rows.append({'world':wi,'card':cid,'seed':seed,'targets':targets,'tape':tape,
                     'equal':pred is not None and projection(pred)==projection(actual),
                     'prediction':projection(pred) if pred else None,'actual':projection(actual),'error':error})
    # Exact two-target branch and deterministic sampling, with no claimed proof.
    e,i=c.fixture(own=['NEW1_019'],enemy=['CS2_172'],hand=['EX1_029'])
    s=m.prepare(e.view(i));a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'position':1}
    r=chance.outcomes(s,a,time.monotonic()+2)
    assert r['exact'] and len(r['outcomes'])==2 and sum(p for p,_ in r['outcomes'])==1
    e,i=c.fixture(own=['NEW1_019']*2,enemy=['CS2_172']*6,hand=['EX1_538'])
    s=m.prepare(e.view(i));a={'type':'play_card','card':s['you']['hand'][0]['entity_id']}
    r=chance.outcomes(s,a,time.monotonic()+2);r2=chance.outcomes(s,a,time.monotonic()+2)
    assert r['supported'] and not r['exact'] and r['outcomes']==r2['outcomes']
    assert abs(sum(p for p,_ in r['outcomes'])-1)<1e-9
    write(ROOT/c.ARGS.out,{'cases':rows,'n':len(rows),'matches':sum(r['equal'] for r in rows),'terminal_games':terminals,'distribution_guards':['exact mass one','sampled public determinism','sample mass one']})
    finish('chance-'+Path(c.ARGS.out).stem,actual_short=len(rows)+3,completed_terminal=terminals)
    print(json.dumps({'n':len(rows),'matches':sum(r['equal'] for r in rows)}))
    for r in rows:
        if not r['equal']:print(json.dumps(r))
    assert all(r['equal'] for r in rows)
if __name__=='__main__':main()
