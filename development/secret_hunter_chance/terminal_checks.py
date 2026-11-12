"""Charge terminal chance fixtures as full attempts and check public terminal states."""
import json
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_chance.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
import tactical_model as m
import chance_model as chance


def project(s):
 return {k:{'hp':s[k]['hero']['health'],'board':[(x['card_id'],x['attack'],x['health']) for x in s[k]['board']]} for k in ('you','opponent')}


def main():
 reserve(Path(c.ARGS.out).stem,full=24,short=24)
 rows=[]
 for knives in (1,2):
  for hp in (1,2):
   for seed in range(71,77):
    e,i=c.fixture(own=['NEW1_019']*knives,enemy=['CS2_172']*3,hand=['EX1_538'],enemy_hp=30,seed=seed)
    e.player(3-i).hero.damage=e.player(3-i).hero.max_health-hp
    initial=m.prepare(e.view(i));a={'type':'play_card','card':initial['you']['hand'][0]['entity_id']}
    picks=[];base=e.game.random.sample
    def sample(pop,k,**kw):
     result=base(pop,k,**kw)
     if result and k==1:picks.append(result[0].entity_id)
     return result
    e.game.random.sample=sample;assert e.step(i,a).accepted;tape=()
    while True:
     try:pred=chance.project(initial,a,tape);break
     except chance.NeedChoice as need:tape+=(need.labels.index(picks[len(tape)]),)
    actual=e.view(i);rows.append({'knives':knives,'enemy_hp':hp,'seed':seed,'terminal':e.over,'equal':pred is not None and project(pred)==project(actual),'predicted':project(pred) if pred else None,'actual':project(actual)})
 write(ROOT/c.ARGS.out,{'n':len(rows),'matches':sum(x['equal'] for x in rows),'terminal':sum(x['terminal'] for x in rows),'cases':rows})
 finish(Path(c.ARGS.out).stem,completed_terminal=sum(x['terminal'] for x in rows),actual_short=len(rows))
 print(json.dumps({k:v for k,v in json.loads((ROOT/c.ARGS.out).read_text()).items() if k!='cases'}))
 for r in rows:
  if not r['equal']:print(json.dumps(r))
 assert all(r['equal'] for r in rows)
if __name__=='__main__':main()
