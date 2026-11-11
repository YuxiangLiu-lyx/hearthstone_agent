"""Evidence boundaries and paired-design failures that could produce misleading win rates."""
import copy
from collections import Counter
import json
import unittest

from hs_arena.deck import validate_deck_data
from development.teacher_eval.analyze import RAW, DATA, extract
from development.teacher_eval.compare import paired


class TeacherEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads((RAW/'games.json').read_text())
        cls.report,_=extract(cls.raw)

    def test_official_outcomes_and_submitted_class(self):
        self.assertEqual({k:(v['wins'],v['losses']) for k,v in self.report['summary'].items()},
                         {'bot1':(6,0),'bot2':(1,3),'astra':(0,4)})
        self.assertEqual(self.report['submitted_deck']['hero_class'],'WARLOCK')

    def test_copies_are_maximum_per_game_not_pooled_or_snapshot_counts(self):
        changed=copy.deepcopy(self.raw)
        for game in changed['games']:
            game['observations']*=2
        duplicate,_=extract(changed)
        for group in ('bot1','bot2','astra'):
            def counts(report):
                return {r['card_id']:r['observed_min_copies'] for r in report['opponent_evidence'][group]['cards']}
            self.assertEqual(counts(self.report),counts(duplicate))
        cards={r['card_id']:r['observed_min_copies'] for r in self.report['opponent_evidence']['astra']['cards']}
        self.assertEqual(cards['NEW1_019'],2)
        self.assertEqual(cards['EX1_597'],1)
        self.assertNotIn('EX1_598',cards)  # Imp is generated, not a deck slot.
        self.assertNotIn('GAME_005',cards)

    def test_anonymous_revealed_secret_counts_once(self):
        cards={r['card_id']:r['observed_min_copies'] for r in self.report['opponent_evidence']['bot2']['cards']}
        self.assertEqual(cards['EX1_610'],1)

    def test_every_proxy_retains_evidence_and_is_legal(self):
        for name,group in [('astra-doubled','astra'),('astra-sticky','astra'),('bot2-face','bot2')]:
            deck=json.loads((DATA/'decks'/f'{name}.json').read_text())
            self.assertEqual(validate_deck_data(deck),[])
            counts=Counter(deck['cards'])
            for r in self.report['opponent_evidence'][group]['cards']:
                self.assertGreaterEqual(counts[r['card_id']],r['observed_min_copies'])


class PairedDesign(unittest.TestCase):
    def setUp(self):
        self.a=[{'opponent':name,'group':group,'seed':seed,'seat':seat,'score':0}
                for name,group in [('a1','astra'),('a2','astra'),('h','bot2')]
                for seed in (101,102) for seat in (1,2)]

    def test_identical_arms_zero_gain_and_interval(self):
        result=paired(self.a,self.a,equal_groups=True)
        self.assertEqual(result['gain'],0)
        self.assertEqual(result['gain_seed_cluster_95'],[0,0])
        self.assertEqual(result['seed_clusters'],2)

    def test_family_weight_does_not_depend_on_number_of_proxy_variants(self):
        b=[{**r,'score':int(r['group']=='astra')} for r in self.a]
        self.assertEqual(paired(self.a,b,equal_groups=True)['gain'],.5)
        self.assertAlmostEqual(paired(self.a,b)['gain'],2/3)

    def test_missing_duplicate_and_invalid_games_rejected(self):
        for b in (self.a[:-1],self.a+[self.a[0]],[{**r,'harness_error':'failed'} for r in self.a]):
            with self.assertRaises(ValueError):paired(self.a,b)


if __name__=='__main__':
    unittest.main()
