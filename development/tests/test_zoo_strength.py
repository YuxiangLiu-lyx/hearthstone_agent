"""Behavioral regressions for the loss-derived Zoo improvements."""
import sys,copy,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
CANDIDATE=Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 and not sys.argv[1].startswith('-') else ROOT/'development/candidates/v7-zoo-strength'
sys.path.insert(0,str(CANDIDATE/'scripts'))
import policy,base_policy
from zoo_combat import joint_scores,key
from actions import legal
from hs_arena.engine import Engine
from hs_arena.deck import load_deck,validate_deck_data
from hearthstone.enums import Zone
from development.benchmarks.run import load_policy


def fixture(own=(),enemy=(),hand=(),mana=0,own_hp=30,enemy_hp=30):
    deck=load_deck(CANDIDATE/'deck.json');e=Engine(deck,deck,123)
    for i in (1,2):assert e.step(i,{'type':'mulligan','replace':[]}).accepted
    i,_=e.pending();p,o=e.player(i),e.player(3-i)
    for c in list(p.hand):c.zone=Zone.GRAVEYARD
    p.max_mana=mana;p.used_mana=0;p.temp_mana=0
    p.hero.damage=30-own_hp;o.hero.damage=30-enemy_hp
    for cid in own:p.summon(cid).turns_in_play=1
    for cid in enemy:o.summon(cid)
    for cid in hand:p.give(cid)
    e._mark_seen();return e,i


class StrengthTests(unittest.TestCase):
    def act(self,e,i):
        s=e.view(i);before=copy.deepcopy(s);a=policy.decide(s)
        self.assertEqual(s,before);self.assertTrue(legal(s,a));self.assertTrue(e.step(i,a).accepted)
        return a

    def test_two_attackers_clear_taunt_instead_of_stalling(self):
        e,i=fixture(own=['EX1_019']*2,enemy=['CS2_179'],own_hp=6)
        old,_=load_policy(ROOT/'development/candidates/v6-zoo-guide')
        self.assertEqual(old.decide(e.view(i))['type'],'end_turn')
        self.act(e,i);self.act(e,i)
        self.assertEqual(len(e.player(3-i).field),0)

    def test_shield_requires_three_actual_attacks(self):
        e,i=fixture(own=['EX1_008','CS2_172','CS2_172'],enemy=['EX1_032'],own_hp=6)
        first=self.act(e,i)
        self.assertEqual(first['attacker'],e.player(i).field[0].entity_id)
        self.assertFalse(e.player(3-i).field[0].divine_shield)
        self.act(e,i);self.act(e,i)
        self.assertEqual(len(e.player(3-i).field),0)

    def test_burn_plus_attack_kills_larger_target(self):
        e,i=fixture(own=['CS2_065'],enemy=['CS2_179'],hand=['EX1_308'],mana=1,own_hp=6)
        self.act(e,i);self.act(e,i)
        self.assertEqual(len(e.player(3-i).field),0)

    def test_two_random_discard_spells_not_assumed_available(self):
        e,i=fixture(enemy=['EX1_586'],hand=['EX1_308']*2,mana=2)
        s=e.view(i)
        self.assertEqual(joint_scores(s,base_policy.rank_actions(s)),{})

    def test_giant_after_discounting_summon(self):
        e,i=fixture(own=['EX1_008']*3,enemy=['CS2_065']*3,hand=['EX1_586','EX1_008'],mana=4)
        s=e.view(i);giant=next(c for c in s['you']['hand'] if c['card_id']=='EX1_586')
        self.assertEqual(giant['cost'],4)
        old,_=load_policy(ROOT/'development/candidates/v6-zoo-guide')
        self.assertEqual(old.decide(s)['card'],giant['entity_id'])
        a=self.act(e,i);self.assertNotEqual(a['card'],giant['entity_id'])
        self.assertEqual(e.player(i).mana,3)
        a=self.act(e,i);self.assertEqual(a['card'],giant['entity_id'])
        self.assertEqual(len(e.player(i).field),5)

    def test_giant_preserves_last_board_slot(self):
        e,i=fixture(own=['EX1_008']*6,enemy=['CS2_065'],hand=['EX1_586','EX1_008'],mana=3)
        giant=next(c for c in e.view(i)['you']['hand'] if c['card_id']=='EX1_586')
        self.assertEqual(self.act(e,i)['card'],giant['entity_id'])
        self.assertEqual(len(e.player(i).field),7)

    def test_giant_setup_never_overrides_lethal_or_self_damage_guard(self):
        e,i=fixture(own=['EX1_008']*3,enemy=['CS2_065']*3,hand=['EX1_586','EX1_319'],mana=4,own_hp=3)
        a=self.act(e,i)
        self.assertEqual(next(m for m in e.player(i).field if m.entity_id==a['card']).id,'EX1_586')
        e,i=fixture(hand=['EX1_308','EX1_586','EX1_008'],mana=10,enemy_hp=4)
        self.assertEqual(policy.decide(e.view(i)),base_policy.decide(e.view(i)))
        self.act(e,i);self.assertEqual(e.winner,i)

    def test_unknown_combat_triggers_abstain(self):
        e,i=fixture(own=['EX1_019']*2,enemy=['EX1_604','CS2_179'])
        s=e.view(i)
        self.assertEqual(joint_scores(s,base_policy.rank_actions(s)),{})

    def test_fixed_node_bound_and_valid_first_actions(self):
        e,i=fixture(own=['EX1_019']*6,enemy=['CS2_179']*6,hand=['EX1_308']*2,mana=10)
        s=e.view(i);ranked=base_policy.rank_actions(s);t=time.perf_counter()
        values=joint_scores(s,ranked,max_nodes=100)
        self.assertLess(time.perf_counter()-t,.2)
        allowed={key(a) for _,a in ranked}
        self.assertTrue(set(values).issubset(allowed))


if __name__=='__main__':unittest.main()
