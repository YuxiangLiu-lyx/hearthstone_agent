"""Validate the narrow E1 endpoint fix against official turn-end transitions."""
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_response.accounting import reserve,finish
import tactical_model as m
from public_response import worst_reply
import time,json
reserve('e1-end-effects',short=60,seconds=120);rows=[]
for hp,full in ((1,False),(2,False),(5,True)):
 e,i=c.fixture(enemy=['EX1_597']+(['EX1_598']*6 if full else []));o=e.player(3-i);o.field[0].damage=o.field[0].max_health-hp
 for z in o.field:z.atk=0
 s=m.prepare(e.view(i));pred=m.end_effects(s,'opponent');e.step(i,{'type':'end_turn'});e.step(3-i,{'type':'end_turn'})
 key=lambda s:[(z['card_id'],z['attack'],z['health']) for z in s['opponent']['board']]
 rows.append({'health':hp,'full':full,'equal':key(pred)==key(e.view(i))});assert rows[-1]['equal']
write(ROOT/c.ARGS.out,rows);finish('e1-end-effects',actual_short=len(rows));print('passed',len(rows))
