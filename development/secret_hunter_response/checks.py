"""Official-engine differential tests for public response hypotheses and turn closure."""
import copy,json,time
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_response.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
import tactical_model as m
import response_search as rs
from public_response import prepare_reply
from hearthstone.enums import Zone

def projection(s):
 return {key:{'hero':(s[key]['hero']['health'],s[key]['hero'].get('armor',0),s[key]['hero'].get('frozen',False)), 'board':[(z['card_id'],z['attack'],z['health'],z['max_health'],bool(z.get('taunt')),bool(z.get('divine_shield')),bool(z.get('frozen'))) for z in s[key]['board']]} for key in ('you','opponent')}
def main():
 name='responses-'+__import__('pathlib').Path(c.ARGS.out).stem;reserve(name,short=400,full=4,seconds=300);rows=[]
 for cid in ('CS2_188','EX1_046','EX1_093','EX1_058','EX1_162','CS2_179','CS2_172','EX1_008','EX1_029','EX1_302','EX1_308','DS1_185','EX1_539','CS2_024','CS2_029'):
  for at in (0,1):
   e,i=c.fixture(own=['CS2_200','EX1_008'],enemy=['CS2_172','EX1_393'],hand=[])
   p,o=e.player(i),e.player(3-i);s=prepare_reply(m.prepare({**e.view(i),'planning_mode':'response'}));assert s is not None
   assert e.step(i,{'type':'end_turn'}).accepted
   o.max_mana=10;o.used_mana=0
   for card in list(o.hand):card.zone=Zone.GRAVEYARD
   o.give(cid);o.give('CS2_172');s['opponent']['hand_size']=2
   h={'card_id':cid,'mana':10,'hand_size':2};s['_reply_mana']=10
   actions=list(rs.hypothetical_plays(s,h));a=actions[min(at,len(actions)-1)]
   pred=rs.play_hypothesis(s,h,a);t,pos=a
   actual={'type':'play_card','card':next(x['entity_id'] for x in e.view(3-i)['you']['hand'] if x['card_id']==cid)}
   if m.CATALOG[cid]['type']=='MINION':actual['position']=pos
   if t is not None:actual['target']=t
   assert e.step(3-i,actual).accepted,actual
   row={'card':cid,'variant':at,'equal':pred is not None and projection(pred)==projection(e.view(i)),'predicted':projection(pred) if pred else None,'actual':projection(e.view(i))}
   rows.append(row)
   if pred is not None:
    closed=rs.end_turn(pred,'opponent');assert e.step(3-i,{'type':'end_turn'}).accepted
    rows.append({'card':cid,'variant':at,'end_equal':closed is not None and projection(closed)==projection(e.view(i)),'predicted':projection(closed) if closed else None,'actual':projection(e.view(i))})
 for health,full in ((1,False),(2,False),(5,True)):
  e,i=c.fixture(enemy=['EX1_597']+(['EX1_598']*6 if full else []));o=e.player(3-i);o.field[0].damage=o.field[0].max_health-health
  s=m.prepare(e.view(i));r=rs.end_turn(s,'opponent');e.step(i,{'type':'end_turn'});e.step(3-i,{'type':'end_turn'})
  rows.append({'effect':'imp_master','health':health,'full':full,'equal':r is not None and projection(r)==projection(e.view(i)),'predicted':projection(r),'actual':projection(e.view(i))})
 e,i=c.fixture(enemy=['NEW1_019','EX1_597']);assert rs.end_turn(m.prepare(e.view(i)),'opponent') is None
 # A legal 9-mana route removes two Taunts before Krush uses its own charge attack.
 e,i=c.fixture(own=['CS2_200','CS2_200'],enemy=['CS2_121','CS2_121'],hand=['EX1_543'],mana=9,enemy_hp=8)
 s=e.view(i);trace=[]
 for own,enemy in zip(s['you']['board'],s['opponent']['board']):
  a={'type':'attack','attacker':own['entity_id'],'target':enemy['entity_id']};assert e.step(i,a).accepted;trace.append(a)
 card=e.view(i)['you']['hand'][0];a={'type':'play_card','card':card['entity_id'],'position':2};assert e.step(i,a).accepted;trace.append(a)
 k=next(z for z in e.view(i)['you']['board'] if z['card_id']=='EX1_543');a={'type':'attack','attacker':k['entity_id'],'target':e.view(i)['opponent']['hero']['entity_id']};assert e.step(i,a).accepted;trace.append(a);assert e.over and e.winner==i
 rows.append({'effect':'krush_9_mana_two_taunts','equal':True,'trace':trace,'winner':i})
 write(ROOT/c.ARGS.out,{'rows':rows,'n':len(rows),'passed':sum(x.get('equal',x.get('end_equal',False)) for x in rows),'random_imp_juggler_rejected':True})
 finish(name,actual_short=len(rows)+1,actual_full=1)
 failures=[x for x in rows if not x.get('equal',x.get('end_equal',False))];print(json.dumps({'n':len(rows),'failures':failures}));assert not failures
if __name__=='__main__':main()
