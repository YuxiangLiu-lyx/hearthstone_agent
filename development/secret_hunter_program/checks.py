"""Engine microfixtures and real subprocess timing faults, never counted as matches."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from development.secret_hunter_program.common import ROOT,write
parser=argparse.ArgumentParser()
parser.add_argument('--candidate',default='secret-hunter-program')
parser.add_argument('--out',default='docs/secret_hunter_program/checks.json')
ARGS=parser.parse_args()
CANDIDATE=ROOT/ARGS.candidate
sys.path.insert(0,str(CANDIDATE/'scripts'))
from hs_arena.engine import Engine
from hs_arena.deck import load_deck,validate_deck_data
from hearthstone.enums import Zone
from action_validator import legal
from lethal_planner import search,probabilistic_lethal
from tactical_model import prepare,transition

EVIDENCE=[]
FIXTURES=0


def fixture(own=(),enemy=(),hand=(),mana=10,hp=30,enemy_hp=30,seed=71):
    global FIXTURES
    FIXTURES+=1
    e=Engine(load_deck(CANDIDATE/'deck.json'),load_deck(ROOT/'hs-arena-0.2.2/decks/greedy_mage.json'),seed)
    for i in (1,2):assert e.step(i,{'type':'mulligan','replace':[]}).accepted
    i,_=e.pending();p,o=e.player(i),e.player(3-i)
    # Unit fixtures normalize our hero/class and use only public legal cards/effects.
    # Seed 71's active seat is checked; arbitrary hidden hands are never passed to policies.
    if e.view(i)['you']['hero']['hero_class']!='HUNTER':
        assert e.step(i,{'type':'end_turn'}).accepted
        i,_=e.pending();p,o=e.player(i),e.player(3-i)
    for c in list(p.hand):c.zone=Zone.GRAVEYARD
    p.max_mana=mana;p.used_mana=0;p.temp_mana=0
    p.hero.damage=p.hero.max_health-hp;o.hero.damage=o.hero.max_health-enemy_hp
    for cid in own:p.summon(cid).turns_in_play=1
    for cid in enemy:o.summon(cid).turns_in_play=1
    for cid in hand:p.give(cid)
    e._mark_seen();return e,i


def play(e,i,cid,**kwargs):
    c=next(c for c in e.view(i)['you']['hand'] if c['card_id']==cid)
    a={'type':'play_card','card':c['entity_id'],**kwargs}
    assert e.step(i,a).accepted,a


class Mechanisms(unittest.TestCase):
    def test_deck_and_live_card_stats(self):
        d=json.loads((CANDIDATE/'deck.json').read_text());self.assertEqual(validate_deck_data(d),[])
        e,i=fixture();p=e.player(i);actual=[]
        from hs_arena.cards import load
        for cid in dict.fromkeys(d['cards']):
            c=p.card(cid);r=load()[cid]
            self.assertEqual(c.cost,r['cost'])
            if r['type']=='MINION':self.assertEqual((c.atk,c.health),(r['attack'],r['health']))
            actual.append({'id':cid,'cost':c.cost,'attack':getattr(c,'atk',None),'health':getattr(c,'health',None)})
        EVIDENCE.append({'mechanism':'19 cards live data','actual':actual})

    def test_tracking_choice_and_discard(self):
        e,i=fixture(hand=['DS1_184']);before=len(e.player(i).deck);play(e,i,'DS1_184')
        s=e.view(i);self.assertEqual(s['phase'],'choice')
        t=next(a for a in s['legal_actions'] if a['type']=='choose');ids=[c['entity_id'] for c in t['options']]
        self.assertEqual(len(ids),3);self.assertTrue(e.step(i,{'type':'choose','options':[ids[0]]}).accepted)
        self.assertEqual(len(e.player(i).deck),before-3)
        self.assertIn(ids[0],[c.entity_id for c in e.player(i).hand])
        EVIDENCE.append({'mechanism':'Tracking','offered':3,'deck_removed':3,'selected_in_hand':True})

    def test_secretkeeper_own_only(self):
        e,i=fixture(own=['EX1_080'],hand=['EX1_610']);p,o=e.player(i),e.player(3-i)
        play(e,i,'EX1_610');self.assertEqual((p.field[0].atk,p.field[0].health),(2,3))
        e.step(i,{'type':'end_turn'});o.max_mana=10;o.used_mana=0;o.give('EX1_611')
        play(e,3-i,'EX1_611');self.assertEqual((p.field[0].atk,p.field[0].health),(2,3))
        EVIDENCE.append({'mechanism':'Secretkeeper','own_secret_buff':True,'enemy_secret_buff':False,'text_mismatch':True})

    def test_explosive_freezing_order_bow(self):
        for order in [('EX1_610','EX1_611'),('EX1_611','EX1_610')]:
            e,i=fixture(enemy=['CS2_172'],hand=list(order));p,o=e.player(i),e.player(3-i)
            p.summon('EX1_536')
            for cid in order:play(e,i,cid)
            e.step(i,{'type':'end_turn'});attacker=o.field[0]
            self.assertTrue(e.step(3-i,{'type':'attack','attacker':attacker.entity_id,'target':p.hero.entity_id}).accepted)
            result={'order':order,'own_hp':p.hero.health,'enemy_hp':o.hero.health,'durability':p.weapon.durability,
                    'secrets_remaining':[c.id for c in p.secrets],'attacker_zone':attacker.zone.name,'attacker_cost':attacker.cost}
            EVIDENCE.append({'mechanism':'Explosive/Freezing order',**result})
            self.assertEqual(p.hero.health,30);self.assertGreater(p.weapon.durability,2)

    def test_freezing_minion_target_and_hero_no_trigger(self):
        e,i=fixture(own=['EX1_080'],enemy=['CS2_200'],hand=['EX1_611']);p,o=e.player(i),e.player(3-i)
        play(e,i,'EX1_611');e.step(i,{'type':'end_turn'});m=o.field[0];cost=m.cost
        self.assertTrue(e.step(3-i,{'type':'attack','attacker':m.entity_id,'target':p.field[0].entity_id}).accepted)
        self.assertEqual(m.zone,Zone.HAND);self.assertEqual(m.cost,cost+2);self.assertEqual(p.field[0].health,3)
        EVIDENCE.append({'mechanism':'Freezing','minion_target_triggers':True,'cost_increase':2})

    def test_snake_capacity_hyena_juggler(self):
        e,i=fixture(own=['EX1_531','NEW1_019'],enemy=['CS2_200'],hand=['EX1_554']);p,o=e.player(i),e.player(3-i)
        play(e,i,'EX1_554');e.step(i,{'type':'end_turn'})
        before=o.hero.health+sum(m.health for m in o.field)
        self.assertTrue(e.step(3-i,{'type':'attack','attacker':o.field[0].entity_id,'target':p.field[0].entity_id}).accepted)
        self.assertEqual(sum(c.id=='EX1_554t' for c in p.field),3)
        self.assertEqual(before-o.hero.health-sum(m.health for m in o.field),5) # 3 knives + Hyena retaliation.
        EVIDENCE.append({'mechanism':'Snake/Juggler','snakes':3,'knife_damage':3})

    def test_misdirection_never_original_hero(self):
        outcomes=[]
        for seed in range(80,92):
            e,i=fixture(enemy=['CS2_200'],hand=['EX1_533'],seed=seed);p,o=e.player(i),e.player(3-i)
            play(e,i,'EX1_533');e.step(i,{'type':'end_turn'})
            self.assertTrue(e.step(3-i,{'type':'attack','attacker':o.field[0].entity_id,'target':p.hero.entity_id}).accepted)
            self.assertEqual(p.hero.health,30);outcomes.append(o.hero.health)
        EVIDENCE.append({'mechanism':'Misdirection','trials':12,'enemy_hero_health':outcomes,'conditional_world':'one enemy minion and two heroes'})

    def test_ooze_highmane_houndmaster(self):
        e,i=fixture(own=['EX1_534'],hand=['EX1_066','DS1_070']);p,o=e.player(i),e.player(3-i)
        o.summon('EX1_536');play(e,i,'EX1_066');self.assertIsNone(o.weapon)
        play(e,i,'DS1_070',target=p.field[0].entity_id);self.assertEqual((p.field[0].atk,p.field[0].health,p.field[0].taunt),(8,7,True))
        p.field[0].destroy();self.assertEqual(sum(c.id=='EX1_534t' for c in p.field),2)
        EVIDENCE.append({'mechanism':'Ooze/Houndmaster/Highmane','weapon_destroyed':True,'buff':[2,2],'death_tokens':2})

    def test_proven_lethals_with_secrekeeper_juggler_wolf_and_krush(self):
        for case in [dict(own=['EX1_080','NEW1_019'],mana=2,enemy_hp=5),
                     dict(hand=['EX1_543'],mana=9,enemy_hp=8),
                     dict(own=['EX1_029','EX1_029'],hand=['EX1_162','EX1_539'],mana=5,enemy_hp=9),
                     dict(own=['EX1_531'],hand=['EX1_539'],mana=3,enemy_hp=7),
                     dict(own=['EX1_538t']*3,hand=['EX1_162'],mana=4,enemy_hp=7)]:
            e,i=fixture(**case);steps=0
            while not e.over and steps<12:
                s=e.view(i);r=search(s,budget_s=.5,max_nodes=7000)
                self.assertTrue(r['guaranteed'],(case,r));self.assertTrue(legal(s,r['first_action']))
                self.assertTrue(e.step(i,r['first_action']).accepted);steps+=1
            self.assertEqual(e.winner,i)
        EVIDENCE.append({'mechanism':'supported lethal','families':5,'real_engine_wins':5})

    def test_random_and_unknown_are_not_guaranteed(self):
        e,i=fixture(hand=['NEW1_031'],mana=3,enemy_hp=4)
        r=probabilistic_lethal(e.view(i),budget_s=.3,max_nodes=5000);self.assertAlmostEqual(r['probability'],1/3)
        e,i=fixture(own=['NEW1_019'],hand=['EX1_538'],enemy=['CS2_200'],mana=3,enemy_hp=1)
        s=e.view(i);s['you']['board'][0]['can_attack']=False
        a=next(a for a in s['legal_actions'] if a['type']=='play_card')
        self.assertIsNone(transition(prepare(s),{'type':'play_card','card':a['card']}))
        e.player(3-i).summon('EX1_611');self.assertFalse(search(e.view(i))['supported'])

    def test_public_history_uncertainty_and_no_cross_game_memory(self):
        from state_features import with_public_history
        e,i=fixture();s=e.view(i);s.update(player=i,turn=7)
        history=[{'event':'play_card','player':3-i,'card_id':'EX1_029','cost':1},
                 {'event':'play_card','player':3-i,'card_id':'EX1_531','cost':2}]
        a=with_public_history(s,history)['public_opponent_evidence']
        self.assertEqual(a['tendency'],'fast_pressure_evidence')
        self.assertEqual(with_public_history(s,[])['public_opponent_evidence']['shown_cards'],[])
        self.assertIn('unknown',a['uncertainty'])

    def test_random_distributions_and_capacity(self):
        from collections import Counter
        companion=Counter();shot=Counter();redirect=Counter()
        for seed in range(100,130):
            e,i=fixture(hand=['NEW1_031'],seed=seed);play(e,i,'NEW1_031');companion[e.player(i).field[0].id]+=1
            e,i=fixture(enemy=['CS2_200','CS2_172'],hand=['EX1_617'],seed=seed)
            before={m.id for m in e.player(3-i).field};play(e,i,'EX1_617')
            shot[next(iter(before-{m.id for m in e.player(3-i).field}))]+=1
            e,i=fixture(own=['EX1_080'],enemy=['CS2_200','CS2_172'],hand=['EX1_533'],seed=seed)
            p,o=e.player(i),e.player(3-i);play(e,i,'EX1_533');e.step(i,{'type':'end_turn'})
            m=o.field[0];e.step(3-i,{'type':'attack','attacker':m.entity_id,'target':p.hero.entity_id})
            self.assertEqual(p.hero.health,30)
            redirect['enemy_hero' if o.hero.health<30 else 'own_minion' if not p.field else 'enemy_minion']+=1
        self.assertEqual(len(companion),3);self.assertEqual(len(shot),2);self.assertEqual(len(redirect),3)
        e,i=fixture(own=['EX1_080']*6,enemy=['CS2_200'],hand=['EX1_554']);p,o=e.player(i),e.player(3-i)
        play(e,i,'EX1_554');e.step(i,{'type':'end_turn'})
        e.step(3-i,{'type':'attack','attacker':o.field[0].entity_id,'target':p.field[0].entity_id})
        self.assertEqual(sum(m.id=='EX1_554t' for m in p.field),1)
        EVIDENCE.append({'mechanism':'random effect distributions','samples_per_effect':30,'companion':dict(companion),
                         'deadly_shot':dict(shot),'misdirection':dict(redirect),'snake_single_slot':True,
                         'scope':'Microfixtures; finite sample counts, not exact probability estimates or match outcomes.'})


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Mechanisms))
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'fixtures':FIXTURES,'evidence':EVIDENCE}
    write(ROOT/ARGS.out,report)
    from development.secret_hunter_program.accounting import record_cases
    record_cases(ARGS.out,FIXTURES)
    raise SystemExit(not result.wasSuccessful())
