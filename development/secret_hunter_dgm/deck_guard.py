"""Validate byte order, multiset, official class/copy limits and actual submission."""
import collections,json,subprocess,sys
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha
EXPECTED='54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4'
COUNTS=dict(zip('EX1_029 EX1_080 DS1_184 EX1_162 EX1_531 EX1_533 EX1_554 EX1_066 EX1_610 EX1_611 NEW1_019 EX1_536 EX1_538 EX1_539 EX1_617 NEW1_031 DS1_070 EX1_534 EX1_543'.split(),[2,2,1,1,2,1,1,1,2,2,2,2,2,2,1,2,1,2,1]))
def check(src):
 from hs_arena.deck import load_deck
 src=Path(src);deck=json.loads((src/'deck.json').read_text())
 assert sha(src/'deck.json')==EXPECTED
 assert deck['hero_class']=='HUNTER' and len(deck['cards'])==30 and collections.Counter(deck['cards'])==COUNTS
 load_deck(src/'deck.json')
 code='import json,sys;sys.path.insert(0,sys.argv[1]);from program_policy import decide;print(json.dumps(decide({"phase":"deck_submission"},{} )[0]))'
 action=json.loads(subprocess.check_output([sys.executable,'-c',code,str(src/'scripts')],text=True))
 assert action=={'type':'submit_deck','hero_class':'HUNTER','cards':deck['cards']}
 return {'sha256':EXPECTED,'cards':30,'official_validation':True,'actual_deck_submission_matches':True}
if __name__=='__main__':print(json.dumps(check(ROOT/sys.argv[1])))
