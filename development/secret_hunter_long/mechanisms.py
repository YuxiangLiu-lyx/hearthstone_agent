"""Card effects are checked in the frozen course engine, not live HS memory."""
from collections import Counter
import json
import sys
from development.secret_hunter_long.study import HERE,RUN
from development.secret_hunter_mcgs.train import atomic
sys.path.insert(0,str(HERE/'candidates/B/scripts'))
from development.secret_hunter_mcgs.mcgs_init import initialize
initialize()
from development.secret_hunter_mcgs.cases import fixture
from hearthstone.enums import Zone
from hs_arena.cards import load
from action_validator import legal
import tactical_model as model

def main():
    rows=[]
    e=fixture(hand=['DS1_185'],enemy=['EX1_319'],mana=1)
    s=e.view(1);a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'target':s['opponent']['board'][0]['entity_id']}
    predicted=model.transition(model.prepare(s),a)
    assert legal(s,a) and e.step(1,a).accepted and not e.view(1)['opponent']['board']
    assert predicted is not None and not predicted['opponent']['board']
    rows.append({'name':'arcane_one_mana_two_damage_removes_flame_imp','model_matches':True})
    e=fixture(hand=['EX1_162'],own=['CS2_171','CS2_171'],mana=2)
    s=e.view(1);a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'position':1}
    predicted=model.transition(model.prepare(s),a)
    assert legal(s,a) and e.step(1,a).accepted
    actual=e.view(1)
    assert [x['attack'] for x in actual['you']['board']]==[2,2,2]
    assert [x['attack'] for x in predicted['you']['board']]==[2,2,2]
    rows.append({'name':'dire_wolf_two_mana_two_two_adjacent_aura','engine_attacks':[2,2,2],'model_matches':True})
    e=fixture(hand=['EX1_543'],mana=9,enemy_hp=8)
    s=e.view(1);a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'position':0}
    assert e.step(1,a).accepted;s=e.view(1)
    a={'type':'attack','attacker':s['you']['board'][0]['entity_id'],'target':s['opponent']['hero']['entity_id']}
    assert legal(s,a) and e.step(1,a).accepted and e.over and e.winner==1
    rows.append({'name':'krush_nine_mana_eight_charge','terminal':True})
    # Both protected Hounds synergies are exercised via actual summons and death.
    for combo in ('EX1_531','NEW1_019'):
        e=fixture(own=[combo],hand=['EX1_538'],enemy=['CS2_171','CS2_171','CS2_171'],mana=3)
        s=e.view(1);a={'type':'play_card','card':s['you']['hand'][0]['entity_id']}
        assert legal(s,a) and e.step(1,a).accepted
        s=e.view(1);dogs=[m for m in s['you']['board'] if m['card_id']=='EX1_538t']
        assert len(dogs)==3 and all(m['can_attack'] for m in dogs)
        if combo=='EX1_531':
            a={'type':'attack','attacker':dogs[0]['entity_id'],'target':s['opponent']['board'][0]['entity_id']}
            assert e.step(1,a).accepted
            hyena=next(m for m in e.view(1)['you']['board'] if m['card_id']=='EX1_531')
            assert (hyena['attack'],hyena['health'])==(4,3)
        else:
            knife_damage=[x for ev in e.events if (x:=ev.view(1)) and x.get('event')=='damage' and (x.get('source') or {}).get('card_id')=='NEW1_019']
            assert len(knife_damage)==3
        rows.append({'name':combo+'_hounds','actual_engine_passed':True})
    e=fixture(hand=['EX1_610'],enemy=['CS2_171'],mana=5)
    e.player(1).card('EX1_536',zone=Zone.PLAY);s=e.view(1)
    assert e.step(1,{'type':'play_card','card':s['you']['hand'][0]['entity_id']}).accepted
    assert e.step(1,{'type':'end_turn'}).accepted;s=e.view(2)
    assert e.step(2,{'type':'attack','attacker':s['you']['board'][0]['entity_id'],'target':s['opponent']['hero']['entity_id']}).accepted
    assert e.view(1)['you']['weapon']['durability']==3
    rows.append({'name':'own_secret_reveal_bow_durability','durability':3})
    catalog=load();decks={}
    for p in sorted((HERE/'candidates').iterdir()):
        if not p.is_dir():continue
        ids=json.loads((p/'deck.json').read_text())['cards']
        decks[p.name]={'curve':dict(Counter(catalog[c]['cost'] for c in ids)),
          'beasts':sum(catalog[c].get('race')=='BEAST' for c in ids),
          'secrets':sum('SECRET' in catalog[c].get('mechanics',[]) for c in ids),
          'bows':ids.count('EX1_536'),'card_effects':{c:catalog[c] for c in set(ids) if c in ('DS1_185','EX1_162','EX1_543')}}
    atomic(RUN/'mechanism-checks.json',{'checks':rows,'deck_structure':decks,'passed':True})
    print(json.dumps({'checks':len(rows),'decks':decks}))

if __name__=='__main__':main()
