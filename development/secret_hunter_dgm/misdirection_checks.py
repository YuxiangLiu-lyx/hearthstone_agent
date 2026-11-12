"""Exact retarget, Bow durability and combat differential, official engine only."""
import copy,json
from development.secret_hunter_dgm.accounting import reserve,finish
from development.secret_hunter_program.common import ROOT,write
reserve('misdirection-checks',short=150,full=5)
from development.secret_hunter_tactics import checks as c
import tactical_model as m
from chance_reply import transitions
from public_response import prepare_reply
rows=[]
def project(s):
 return {k:{'hero':(s[k]['hero']['health'],s[k]['hero'].get('armor',0)),'board':[(x['card_id'],x['attack'],x['health'],bool(x.get('divine_shield'))) for x in s[k]['board']], 'secrets':[x['card_id'] for x in s[k].get('secrets',[])],'weapon':[(s[k].get('weapon') or {}).get(t,0) for t in ('attack','durability')]} for k in ('you','opponent')}
for own,enemy in [([],['CS2_172']),(['EX1_080'],['CS2_172','CS2_200']),(['EX1_531','EX1_538t'],['CS2_172']),(['EX1_162','EX1_029'],['EX1_008','CS2_172'])]:
 for seed in range(71,77):
  e,i=c.fixture(own=own,enemy=enemy,hand=['EX1_533'],seed=seed)
  e.player(i).summon('EX1_536');c.play(e,i,'EX1_533')
  assert e.step(i,{'type':'end_turn'}).accepted
  s=m.prepare(e.view(i));s['you']['hero']['attack']=0
  for x in s['opponent']['board']:x['remaining_attacks']=int(x['attack']>0);x['can_attack']=True
  a={'type':'attack','attacker':s['opponent']['board'][0]['entity_id'],'target':s['you']['hero']['entity_id']}
  dist=transitions(s,a);assert dist is not None
  assert abs(sum(p for p,_ in dist)-1)<1e-10
  assert e.step(3-i,a).accepted
  real=e.view(i);equal=any(project(pred)==project(real) for _,pred in dist)
  rows.append({'own':own,'enemy':enemy,'seed':seed,'branches':len(dist),'equal':equal,'actual':project(real),'predictions':[project(v) for _,v in dist]})
write(ROOT/c.ARGS.out,{'n':len(rows),'matches':sum(r['equal'] for r in rows),'cases':rows});finish('misdirection-checks',actual_short=len(rows));print(len(rows),sum(r['equal'] for r in rows));assert all(r['equal'] for r in rows)
