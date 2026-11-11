"""Official-engine regressions for visible self-lethal attack consequences."""
from pathlib import Path
import subprocess
import sys
import unittest

from tests.test_control_priest import fixture
from development.benchmarks.run import load_policy
from hearthstone.enums import Zone


class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy, cls.actions = load_policy("development/candidates/priest-v2-safety")

    def execute(self, engine, seat):
        state = engine.view(seat)
        action = self.policy.decide(state, {"face_weight": .35})
        self.assertTrue(self.actions.legal(state, action))
        self.assertTrue(engine.step(seat, action).accepted)
        return action

    def test_heal_before_killing_leper(self):
        e, i = fixture(own=["CS2_182"], enemy=["EX1_029"], mana=2, hp=2)
        first = self.execute(e, i)
        self.assertEqual(first["type"], "hero_power")
        self.execute(e, i)
        self.assertFalse(e.over)
        self.assertEqual(e.player(i).hero.health, 2)

    def test_heal_before_abomination_explosion(self):
        e, i = fixture(own=["CS2_200"], enemy=["EX1_097"], mana=2, hp=2)
        self.assertEqual(self.execute(e, i)["type"], "hero_power")
        self.execute(e, i)
        self.assertFalse(e.over)
        self.assertEqual(e.player(i).hero.health, 2)

    def test_fatigue_draw_deathrattle_does_not_suicide(self):
        e, i = fixture(own=["EX1_096"], enemy=["CS2_172"], mana=2, hp=1)
        for c in list(e.player(i).deck):
            c.zone = Zone.GRAVEYARD
        self.assertEqual(self.execute(e, i)["type"], "hero_power")
        self.execute(e, i)
        self.assertFalse(e.over)
        self.assertEqual(e.player(i).hero.health, 2)

    def test_safe_direct_lethal_is_preserved(self):
        e, i = fixture(own=["CS2_200"], enemy=["EX1_029"], mana=2, hp=2, enemy_hp=6)
        self.assertEqual(self.execute(e, i)["type"], "attack")
        self.assertEqual(e.winner, i)


if __name__ == "__main__":
    unittest.main()
