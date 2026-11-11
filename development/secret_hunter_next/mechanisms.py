"""Official-engine differentials for new deterministic effects and conservative guards."""
import copy,json,sys
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_next.accounting import reserve,finish
# Shared fixture accepts --candidate/--out; its main and historical ledger are not executed.
from development.secret_hunter_tactics import checks as c
import tactical_model as m
from public_response import prepare_reply,attack
from state_features import is_beast

cases=[]
def project(s):
 return {key:{'hero':s[key]['hero']['health'],'board':[(x['card_id'],x['attack'],x['health'],x.get('taunt',False),x.get('divine_shield',False)) for x in s[key]['board']]} for key in ('you','opponent')}
def compare(label,pred,e,i):
 actual=e.view(i);cases.append({'label':label,'equal':pred is not None and project(pred)==project(actual),'predicted':project(pred) if pred else None,'actual':project(actual)})
def main():
 reserve('mechanisms-v2',short=120)
 for damaged in (False,True):
  for silenced in (False,True):
   for aura in (False,True):
    e,i=c.fixture(own=['EX1_393']+(['EX1_162'] if aura else []),enemy=['CS2_172'],hand=['DS1_185'])
    x=e.player(i).field[0]
    if damaged:x.hit(1)
    if silenced:x.silence()
    s=e.view(i);p=m.prepare(s);compare('amani_initial',p,e,i)
    # Healing must remove enrage without removing permanent/aura attack.
    x.heal(x,10);p['you']['board'][0]['health']=p['you']['board'][0]['max_health'];m.refresh(p);compare('amani_healed',p,e,i)
    s=e.view(i);a={'type':'attack','attacker':x.entity_id,'target':e.player(3-i).field[0].entity_id};pred=m.transition(m.prepare(s),a);assert e.step(i,a).accepted;compare('amani_combat',pred,e,i)
 for hp in (1,2,3):
  for count in (1,6,7):
   for silenced in (False,True):
    e,i=c.fixture(own=['EX1_597']+['EX1_598']*(count-1));x=e.player(i).field[0];x.damage=x.max_health-hp
    if silenced:x.silence()
    s=e.view(i);pred=m.end_effects(m.prepare(s),'you');assert e.step(i,{'type':'end_turn'}).accepted;compare('master_end_capacity',pred,e,i)
 for secret in ('EX1_610','EX1_611','EX1_554'):
  e,i=c.fixture(own=['EX1_531','EX1_597'],enemy=['EX1_393','EX1_162'],hand=[secret]);c.play(e,i,secret)
  s=e.view(i);pred=prepare_reply(m.prepare(s));assert e.step(i,{'type':'end_turn'}).accepted;compare('master_secret_end',pred,e,i)
  a={'type':'attack','attacker':e.player(3-i).field[0].entity_id,'target':e.player(i).hero.entity_id if secret!='EX1_554' else e.player(i).field[0].entity_id}
  pred=attack(pred,a);assert e.step(3-i,a).accepted;compare('amani_secret_attack',pred,e,i)
 e,i=c.fixture(own=['EX1_597','NEW1_019']);assert m.end_effects(m.prepare(e.view(i)),'you') is None
 assert not is_beast({'card_id':'EX1_598'}) and is_beast({'card_id':'EX1_554t'})
 report={'cases':cases,'matches':sum(x['equal'] for x in cases),'n':len(cases),'guards':['Imp is not Beast','Snake is Beast','Master plus Juggler end trigger rejected']}
 write(ROOT/c.ARGS.out,report);finish('mechanisms-v2',actual_short=len(cases)+3)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
 for x in cases:
  if not x['equal']:print(json.dumps(x))
 assert all(x['equal'] for x in cases)
if __name__=='__main__':main()
