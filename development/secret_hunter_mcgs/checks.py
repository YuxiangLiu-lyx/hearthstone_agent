"""Mechanism tests against the unmodified course engine and small exact graphs."""
import collections
import copy
import json
import math
from pathlib import Path
import random
import sys
import time
import unittest
from development.secret_hunter_mcgs.build import HERE,Y1
sys.path[:0]=[str(HERE),str(Y1/'scripts')]
from mcgs_init import initialize
initialize()
from mcgs_graph import Graph,Chance
from mcgs_world import build,clone,Unsupported
from mcgs_search import key,rank,search
from development.secret_hunter_mcgs.cases import fixture
from actions import expand
from hearthstone.enums import Zone

EVIDENCE=[]

def play(e,seat,cid,**kw):
    c=next(c for c in e.view(seat)['you']['hand'] if c['card_id']==cid)
    a={'type':'play_card','card':c['entity_id'],**kw}
    assert e.step(seat,a).accepted
    return a

class Mechanisms(unittest.TestCase):
    def test_diamond_offpath_and_ucd_value(self):
        g=Graph(d1=2,d2=1);r,a,b,c=[g.node(s) for s in 'rabc']
        ra=g.connect(r,a,'A');rb=g.connect(r,b,'B');ac=g.connect(a,c,'C');bc=g.connect(b,c,'C')
        g.backup([ra,ac],1.)
        self.assertEqual(g.transpositions,1);self.assertEqual(b.visits,1);self.assertEqual(bc.visits,1)
        self.assertEqual(rb.visits,0);self.assertEqual(c.visits,1)
        self.assertAlmostEqual(bc.value(.3),1+.3*math.sqrt(2*math.log(max(1,b.total))))
        EVIDENCE.append({'test':'diamond','offpath_updates':g.offpath_updates,'node_visits':[n.visits for n in (r,a,b,c)],'edge_visits':[e.visits for e in (ra,rb,ac,bc)]})

    def test_empirical_chance_and_rounding(self):
        c=Chance();c.add('a',1);c.add('a',1);c.add('b',2);rng=random.Random(5)
        sample=collections.Counter(c.sample(rng)[0] for _ in range(12000))
        self.assertAlmostEqual(sample['a']/12000,2/3,delta=.02)
        c.visits=3
        self.assertEqual(c.width({'dpw_c':1,'alpha':1,'eta':2},1),2)
        self.assertEqual(c.width({'dpw_c':1,'alpha':1,'eta':2,'rounding':'floor_ablation'},1),1)
        c.visits=1
        self.assertEqual(c.width({'dpw_c':4.1,'eta':2,'rounding':'paper'},1),3)
        self.assertEqual(c.width({'dpw_c':4.1,'eta':2,'rounding':'source'},1),2)
        EVIDENCE.append({'test':'duplicate_weighting','samples':dict(sample),'stored_samples':c.count,'unique_outcomes':len(c.outcomes)})

    def test_equal_visible_outcomes_keep_latent_diversity(self):
        c=Chance();c.add('same-public-state','coil');c.add('same-public-state','no-coil')
        rng=random.Random(10);seen=collections.Counter(c.sample(rng)[1] for _ in range(1000))
        self.assertEqual(set(seen),{'coil','no-coil'})
        self.assertAlmostEqual(seen['coil']/1000,.5,delta=.06)
        EVIDENCE.append({'test':'latent_particle_retention','counts':dict(seen)})

    def test_public_world_and_actual_commutation(self):
        e=fixture(own=['EX1_029','EX1_029'],hand=['EX1_533'],mana=3)
        s=e.view(1);a=build(s,1);b=build(s,2)
        self.assertEqual(key(a.view(1)),key(b.view(1)))
        ids=[m['entity_id'] for m in s['you']['board']];target=s['opponent']['hero']['entity_id']
        for order,w in ((ids,a),(ids[::-1],b)):
            for i in order:self.assertTrue(w.step(1,{'type':'attack','attacker':i,'target':target}).accepted)
        self.assertEqual(key(a.view(1)),key(b.view(1)))
        changed=copy.deepcopy(a.view(1));changed['you']['board'].reverse()
        self.assertNotEqual(key(changed),key(a.view(1)))
        changed=copy.deepcopy(a.view(1));changed['you']['mana']-=1
        self.assertNotEqual(key(changed),key(a.view(1)))
        EVIDENCE.append({'test':'real_engine_diamond','same_public_successor':True,'position_and_mana_separated':True})

    def test_direwolf_rehydration_and_removal(self):
        e=fixture(own=['EX1_538t','EX1_162','EX1_538t'],enemy=['CS2_200'])
        w=build(e.view(1),3)
        self.assertEqual([m.atk for m in w.player(1).field],[2,2,2])
        w.player(1).field[1].destroy();w.game.refresh_auras()
        self.assertEqual([m.atk for m in w.player(1).field],[1,1])

    def test_tracking_rehydration(self):
        e=fixture(hand=['DS1_184'],mana=6);play(e,1,'DS1_184')
        s=e.view(1);w=build(s,4);before=len(w.player(1).deck)
        a=expand(w.view(1))[0];self.assertEqual(a['type'],'choose')
        self.assertTrue(w.step(1,a).accepted);self.assertEqual(len(w.player(1).deck),before-3)
        self.assertIn(a['options'][0],[c.entity_id for c in w.player(1).hand])

    def test_mortal_coil_friendly_amani_lethal(self):
        e=fixture(enemy=['EX1_556','CS2_188','EX1_008','EX1_393'],hp=9,mana=6,opponent_hand=['EX1_302'])
        e.step(1,{'type':'end_turn'});q=e.player(2);amani=next(m for m in q.field if m.id=='EX1_393')
        chosen=rank(e.view(2),{})
        self.assertTrue(any(a.get('target')==amani.entity_id and a['type']=='play_card' for _,a in chosen))
        play(e,2,'EX1_302',target=amani.entity_id);self.assertEqual(amani.atk,5)
        self.assertEqual(sum(m.atk for m in q.field),9)
        for m in list(q.field):
            self.assertTrue(e.step(2,{'type':'attack','attacker':m.entity_id,'target':e.player(1).hero.entity_id}).accepted)
        self.assertTrue(e.over);self.assertEqual(e.winner,2)
        EVIDENCE.append({'test':'friendly_coil_amani','visible_attack_before':6,'attack_after':9,'own_hp':9,'winner':2})

    def test_krush_taunt_route(self):
        e=fixture(own=['EX1_534'],enemy=['CS2_179'],hand=['EX1_543'],mana=9,enemy_hp=8)
        self.assertTrue(e.step(1,{'type':'attack','attacker':e.player(1).field[0].entity_id,'target':e.player(2).field[0].entity_id}).accepted)
        play(e,1,'EX1_543');k=next(c for c in e.player(1).field if c.id=='EX1_543')
        self.assertTrue(e.step(1,{'type':'attack','attacker':k.entity_id,'target':e.player(2).hero.entity_id}).accepted)
        self.assertEqual(e.winner,1)

    def test_secret_order_bow_and_misdirection(self):
        outcomes=[]
        for order in [('EX1_610','EX1_611'),('EX1_611','EX1_610')]:
            e=fixture(enemy=['CS2_172'],hand=list(order),mana=10);e.player(1).summon('EX1_536')
            for cid in order:play(e,1,cid)
            w=build(e.view(1),7);w.step(1,{'type':'end_turn'})
            m=w.player(2).field[0]
            w.step(2,{'type':'attack','attacker':m.entity_id,'target':w.player(1).hero.entity_id})
            outcomes.append({'order':order,'durability':w.player(1).weapon.durability,'hp':w.player(1).hero.health})
        self.assertEqual([r['durability'] for r in outcomes],[4,3])
        for seed in range(12):
            e=fixture(enemy=['CS2_200'],hand=['EX1_533'],mana=10);play(e,1,'EX1_533')
            w=build(e.view(1),seed);w.step(1,{'type':'end_turn'})
            self.assertTrue(w.step(2,{'type':'attack','attacker':w.player(2).field[0].entity_id,'target':w.player(1).hero.entity_id}).accepted)
            self.assertEqual(w.player(1).hero.health,30)
        EVIDENCE.append({'test':'ordered_secrets_bow','outcomes':outcomes,'misdirection_trials':12})

    def test_companion_exact_probability_reference(self):
        counts=collections.Counter();e=fixture(hand=['NEW1_031'],mana=3);s=e.view(1)
        w=build(s,9)
        for seed in range(300):
            trial=clone(w,seed);play(trial,1,'NEW1_031');counts[trial.player(1).field[0].id]+=1
        self.assertEqual(len(counts),3)
        for count in counts.values():self.assertAlmostEqual(count/300,1/3,delta=.065)
        EVIDENCE.append({'test':'companion','counts':dict(counts),'exact_probability_each':1/3})

    def test_juggler_hounds_and_independent_rng(self):
        e=fixture(own=['NEW1_019'],enemy=['CS2_200','CS2_200'],hand=['EX1_538'],mana=3)
        before=e.game.random.getstate();s=e.view(1);w=build(s,17);a=clone(w,42);b=clone(w,42)
        for trial in (a,b):play(trial,1,'EX1_538')
        self.assertEqual(key(a.view(1)),key(b.view(1)));self.assertEqual(before,e.game.random.getstate())
        self.assertEqual(len(a.player(1).field),3)
        damage=30-a.player(2).hero.health+sum(m.damage for m in a.player(2).field)
        self.assertEqual(damage,2)

    def test_complete_opponent_turn_and_public_privacy(self):
        e=fixture(own=['EX1_029'],enemy=['EX1_393'],hand=['EX1_531'],mana=3,hp=12,opponent_hand=['EX1_302'])
        s=e.view(1);baseline=rank(s,{})[0][1]
        r=search(s,{'iterations':10,'max_transitions':300},baseline,time.monotonic()+8,trace=True)
        self.assertIsNone(r['failure']);self.assertGreater(r['metrics']['cross_turn'],0)
        self.assertGreater(r['metrics']['opponent_actions'],0);self.assertFalse(r['guaranteed'])
        EVIDENCE.append({'test':'full_horizon','metrics':r['metrics'],'transpositions':r['transpositions']})
        short=search(s,{'iterations':10,'max_transitions':300,'horizon':1},baseline,time.monotonic()+8)
        self.assertEqual(short['metrics'].get('opponent_actions',0),0)

if __name__=='__main__':
    start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Mechanisms)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    path=HERE.parents[1]/'docs/secret_hunter_mcgs/mechanisms.json'
    path.write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'seconds':time.monotonic()-start,'evidence':EVIDENCE},indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
