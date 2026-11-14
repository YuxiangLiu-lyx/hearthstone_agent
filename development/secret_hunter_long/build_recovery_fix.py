"""Versioned recovery-turn refresh fix, backed by an actual engine boundary."""
import importlib.util
import json
import sys
import time
from development.secret_hunter_long.study import HERE,RUN
from development.secret_hunter_long.build import clone,audit
from development.secret_hunter_mcgs.train import atomic

def edit(dest):
    p=dest/'scripts/champion_recovery.py';s=p.read_text()
    s=s.replace('def recovery(state,cfg,deadline,max_nodes=16):','def prepare_recovery(state):')
    s=s.replace("if s is None:return {'supported':False,'nodes':0}","if s is None:return None")
    s=s.replace("return {'supported':False,'nodes':0}","return None")
    needle="    initial=value(s,cfg);best=initial;nodes=0;frontier=[s];seen=set()"
    replace="""    # A new own turn refreshes attack entitlement even if the prior
    # turn spent an attack or no weapon existed. No hypothetical draw is added.
    s['hero_attack_available']=True
    s['mana_spent']=0
    s['turn']=s.get('turn',0)+2
    return s

def recovery(state,cfg,deadline,max_nodes=16):
    s=prepare_recovery(state)
    if s is None:return {'supported':False,'nodes':0}
    if min(s['you']['hero']['health'],s['opponent']['hero']['health'])<=0:
        return {'supported':True,'nodes':0,'gain':0,'terminal':True}
    initial=value(s,cfg);best=initial;nodes=0;frontier=[s];seen=set()"""
    assert s.count(needle)==1;p.write_text(s.replace(needle,replace))
    p=dest/'scripts/turn_search.py';s=p.read_text()
    s=s.replace('evaluated=[];reply_nodes=0;complete=True','evaluated=[];reply_nodes=0;complete=True;recovery_calls=0;recovery_supported=0;recovery_nodes=0')
    s=s.replace("                reply_nodes+=rec['nodes']","                reply_nodes+=rec['nodes']\n                recovery_calls+=1;recovery_supported+=bool(rec.get('supported'));recovery_nodes+=rec['nodes']")
    s=s.replace("'scope':'visible attacks only; hidden cards excluded'}","'scope':'visible attacks, then known-hand recovery; hidden cards excluded',\n                         'recovery_calls':recovery_calls,'recovery_supported':recovery_supported,'recovery_nodes':recovery_nodes}")
    p.write_text(s)

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    source=clone('TRPLY2','TRPLY',edit=edit,generation=2,hypothesis='Actual-engine recovery boundary: refresh hero attack entitlement after spent previous attack, reset turn metadata; same32/16 budget; extra coverage counters only')
    sys.path.insert(0,str(source/'scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()
    from development.secret_hunter_mcgs.cases import fixture
    import tactical_model as model
    from public_response import prepare_reply
    old=load_module('old_recovery',HERE/'candidates/TRPLY/scripts/champion_recovery.py')
    new=load_module('new_recovery',source/'scripts/champion_recovery.py')
    e=fixture(hand=['EX1_536'],mana=3);e.player(1).hero.num_attacks=1
    s=e.view(1);root=model.prepare({**s,'planning_mode':'response','hero_attack_available':False})
    projected_reply=prepare_reply(root);assert projected_reply is not None
    captured=[];options=model.options
    try:
        model.options=lambda state:(captured.append(state) or [])
        old.recovery(projected_reply,json.loads((source/'config.json').read_text()),time.monotonic()+2)
    finally:model.options=options
    old_start=captured[0];new_start=new.prepare_recovery(projected_reply)
    assert e.step(1,{'type':'end_turn'}).accepted and e.step(2,{'type':'end_turn'}).accepted
    actual_before=e.view(1);card=next(c for c in actual_before['you']['hand'] if c['card_id']=='EX1_536')
    action={'type':'play_card','card':card['entity_id']}
    old_after=model.transition(old_start,action);new_after=model.transition(new_start,action)
    assert e.step(1,action).accepted;actual=e.view(1)
    hero=new_after['you']['hero']['entity_id']
    old_attacks=[a for a in model.options(old_after) if a['type']=='attack' and a['attacker']==hero]
    new_attacks=[a for a in model.options(new_after) if a['type']=='attack' and a['attacker']==hero]
    assert not old_attacks and new_attacks and actual['you']['hero']['can_attack']
    attack=new_attacks[0]
    assert e.step(1,attack).accepted
    record={'candidate':'TRPLY2','parent':'TRPLY','test':'spent old-turn attack; new own turn equip Bow and attack',
      'old_projected_has_hero_attack':False,'new_projected_has_hero_attack':True,'actual_engine_can_attack':True,
      'actual_bow_and_attack_accepted':True,'no_draw_assumption':'projection excludes the new draw, uses previously known Bow only',
      'budget':'unchanged 32 reply +16 recovery transitions per endpoint, same deadlines and endpoint cap','audit':audit(source)}
    atomic(RUN/'recovery-refresh-check.json',record);print(json.dumps({k:v for k,v in record.items() if k!='audit'}))

if __name__=='__main__':main()
