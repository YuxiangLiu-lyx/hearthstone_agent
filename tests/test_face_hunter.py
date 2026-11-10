"""Official-engine behavioral tests; fixture access is never shipped in the skill."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import time
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

    def test_bow_against_large_minion_has_no_poison_flag(self):
        from baseline import decide as basic
        e,i=fixture(enemy=['CS2_200'],mana=0)
        e.player(i).summon('EX1_536')
        s=e.view(i)
        self.assertNotIn('poisonous',s['you']['hero'])
        a=basic(s)
        self.assertTrue(legal(s,a))
        self.assertEqual(a['target'],s['opponent']['hero']['entity_id'])

    def test_hard_watchdog_returns_legal_fallback(self):
        e,i=fixture();s=e.view(i);s['seq']=99
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'skill'
            shutil.copytree(ROOT/'face_hunter',d,ignore=shutil.ignore_patterns('__pycache__'))
            (d/'game').mkdir();(d/'game/state.json').write_text(json.dumps(s))
            (d/'config.json').write_text('{"decision_budget_s":0.1}')
            (d/'scripts/strategy.py').write_text('import time\ndef decide(state,config=None):\n    time.sleep(10)\n')
            start=time.perf_counter()
            p=subprocess.run([sys.executable,'scripts/decide.py'],cwd=d,capture_output=True,text=True,timeout=3)
            self.assertLess(time.perf_counter()-start,1.5)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('fallback',p.stderr)
            self.assertTrue(legal(s,json.loads(p.stdout)['action']))


class LethalTests(unittest.TestCase):
    def assert_real_lethal(self, engine, seat):
        from lethal_planner import search
        actions = []
        while not engine.over and len(actions) < 18:
            state = engine.view(seat)
            result = search(state, budget_s=1.0, max_nodes=10000, beam_width=48)
            self.assertTrue(result["guaranteed"], (actions, result))
            self.assertTrue(legal(state, result["first_action"]))
            self.assertTrue(engine.step(seat, result["first_action"]).accepted)
            actions.append(result["first_action"])
        self.assertEqual(engine.winner, seat)
        return actions

    def test_01_minion_attack(self):
        self.assert_real_lethal(*fixture(own=["CS2_172"], mana=0, enemy_hp=3))

    def test_02_hero_power_finisher(self):
        self.assert_real_lethal(*fixture(own=["CS2_172"], mana=2, enemy_hp=5))

    def test_03_beast_before_kill_command(self):
        e, i = fixture(hand=["DS1_175", "EX1_539"], mana=4, enemy_hp=5)
        cards = {c["entity_id"]:c["card_id"] for c in e.view(i)["you"]["hand"]}
        actions = self.assert_real_lethal(e, i)
        self.assertEqual(cards[actions[0]["card"]], "DS1_175")

    def test_04_one_wolf_unleash(self):
        self.assert_real_lethal(*fixture(enemy=["CS2_231"]*3, hand=["DS1_175", "EX1_538"], mana=4, enemy_hp=6))

    def test_05_two_wolves_unleash(self):
        self.assert_real_lethal(*fixture(enemy=["CS2_231"]*3, hand=["DS1_175"]*2+["EX1_538"], mana=5, enemy_hp=9))

    def test_06_board_space_limits_hounds(self):
        from lethal_planner import search
        e, i = fixture(own=["CS2_120"]*5, enemy=["CS2_231"]*5, hand=["DS1_175", "EX1_538"], mana=4, enemy_hp=5)
        for m in e.player(i).field: m.turns_in_play=0
        self.assertFalse(search(e.view(i), budget_s=.5, max_nodes=5000)["guaranteed"])

    def test_07_taunt_blocks_face(self):
        from lethal_planner import search
        e, i = fixture(own=["CS2_172"], enemy=["CS2_179"], mana=0, enemy_hp=3)
        self.assertFalse(search(e.view(i))["guaranteed"])

    def test_08_armor(self):
        from lethal_planner import search
        e, i = fixture(hand=["DS1_185"], mana=1, enemy_hp=2, armor=1)
        self.assertFalse(search(e.view(i))["guaranteed"])
        self.assert_real_lethal(*fixture(hand=["DS1_185"], mana=3, enemy_hp=2, armor=2))

    def test_09_coin(self):
        self.assert_real_lethal(*fixture(hand=["GAME_005", "DS1_185"], mana=0, enemy_hp=2))

    def test_10_random_companion_is_not_guaranteed(self):
        from lethal_planner import search, probabilistic_lethal
        e, i = fixture(hand=["NEW1_031"], mana=3, enemy_hp=4)
        self.assertFalse(search(e.view(i))["guaranteed"])
        chance = probabilistic_lethal(e.view(i), budget_s=.5, max_nodes=6000)
        self.assertAlmostEqual(chance["probability"], 1/3)
        self.assertTrue(chance["depends_on_random"])
        self.assertTrue(legal(e.view(i), chance["first_action"]))

    def test_11_dead_wolf_removes_aura(self):
        from tactical_model import prepare, transition
        e, i = fixture(own=["DS1_175", "EX1_538t", "EX1_538t"], enemy=["CS1_042"], mana=0, enemy_hp=3)
        s=e.view(i)
        a={"type":"attack", "attacker":s["you"]["board"][0]["entity_id"], "target":s["opponent"]["board"][0]["entity_id"]}
        projected=transition(prepare(s),a)
        self.assertEqual([m["attack"] for m in projected["you"]["board"]],[1,1])
        self.assert_real_lethal(e,i)

    def test_12_order_preserves_last_beast(self):
        e, i = fixture(own=["CS2_171"], enemy=["CS1_042"], hand=["EX1_539"], mana=3, enemy_hp=5)
        actions=self.assert_real_lethal(e,i)
        self.assertEqual(actions[0]["type"], "play_card")

    def test_hyena_gains_attack_from_beast_death(self):
        self.assert_real_lethal(*fixture(own=["EX1_531", "CS2_171"], enemy=["CS1_042"], hand=["DS1_185"], mana=1, enemy_hp=4))

    def test_weapon_burn_and_hero_power(self):
        e, i = fixture(hand=["DS1_185"], mana=3, enemy_hp=7)
        e.player(i).summon("EX1_536")
        self.assert_real_lethal(e,i)

    def test_search_avoids_baseline_development_over_lethal(self):
        from baseline import decide as basic
        from lethal_planner import search
        e,i=fixture(own=['DS1_175'],hand=['EX1_534','EX1_539'],mana=6,enemy_hp=8)
        self.assertTrue(search(e.view(i))["guaranteed"])
        for _ in range(15):
            if e.over:break
            a=basic(e.view(i))
            if a['type']=='end_turn':break
            self.assertTrue(e.step(i,a).accepted)
        self.assertFalse(e.over)
        self.assert_real_lethal(*fixture(own=['DS1_175'],hand=['EX1_534','EX1_539'],mana=6,enemy_hp=8))

    def test_new_bow_uses_only_observed_unused_attack(self):
        from lethal_planner import search
        from state_features import with_public_history
        e,i=fixture(hand=['EX1_536'],mana=3,enemy_hp=3)
        s=e.view(i)
        history=[{'event':'turn_start','turn':s['turn'],'player':i}]
        enriched=with_public_history(s,history)
        self.assertTrue(search(enriched)['guaranteed'])
        history.append({'event':'attack','attacker':s['you']['hero'],'player':i})
        self.assertFalse(search(with_public_history(s,history))['guaranteed'])

    def test_unknown_secrets_abstain_and_budget(self):
        import time
        from lethal_planner import search
        e, i = fixture(own=["CS2_172"]*6, enemy=["CS2_179"]*6, hand=["DS1_185"]*5, enemy_hp=30)
        s=e.view(i);s["opponent"]["secrets_count"]=1
        self.assertFalse(search(s)["supported"])
        s["opponent"]["secrets_count"]=0
        start=time.perf_counter();r=search(s,budget_s=.01,max_nodes=100)
        self.assertLess(time.perf_counter()-start,.2)
        self.assertLessEqual(r["nodes"],100)

    def test_one_step_differential(self):
        from hs_arena._fp import init_engine
        from tactical_model import prepare, options, transition, supported
        memo={id(c):c for c in init_engine().db.values()}
        cases=[dict(own=["DS1_175","CS2_171","EX1_531"],enemy=["CS1_042","EX1_008"],hand=["DS1_185","EX1_539","EX1_538","DS1_175"]),
               dict(own=["EX1_534","EX1_531"],enemy=["CS2_200"],hand=["GAME_005","EX1_536"]),
               dict(own=["EX1_029","CS2_172"],enemy=["EX1_556","CS2_033"],hand=["CS2_124"])]
        count=0
        for setup in cases:
            e,i=fixture(**setup);s=e.view(i);self.assertTrue(supported(s))
            for a in options(prepare(s)):
                if not legal(s,a):continue
                predicted=transition(prepare(s),a)
                if predicted is None:continue
                clone=copy.deepcopy(e,dict(memo));self.assertTrue(clone.step(i,a).accepted)
                observed=clone.view(i)
                for side in ('you','opponent'):
                    for key in ('health','armor'):
                        self.assertEqual(predicted[side]['hero'][key],observed[side]['hero'][key],(a,side,key))
                    fields=lambda rows:[(m['card_id'],m['attack'],m['health'],m.get('divine_shield',False)) for m in rows]
                    self.assertEqual(fields(predicted[side]['board']),fields(observed[side]['board']),(a,side))
                self.assertEqual(predicted['you']['mana'],observed['you']['mana'],a)
                count+=1
        self.assertGreater(count,25)


class TwoTurnRiskTests(unittest.TestCase):
    def test_banked_kill_command_and_power(self):
        from next_turn import features
        e,i=fixture(own=['CS2_120'],hand=['EX1_539'],mana=4,enemy_hp=7)
        f=features(e.view(i))
        self.assertEqual(f['burn_with_existing_beast'],7)
        self.assertEqual(f['burn_without_existing_beast'],5)
        self.assertLess(f['survival_risk'],.1)

    def test_two_health_next_turn_power(self):
        from next_turn import features
        e,i=fixture(mana=1,enemy_hp=2)
        f=features(e.view(i))
        self.assertEqual(f['next_mana'],2)
        self.assertEqual(f['burn_without_existing_beast'],2)
        self.assertGreaterEqual(f['lethal_confidence'],.95)

    def test_hero_power_lethal_precedes_gambling(self):
        from strategy import choose_with_info
        e,i=fixture(hand=['NEW1_031'],mana=3,enemy_hp=2,own_hp=1)
        a,info=choose_with_info(e.view(i),{'lethal':True,'two_turn':True,'risk':True})
        self.assertEqual(a,{'type':'hero_power'})
        self.assertEqual(info['mode'],'guaranteed_lethal')

    def test_comeback_requires_a_real_random_win_branch(self):
        from strategy import choose_with_info
        e,i=fixture(enemy=['CS2_200'],hand=['NEW1_031'],mana=3,enemy_hp=4,own_hp=1)
        a,info=choose_with_info(e.view(i),{'lethal':True,'two_turn':True,'risk':True})
        self.assertEqual(info['mode'],'high_risk_comeback')
        self.assertAlmostEqual(info['random_lethal']['probability'],1/3)
        self.assertTrue(legal(e.view(i),a))

    def test_survival_trade_when_face_is_fatal(self):
        from strategy import decide
        e,i=fixture(own=['CS2_201'],enemy=['CS2_200'],mana=0,enemy_hp=30,own_hp=7)
        for c in list(e.player(3-i).hand):c.zone=Zone.GRAVEYARD
        s=e.view(i)
        a=decide(s,{'lethal':True,'two_turn':True,'risk':True})
        self.assertEqual(a.get('target'),s['opponent']['board'][0]['entity_id'])
        self.assertTrue(e.step(i,a).accepted)

    def test_saved_wolf_unleash_is_in_next_turn_estimate(self):
        from next_turn import features
        e,i=fixture(enemy=['CS2_231']*4,hand=['DS1_175','EX1_538'],mana=3,enemy_hp=8)
        f=features(e.view(i))
        self.assertEqual(f['hound_combo_reach'],8)


if __name__ == "__main__":
    unittest.main()
