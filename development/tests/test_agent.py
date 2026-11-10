"""Behavior and real-engine differential tests, stdlib unittest only.

The test fixture may construct host states. Policies receive only engine.view().
No such fixture code is shipped in the Skill.
"""
import copy
import importlib
import json
import random
import sys
import subprocess
import tempfile
import shutil
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else ROOT/'development/candidates/v2-search'
sys.path.insert(0,str(CANDIDATE/'scripts'))
from actions import expand, legal, fallback
from decide import response
from hs_arena.deck import load_deck, validate_deck_data
from hs_arena.engine import Engine
from hearthstone.enums import Zone
from hs_arena.agents.greedy_bot import GreedyBot


def fixture(own=(),enemy=(),hand=(),mana=10,enemy_hp=30,own_hp=30):
    deck=load_deck(ROOT/'development/decks/mage-tempo.json')
    e=Engine(deck,deck,123)
    for i in (1,2):assert e.step(i,{'type':'mulligan','replace':[]}).accepted
    i,_=e.pending();p=e.player(i);o=e.player(3-i)
    for c in list(p.hand):c.zone=Zone.GRAVEYARD
    p.max_mana=mana;p.used_mana=0;p.temp_mana=0
    p.hero.damage=p.hero.max_health-own_hp;o.hero.damage=o.hero.max_health-enemy_hp
    for cid in own:
        m=p.summon(cid);m.turns_in_play=1
    for cid in enemy:o.summon(cid)
    for cid in hand:p.give(cid)
    e._mark_seen()
    return e,i


class ProtocolTests(unittest.TestCase):
    def test_all_recipes_legal(self):
        for p in (ROOT/'development/decks').glob('*.json'):
            self.assertEqual(validate_deck_data(json.loads(p.read_text())),[],p)
        self.assertEqual(validate_deck_data(json.loads((CANDIDATE/'deck.json').read_text())),[])

    def test_setup_and_terminal(self):
        r=response({'phase':'deck_submission','seq':1})
        self.assertEqual(validate_deck_data(r['action']),[])
        self.assertEqual(response({'phase':'game_over','seq':2,'result':None}),{'seq':2,'game_over':True,'result':None})

    def test_mulligan_choice_and_choose_one(self):
        s={'phase':'mulligan','legal_actions':[{'type':'mulligan','options':[2,3,4],'min':0,'max':3}]}
        self.assertTrue(legal(s,{'type':'mulligan','replace':[2,4]}))
        self.assertFalse(legal(s,{'type':'mulligan','replace':[2,2]}))
        self.assertFalse(legal(s,{'type':'mulligan','replace':[999]}))
        s={'phase':'choice','legal_actions':[{'type':'choose','min':2,'max':2,'options':[{'entity_id':2},{'entity_id':3},{'entity_id':4}]}]}
        self.assertEqual(len(expand(s)),3)
        self.assertTrue(legal(s,fallback(s)))
        s={'legal_actions':[{'type':'play_card','card':5,'positions':[0,1],'choose':[
            {'entity_id':7,'targets':None},{'entity_id':8,'targets':[11,12]}]}]}
        self.assertEqual(len(expand(s)),6)
        self.assertTrue(legal(s,{'type':'play_card','card':5,'choose':7}))
        self.assertFalse(legal(s,{'type':'play_card','card':5,'choose':7,'target':11}))

    def test_exception_fallback(self):
        from unittest.mock import patch
        e,i=fixture();s=e.view(i);s['seq']=2
        with patch('policy.decide',side_effect=RuntimeError('injected test failure')):
            r=response(s)
        self.assertTrue(legal(s,r['action']))

    def test_cli_fresh_directory_and_hard_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skill'
            shutil.copytree(CANDIDATE,d,ignore=shutil.ignore_patterns('__pycache__'))
            (d/'game').mkdir()
            e,i=fixture(own=['CS2_182'],hand=['CS2_029']);s=e.view(i);s['seq']=19
            (d/'game/state.json').write_text(json.dumps(s))
            proc=subprocess.run([sys.executable,'scripts/decide.py'],cwd=d,capture_output=True,text=True,timeout=8)
            self.assertEqual(proc.returncode,0,proc.stderr)
            answer=json.loads(proc.stdout)
            self.assertEqual(answer['seq'],19);self.assertTrue(legal(s,answer['action']))
            if '--worker' in (d/'scripts/decide.py').read_text():
                (d/'config.json').write_text('{"decision_budget_s":0.1}')
                (d/'scripts/policy.py').write_text('import time\ndef decide(state,config=None):\n time.sleep(10)\n')
                start=time.perf_counter()
                proc=subprocess.run([sys.executable,'scripts/decide.py'],cwd=d,capture_output=True,text=True,timeout=3)
                self.assertLess(time.perf_counter()-start,1.5)
                self.assertIn('fallback',proc.stderr)
                self.assertTrue(legal(s,json.loads(proc.stdout)['action']))

    def test_random_game_actions_and_nonmutation(self):
        from policy import decide
        n=0
        for seed in (5,16,81):
            d=load_deck(CANDIDATE/'deck.json');e=Engine(d,d,seed,max_turns=90)
            while not e.over:
                i,_=e.pending();s=e.view(i);before=copy.deepcopy(s)
                a=decide(s)
                self.assertEqual(s,before)
                self.assertTrue(legal(s,a),(s['phase'],a))
                self.assertTrue(e.step(i,a).accepted)
                n+=1
        self.assertGreater(n,100)


