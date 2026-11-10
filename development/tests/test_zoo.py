"""Guide-derived behavior tested with actual Fireplace fixtures, public views only."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CANDIDATE = Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else ROOT / 'development/candidates/v6-zoo-guide'
sys.path.insert(0, str(CANDIDATE / 'scripts'))
import policy
import base_policy
from actions import legal
from hs_arena.deck import load_deck
from hs_arena.engine import Engine
from hearthstone.enums import Zone


def fixture(own=(), enemy=(), hand=(), mana=10, enemy_hp=30, own_hp=30):
    deck = load_deck(CANDIDATE / 'deck.json')
    e = Engine(deck, deck, 123)
    for i in (1, 2):
        assert e.step(i, {'type': 'mulligan', 'replace': []}).accepted
    i, _ = e.pending()
    p, o = e.player(i), e.player(3-i)
    for c in list(p.hand):
        c.zone = Zone.GRAVEYARD
    p.max_mana, p.used_mana, p.temp_mana = mana, 0, 0
    p.hero.damage, o.hero.damage = 30-own_hp, 30-enemy_hp
    for cid in own:
        p.summon(cid).turns_in_play = 1
    for cid in enemy:
        o.summon(cid)
    for cid in hand:
        p.give(cid)
    e._mark_seen()
    return e, i


class ZooTests(unittest.TestCase):
    def act(self, e, i):
        s = e.view(i)
        before = copy.deepcopy(s)
        a = policy.decide(s)
        self.assertEqual(s, before)
        self.assertTrue(legal(s, a))
        self.assertTrue(e.step(i, a).accepted)
        return a

    def test_protected_champion_and_existing_planner_unchanged(self):
        manifest = json.loads((ROOT / 'development/reports/zoo-protected-before.json').read_text())
        for path, digest in manifest.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest, path)
        self.assertEqual((CANDIDATE/'scripts/base_policy.py').read_bytes(),
                         (ROOT/'submission/hearthstone-agent/scripts/policy.py').read_bytes())
        for name in ('actions.py', 'decide.py', 'evaluator.py'):
            self.assertEqual((CANDIDATE/'scripts'/name).read_bytes(),
                             (ROOT/'submission/hearthstone-agent/scripts'/name).read_bytes())

    def test_immediate_lethal_precedes_discard_and_development(self):
        e, i = fixture(hand=['EX1_308', 'EX1_067', 'NEW1_019'], enemy_hp=4)
        s = e.view(i)
        self.assertEqual(policy.decide(s), base_policy.decide(s))
        self.act(e, i)
        self.assertEqual(e.winner, i)

    def test_lethal_attack_preserved(self):
        e, i = fixture(own=['CS2_182'], hand=['NEW1_019', 'EX1_319'], enemy_hp=4)
        self.act(e, i)
        self.assertEqual(e.winner, i)

    def test_tap_replenishes_but_never_fatigues_or_burns_or_self_kills(self):
        e, i = fixture(mana=2)
        self.assertEqual(self.act(e, i)['type'], 'hero_power')
        self.assertEqual(len(e.player(i).hand), 1)
        for setup in ({'own_hp': 2}, {'own_hp': 8}, {'hand': ['EX1_067']*9}):
            e, i = fixture(mana=2, **setup)
            self.assertNotEqual(policy.decide(e.view(i))['type'], 'hero_power')
        e, i = fixture(mana=2)
        for c in list(e.player(i).deck):
            c.zone = Zone.GRAVEYARD
        self.assertNotEqual(policy.decide(e.view(i))['type'], 'hero_power')

    def test_flame_imp_wont_kill_own_hero(self):
        e, i = fixture(hand=['EX1_319'], mana=1, own_hp=3)
        self.assertEqual(self.act(e, i)['type'], 'end_turn')
        self.assertFalse(e.over)

    def test_juggler_before_affordable_summon(self):
        e, i = fixture(hand=['EX1_319', 'NEW1_019'], mana=3)
        self.act(e, i)
        self.assertEqual(e.player(i).field[0].id, 'NEW1_019')
        self.act(e, i)
        self.assertEqual(e.player(3-i).hero.health, 29)

    def test_buff_targets_trade_breakpoint(self):
        e, i = fixture(own=['EX1_008', 'CS2_182'], enemy=['CS2_120'], hand=['CS2_188'], mana=1)
        s = e.view(i)
        buffs = [(v,a) for v,a in policy.rank_actions(s) if a['type']=='play_card']
        self.assertEqual(buffs[0][1]['target'], s['you']['board'][0]['entity_id'])
        self.assertTrue(e.step(i, buffs[0][1]).accepted)
        shield = next(m for m in e.player(i).field if m.id == 'EX1_008')
        self.assertTrue(e.step(i, {'type':'attack', 'attacker':shield.entity_id,
                                  'target':e.player(3-i).field[0].entity_id}).accepted)
        self.assertEqual(len(e.player(3-i).field), 0)
        self.assertEqual(shield.health, 1)

    def test_wolf_position_breaks_taunt(self):
        e, i = fixture(own=['CS2_172', 'CS2_172', 'CS2_065'], enemy=['CS2_179'], hand=['EX1_162'], mana=2)
        # Two 3/2s become 4/2; the actual taunt is a 3/5, so adjust its health to 4.
        e.player(3-i).field[0].damage = 1
        plays = [a for _,a in policy.rank_actions(e.view(i)) if a['type']=='play_card']
        self.assertEqual(plays[0]['position'], 1)
        self.assertTrue(e.step(i, plays[0]).accepted)
        self.assertEqual(e.player(i).field[0].atk, 4)
        self.assertEqual(e.player(i).field[2].atk, 4)

    def test_argus_buffs_two_actual_neighbors(self):
        e, i = fixture(own=['EX1_008', 'EX1_556'], hand=['EX1_093'], mana=4)
        a = self.act(e, i)
        self.assertEqual(a['position'], 1)
        self.assertTrue(e.player(i).field[0].taunt)
        self.assertTrue(e.player(i).field[2].taunt)

    def test_sticky_body_does_not_displace_ready_wolf_neighbor(self):
        e, i = fixture(own=['EX1_008', 'EX1_162', 'CS2_065'], hand=['EX1_556'], mana=3)
        plays = [a for _,a in policy.rank_actions(e.view(i)) if a['type']=='play_card']
        self.assertIn(plays[0]['position'], (0,3))
        self.assertTrue(e.step(i, plays[0]).accepted)

    def test_discard_sequence_and_empty_hand_soulfire_before_tap(self):
        e, i = fixture(hand=['EX1_308','EX1_008'], enemy=['NEW1_019'], mana=2)
        self.act(e, i)
        self.assertEqual(e.player(i).field[0].id, 'EX1_008')
        self.act(e, i)
        self.assertEqual(len(e.player(3-i).field), 0)
        e, i = fixture(hand=['EX1_308'], enemy=['NEW1_019'], mana=3)
        self.assertEqual(self.act(e, i)['type'], 'play_card')
        self.assertEqual(self.act(e, i)['type'], 'hero_power')
        self.assertEqual(len(e.player(i).hand), 1)

    def test_opening_hand_requires_real_one_drop(self):
        e, i = fixture(hand=['CS2_188','EX1_162','EX1_067'])
        s = e.view(i);s['phase']='mulligan'
        ids = [c['entity_id'] for c in s['you']['hand']]
        s['legal_actions']=[{'type':'mulligan','options':ids}]
        self.assertEqual(policy.decide(s)['replace'], ids)
        s['you']['hand'][0]['card_id']='EX1_319'
        self.assertEqual(policy.decide(s)['replace'], [ids[2]])

    def test_class_mana_aoe_reserve_is_only_public_heuristic(self):
        e, i = fixture(own=['CS2_172']*4, hand=['EX1_319','EX1_067'], mana=4)
        s = e.view(i);s['opponent']['hero']['hero_class']='PALADIN'
        s['opponent']['max_mana']=3
        self.assertTrue(policy.aoe_exposed(s['you'],s['opponent']))
        s['opponent']['max_mana']=2
        self.assertFalse(policy.aoe_exposed(s['you'],s['opponent']))

    def test_loader_isolates_frozen_policies(self):
        from development.benchmarks.run import load_policy
        zoo, _ = load_policy(CANDIDATE)
        old, _ = load_policy(ROOT/'submission/hearthstone-agent')
        e, i = fixture(hand=['EX1_319'], mana=1, own_hp=3)
        s=e.view(i)
        expected_zoo = zoo.decide(s)
        expected_old = old.decide(s)
        for _ in range(3):
            self.assertEqual(zoo.decide(s), expected_zoo)
            self.assertEqual(old.decide(s), expected_old)
        self.assertNotEqual(expected_zoo, expected_old)


if __name__ == '__main__':
    unittest.main()
