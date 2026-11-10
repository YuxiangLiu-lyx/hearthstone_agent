"""Official-engine behavioral tests; fixture access is never shipped in the skill."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "face_hunter/scripts"))
from action_validator import legal, fallback
from decide import response
from strategy import decide
from hs_arena.deck import load_deck, validate_deck_data
from hs_arena.engine import Engine
from hearthstone.enums import Zone


def fixture(own=(), enemy=(), hand=(), mana=10, enemy_hp=30, own_hp=30, armor=0, seed=7):
    deck = load_deck(ROOT / "face_hunter/deck.json")
    engine = Engine(deck, deck, seed)
    for seat in (1, 2):
        assert engine.step(seat, {"type": "mulligan", "replace": []}).accepted
    seat, _ = engine.pending()
    player, opponent = engine.player(seat), engine.player(3-seat)
    for card in list(player.hand):
        card.zone = Zone.GRAVEYARD
    player.max_mana, player.used_mana, player.temp_mana = mana, 0, 0
    player.hero.damage = player.hero.max_health-own_hp
    opponent.hero.damage = opponent.hero.max_health-enemy_hp
    opponent.hero.armor = armor
    for cid in own:
        minion = player.summon(cid)
        minion.turns_in_play = 1
    for cid in enemy:
        opponent.summon(cid)
    for cid in hand:
        player.give(cid)
    engine._mark_seen()
    return engine, seat


class BaselineTests(unittest.TestCase):
    def test_exact_deck_and_submission(self):
        deck = json.loads((ROOT / "face_hunter/deck.json").read_text())
        self.assertEqual(validate_deck_data(deck), [])
        self.assertEqual(len(deck["cards"]), 30)
        self.assertEqual(len(set(deck["cards"])), 15)
        answer = response({"phase": "deck_submission", "seq": 7})
        self.assertEqual(answer["seq"], 7)
        self.assertEqual(answer["action"]["cards"], deck["cards"])
        self.assertEqual(answer["action"]["type"], "submit_deck")

    def test_terminal_and_exception_recovery(self):
        self.assertTrue(response({"phase": "game_over", "seq": 2})["game_over"])
        e, i = fixture()
        s = e.view(i); s["seq"] = 3
        with patch("strategy.decide", side_effect=ValueError("injected failure")):
            self.assertTrue(legal(s, response(s)["action"]))

    def test_mulligan_and_tracking_choice(self):
        d = load_deck(ROOT / "face_hunter/deck.json")
        e = Engine(d, d, 11)
        self.assertTrue(e.step(1, decide(e.view(1))).accepted)
        e, i = fixture(hand=["DS1_184"])
        c = e.view(i)["you"]["hand"][0]
        self.assertTrue(e.step(i, {"type": "play_card", "card": c["entity_id"]}).accepted)
        s = e.view(i)
        self.assertEqual(s["phase"], "choice")
        self.assertTrue(e.step(i, decide(s)).accepted)

    def test_legal_targets_and_state_is_immutable(self):
        e, i = fixture(own=["CS2_172"], enemy=["CS2_179"], hand=["DS1_185", "EX1_539"])
        s = e.view(i); old = copy.deepcopy(s)
        a = decide(s)
        self.assertEqual(s, old)
        self.assertTrue(legal(s, a))
        self.assertTrue(e.step(i, a).accepted)
        self.assertFalse(legal(s, {"type": "attack", "attacker": s["you"]["board"][0]["entity_id"], "target": s["opponent"]["hero"]["entity_id"]}))

    def test_cli_reads_current_seq(self):
        e, i = fixture(hand=["CS2_171"])
        s = e.view(i); s["seq"] = 123
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(s))
            p = subprocess.run([sys.executable, str(ROOT / "face_hunter/scripts/decide.py"), str(path)], capture_output=True, text=True, timeout=5)
            self.assertEqual(p.returncode, 0, p.stderr)
            answer = json.loads(p.stdout)
            self.assertEqual(answer["seq"], 123)
            self.assertTrue(legal(s, answer["action"]))


if __name__ == "__main__":
    unittest.main()