@unittest.skipUnless((CANDIDATE/'scripts/planner.py').exists(),'candidate has no planner')
class PlannerTests(unittest.TestCase):
    def assert_real_lethal(self,e,i):
        from planner import lethal_plan
        moves=0
        while not e.over and moves<10:
            s=e.view(i);plan=lethal_plan(s,budget_s=.5,max_nodes=7000)
            self.assertTrue(plan,(s,plan))
            self.assertTrue(legal(s,plan[0]))
            self.assertTrue(e.step(i,plan[0]).accepted)
            moves+=1
        self.assertEqual(e.winner,i)

    def test_burn_mana_and_armor(self):
        e,i=fixture(hand=['CS2_024','CS2_029'],mana=6,enemy_hp=9)
        self.assert_real_lethal(e,i)
        from planner import lethal_plan
        e,i=fixture(hand=['CS2_024','CS2_029'],mana=5,enemy_hp=10)
        self.assertIsNone(lethal_plan(e.view(i)))
        e,i=fixture(hand=['CS2_029'],mana=4,enemy_hp=5);e.player(3-i).hero.armor=2
        self.assertIsNone(lethal_plan(e.view(i)))

    def test_taunt_shield_and_charge(self):
        e,i=fixture(own=['CS2_200'],enemy=['CS2_179'],hand=['CS2_029'],mana=4,enemy_hp=6)
        self.assert_real_lethal(e,i)
        e,i=fixture(own=['CS2_200'],enemy=['EX1_032'],hand=['CS2_029'],mana=6,enemy_hp=6)
        self.assert_real_lethal(e,i)
        e,i=fixture(hand=['EX1_067'],mana=6,enemy_hp=4)
        self.assert_real_lethal(e,i)

    def test_buff_and_discount_order(self):
        e,i=fixture(own=['CS2_182'],hand=['CS2_087'],mana=1,enemy_hp=7)
        self.assert_real_lethal(e,i)
        e,i=fixture(hand=['EX1_608','CS2_029','CS2_029'],mana=8,enemy_hp=12)
        self.assert_real_lethal(e,i)

    def test_frozen_and_unknown_secret_abstain(self):
        from planner import lethal_plan
        e,i=fixture(own=['CS2_200'],mana=0,enemy_hp=6);e.player(i).field[0].frozen=True
        self.assertIsNone(lethal_plan(e.view(i)))
        s=e.view(i);s['opponent']['secrets_count']=1
        self.assertIsNone(lethal_plan(s))

    def test_budget(self):
        from planner import lethal_plan
        e,i=fixture(own=['CS2_182']*6,enemy=['CS2_179']*6,hand=['CS2_024']*5,mana=10,enemy_hp=30)
        t=time.perf_counter();lethal_plan(e.view(i),budget_s=.01,max_nodes=100)
        self.assertLess(time.perf_counter()-t,.2)

    def test_one_step_differential(self):
        from planner import prepare,transition,options,supported
        from hs_arena._fp import init_engine
        db=init_engine();memo={id(c):c for c in db.db.values()}
        setups=[dict(own=['CS2_182'],enemy=['CS2_179','EX1_008'],hand=['CS2_029','CS2_024']),
                dict(own=['NEW1_012','EX1_608'],enemy=['EX1_556'],hand=['CS2_025','CS2_092','EX1_067']),
                dict(own=['CS2_033'],enemy=['CS2_182'],hand=['CS2_189','EX1_019','GAME_005'])]
        count=0
        for setup in setups:
            e,i=fixture(**setup);s=e.view(i);self.assertTrue(supported(s))
            model=prepare(s)
            for a in options(model):
                if not legal(s,a):continue
                predicted=transition(model,a)
                if predicted is None:continue
                clone=copy.deepcopy(e,dict(memo));self.assertTrue(clone.step(i,a).accepted)
                observed=clone.view(i)
                for side in ('you','opponent'):
                    for field in ('health','armor'):self.assertEqual(predicted[side]['hero'][field],observed[side]['hero'][field],a)
                    if side=='you':self.assertEqual(predicted[side]['mana'],observed[side]['mana'],a)
                    keys=('card_id','attack','health','divine_shield','taunt','frozen')
                    project=lambda board:[tuple(m.get(k,False) for k in keys) for m in board]
                    self.assertEqual(project(predicted[side]['board']),project(observed[side]['board']),a)
                count+=1
        self.assertGreater(count,20)


if __name__=='__main__':unittest.main()
