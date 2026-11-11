"""Validate hidden draw boundaries without exposing or inventing card identities."""
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_next.accounting import reserve,finish
import tactical_model as m
from public_response import prepare_reply,attack
cases=[]
def main():
 reserve('local-coverage-v2',short=100)
 for cid in ('EX1_096','EX1_012','EX1_608','NEW1_012'):
  e,i=c.fixture(own=['CS2_200'],enemy=[cid],hand=['DS1_185']);s=e.view(i);assert m.supported(s)
  a={'type':'attack','attacker':e.player(i).field[0].entity_id,'target':e.player(3-i).field[0].entity_id};pred=m.transition(m.prepare(s),a);assert pred is not None;assert e.step(i,a).accepted
  real=e.view(i)
  for key in ('hand_size','deck_remaining'):assert pred['opponent'][key]==real['opponent'][key],(cid,key)
  assert [(x['card_id'],x['health']) for x in pred['you']['board']]==[(x['card_id'],x['health']) for x in real['you']['board']]
  cases.append({'card':cid,'matched_public_draw_and_combat':True})
 for key,value in [('deck_remaining',0),('hand_size',10)]:
  e,i=c.fixture(own=['CS2_200'],enemy=['EX1_096']);s=e.view(i);s['opponent'][key]=value
  a={'type':'attack','attacker':e.player(i).field[0].entity_id,'target':e.player(3-i).field[0].entity_id};assert m.transition(m.prepare(s),a) is None
 e,i=c.fixture(own=['EX1_096'],enemy=['CS2_200']);s=e.view(i);a={'type':'attack','attacker':e.player(i).field[0].entity_id,'target':e.player(3-i).field[0].entity_id};assert m.transition(m.prepare(s),a) is None
 report={'n':7,'matches':7,'cases':cases,'guards':['own unknown draw','enemy fatigue','enemy hand burn']};write(ROOT/c.ARGS.out,report);finish('local-coverage-v2',actual_short=7);print(report)
if __name__=='__main__':main()
