"""Archived M2 coverage and local response isolation regression fixtures."""
import json,sys,time,copy
from development.secret_hunter_dgm.accounting import reserve,finish
from development.secret_hunter_program.common import ROOT,write
reserve('local-coverage-checks',short=100,full=2)
# Existing fixtures validate official card semantics, under the selected candidate.
from development.secret_hunter_tactics import checks as c
import tactical_model as m
rows=[]
for own,enemy in [([],['EX1_096']),([],['EX1_012']),([],['EX1_608']),([],['NEW1_012'])]:
 e,i=c.fixture(own=own,enemy=enemy,hand=['EX1_539'])
 s=m.prepare({**e.view(i),'planning_mode':'proof'});a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'target':s['opponent']['board'][0]['entity_id']}
 pred=m.transition(s,a);assert pred is not None
 assert e.step(i,a).accepted
 real=e.view(i)
 def key(v):return (v['opponent']['hand_size'],v['opponent']['deck_remaining'],[(x['card_id'],x['health']) for x in v['opponent']['board']])
 assert key(pred)==key(real),(key(pred),key(real));rows.append({'enemy':enemy,'equal':True})
e,i=c.fixture(own=['EX1_096'],enemy=['CS2_200']);s=m.prepare(e.view(i));a={'type':'attack','attacker':s['you']['board'][0]['entity_id'],'target':s['opponent']['board'][0]['entity_id']};assert m.transition(s,a) is None
write(ROOT/c.ARGS.out,{'rows':rows,'own_unknown_draw_stays_unsupported':True});finish('local-coverage-checks',actual_short=5);print('passed 5 local effects')
