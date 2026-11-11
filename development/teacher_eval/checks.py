"""Run engine regressions without changing historical experiment ledgers or reports."""
import json
import unittest

# The shared fixture parser accepts --candidate and --out. Importing does not run its main.
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_tactics import tactical_checks as tactics
from development.secret_hunter_program.common import ROOT, write
from program_policy import decide

CFG=json.loads((c.CANDIDATE/'config.json').read_text())


class ArcaneShot(unittest.TestCase):
    def test_two_shot_lethal_before_visible_incoming_death(self):
        e,i=c.fixture(enemy=['CS2_200'],hand=['DS1_185','DS1_185'],mana=2,hp=1,enemy_hp=4)
        for _ in range(3):
            if e.over:break
            s=e.view(i);action,info=decide(s,CFG)
            self.assertEqual(info['reason'],'guaranteed_lethal')
            self.assertTrue(e.step(i,action).accepted)
        self.assertTrue(e.over)
        self.assertEqual(e.winner,i)

    def test_one_mana_shot_removes_knife_juggler(self):
        e,i=c.fixture(enemy=['NEW1_019'],hand=['DS1_185'],mana=1)
        s=e.view(i);action,info=decide(s,CFG)
        self.assertEqual(action['type'],'play_card',info)
        self.assertEqual(action.get('target'),s['opponent']['board'][0]['entity_id'],info)
        self.assertTrue(e.step(i,action).accepted)
        self.assertFalse(e.player(3-i).field)


if __name__=='__main__':
    loader=unittest.defaultTestLoader
    suite=unittest.TestSuite([loader.loadTestsFromTestCase(tactics.Tactics),loader.loadTestsFromTestCase(ArcaneShot)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'fixtures':c.FIXTURES,'evidence':tactics.EVIDENCE,
            'scope':'Existing tactical regressions plus actual-engine Arcane Shot lethal/removal; old ledgers unchanged.'}
    write(ROOT/c.ARGS.out,report)
    raise SystemExit(not result.wasSuccessful())
