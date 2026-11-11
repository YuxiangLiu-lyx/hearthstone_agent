"""Actual-engine regression scenarios for theft, buffs, control and runtime differences."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"control_priest/scripts"))
from actions import legal
from policy import decide, rank_actions
from priest_tactics import with_history
from hs_arena.deck import load_deck, validate_deck_data
from hs_arena.engine import Engine
from hearthstone.enums import Zone


def fixture(own=(), enemy=(), hand=(), mana=10, hp=30, enemy_hp=30):
    deck = load_deck(ROOT/"control_priest/deck.json")
    engine = Engine(deck, deck, 31)
    for seat in (1, 2):
        assert engine.step(seat, {"type": "mulligan", "replace": []}).accepted
    seat, _ = engine.pending(); player = engine.player(seat)
    for card in list(player.hand):
        card.zone = Zone.GRAVEYARD
    player.max_mana, player.used_mana, player.temp_mana = mana, 0, 0
    player.hero.damage = 30-hp; player.opponent.hero.damage = 30-enemy_hp
    for cid in own:
        player.summon(cid).turns_in_play = 1
    for cid in enemy:
        player.opponent.summon(cid)
    for cid in hand:
        player.give(cid)
    engine._mark_seen()
    return engine, seat


class PriestTests(unittest.TestCase):
    def play(self, engine, seat, **extra):
        state = {**engine.view(seat), **extra}
        action = decide(state, {"face_weight": .35})
        self.assertTrue(legal(state, action), action)
        self.assertTrue(engine.step(seat, action).accepted)
        return action

    def test_decks_and_submission(self):
        for path in ("control_priest/deck.json", "development/priest/decks/control-synergy.json"):
            data = json.loads((ROOT/path).read_text())
            self.assertEqual(validate_deck_data(data), [])
            self.assertEqual(len(data["cards"]), 30)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"state.json"; p.write_text('{"phase":"deck_submission","seq":8}')
            r = subprocess.run([sys.executable, str(ROOT/"control_priest/scripts/decide.py"), str(p)], capture_output=True, text=True, check=True)
            result = json.loads(r.stdout)
            self.assertEqual(result["seq"], 8)
            self.assertEqual(result["action"]["type"], "submit_deck")

    def test_power_infusion_runtime_is_two_two(self):
        e, i = fixture(own=["CS2_182"], hand=["EX1_194"])
        m, c = e.player(i).field[0], e.player(i).hand[0]
        self.assertTrue(e.step(i, {"type": "play_card", "card": c.entity_id, "target": m.entity_id}).accepted)
        self.assertEqual((m.atk, m.health), (6, 7))

    def test_shield_costs_zero_and_does_not_draw(self):
        e, i = fixture(own=["CS2_182"], hand=["CS2_004"], mana=0)
        p = e.player(i); deck_count = len(p.deck)
        self.assertTrue(e.step(i, {"type": "play_card", "card": p.hand[0].entity_id, "target": p.field[0].entity_id}).accepted)
        self.assertEqual(len(p.deck), deck_count)
        self.assertEqual((len(p.hand), p.field[0].health), (0, 7))

    def test_scarlet_enables_cabal_theft_of_four_attack(self):
        e, i = fixture(enemy=["CS2_182"], hand=["EX1_196", "EX1_091"], mana=7)
        target = e.player(3-i).field[0].entity_id
        a = self.play(e, i)
        self.assertEqual(a["target"], target)
        self.assertEqual(e.player(3-i).field[0].atk, 2)
        self.play(e, i)
        self.assertIn(target, [m.entity_id for m in e.player(i).field])
        self.assertEqual(len(e.player(3-i).field), 0)

    def test_scarlet_enables_pain_on_four_attack(self):
        e, i = fixture(enemy=["CS2_182"], hand=["EX1_196", "CS2_234"], mana=3)
        self.play(e, i); self.play(e, i)
        self.assertEqual(len(e.player(3-i).field), 0)

    def test_cabal_does_not_assume_two_free_slots_with_six_minions(self):
        e, i = fixture(own=["CS2_120"]*6, enemy=["EX1_556"], hand=["EX1_091"], mana=6)
        rows = rank_actions(e.view(i)); card = e.player(i).hand[0].entity_id
        self.assertLess(max(score for score,a in rows if a.get("card") == card), 0)

    def test_mind_control_removes_threat_and_keeps_body(self):
        e, i = fixture(enemy=["CS2_200"], hand=["CS1_113"], hp=5)
        target = e.player(3-i).field[0].entity_id
        a = self.play(e, i)
        self.assertEqual(a["target"], target)
        self.assertIn(target, [m.entity_id for m in e.player(i).field])

    def test_natalie_destroys_enemy_and_gains_current_health(self):
        e, i = fixture(enemy=["CS2_200"], hand=["EX1_198"], mana=8)
        self.play(e, i)
        self.assertEqual(len(e.player(3-i).field), 0)
        self.assertEqual(e.player(i).field[0].health, 8)

    def test_shadow_madness_spends_the_borrowed_body(self):
        e, i = fixture(enemy=["EX1_556", "CS2_182"], hand=["EX1_334"], mana=3)
        borrowed = e.player(3-i).field[0].entity_id
        self.play(e, i)
        state = e.view(i)
        self.assertTrue(any(m["entity_id"] == borrowed and m["can_attack"] for m in state["you"]["board"]))
        a = self.play(e, i, temporary_control=[borrowed])
        self.assertEqual(a["attacker"], borrowed)
        self.assertNotIn(borrowed, [m.entity_id for m in e.player(i).field])
        self.assertEqual(len(e.player(i).field), 1)  # Deathrattle token stays with us.

    def test_public_history_tracks_only_own_current_turn_theft(self):
        s = {"player": 1}
        events = [{"event": "play_card", "player": 1, "card_id": "EX1_334", "target": {"entity_id": 7}},
                  {"event": "turn_start", "player": 1},
                  {"event": "play_card", "player": 1, "card_id": "EX1_334", "target": {"entity_id": 9}}]
        self.assertEqual(with_history(s, events)["temporary_control"], [9])

    def test_holy_nova_clears_and_heals(self):
        e, i = fixture(enemy=["CS2_171"]*4, hand=["CS1_112"], mana=4, hp=4)
        self.play(e, i)
        self.assertEqual(len(e.player(3-i).field), 0)
        self.assertEqual(e.player(i).hero.health, 6)

    def test_ruin_counts_own_casualties(self):
        e, i = fixture(own=["CS2_200"]*3, enemy=["CS2_200"], hand=["EX1_197"], mana=4)
        card = e.player(i).hand[0].entity_id
        score = next(s for s,a in rank_actions(e.view(i)) if a.get("card") == card)
        self.assertLess(score, 0)

    def test_shield_inner_fire_order_finds_actual_lethal(self):
        e, i = fixture(own=["CS2_182"], hand=["CS2_004", "CS1_129"], mana=1, enemy_hp=7)
        for _ in range(3):
            self.play(e, i)
            if e.over:
                break
        self.assertTrue(e.over)
        self.assertEqual(e.winner, i)

    def test_heal_before_surviving_trade(self):
        e, i = fixture(own=["CS2_182"], enemy=["CS2_172"], mana=2)
        e.player(i).field[0].damage = 3
        action = self.play(e, i)
        self.assertEqual(action["type"], "hero_power")
        self.play(e, i)
        self.assertEqual(len(e.player(3-i).field), 0)
        self.assertEqual(e.player(i).field[0].health, 1)

    def test_thoughtsteal_not_used_on_empty_deck(self):
        e, i = fixture(hand=["EX1_339"], mana=2)
        for c in list(e.player(3-i).deck):
            c.zone = Zone.GRAVEYARD
        self.assertNotEqual(self.play(e, i)["type"], "play_card")

    def test_faceless_copies_a_quality_body(self):
        e, i = fixture(own=["EX1_110"], enemy=["CS2_171"], hand=["EX1_564"], mana=5)
        cairne = e.player(i).field[0]
        action = self.play(e, i)
        self.assertEqual(action["target"], cairne.entity_id)
        self.assertEqual([m.id for m in e.player(i).field], ["EX1_110", "EX1_110"])
        self.assertTrue(e.player(i).field[1].has_deathrattle)

    def test_temporary_theft_returns_when_not_spent(self):
        e, i = fixture(enemy=["CS2_120"], hand=["EX1_334"], mana=3)
        p = e.player(i); target = p.opponent.field[0].entity_id
        self.assertTrue(e.step(i, {"type": "play_card", "card": p.hand[0].entity_id, "target": target}).accepted)
        self.assertIn(target, [m.entity_id for m in p.field])
        self.assertTrue(e.step(i, {"type": "end_turn"}).accepted)
        self.assertIn(target, [m.entity_id for m in p.opponent.field])

    def test_frozen_shadow_madness_is_not_a_ready_attacker(self):
        e, i = fixture(enemy=["EX1_556", "CS2_182"], hand=["EX1_334"], mana=3)
        e.player(3-i).field[0].frozen = True
        card = e.player(i).hand[0].entity_id
        self.assertLess(max(s for s,a in rank_actions(e.view(i)) if a.get("card") == card), 0)

    def test_copy_generation_never_removes_opponent_cards(self):
        e, i = fixture(hand=["EX1_339"], mana=2)
        p = e.player(i); count = len(p.opponent.deck)
        self.play(e, i)
        self.assertEqual(len(p.opponent.deck), count)
        self.assertEqual(len(p.hand), 2)

    def test_direct_lethal_retains_priority_over_theft(self):
        e, i = fixture(own=["CS2_200"], enemy=["EX1_556"], hand=["EX1_091"], enemy_hp=6)
        action = self.play(e, i)
        self.assertEqual(action["type"], "attack")
        self.assertEqual(e.winner, i)

    def test_fatigue_heal_and_no_fatal_mass_dispel(self):
        e, i = fixture(hand=["EX1_626"], hp=1)
        for c in list(e.player(i).deck):
            c.zone = Zone.GRAVEYARD
        action = self.play(e, i)
        self.assertEqual(action["type"], "hero_power")
        self.assertEqual(action["target"], e.player(i).hero.entity_id)


if __name__ == "__main__":
    unittest.main()
