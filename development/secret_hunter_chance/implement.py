"""Create C1's independent bounded chance projection and search integration."""
from pathlib import Path
import json
D=Path('development/secret_hunter_chance/candidates/C1/scripts')
p=D/'tactical_model.py';s=p.read_text()
s=s.replace('def summon(state, side, cid, entity_id=None, hand_card=None, position=None):','def summon(state, side, cid, entity_id=None, hand_card=None, position=None, trigger=True):')
s=s.replace('    refresh(state)\n\n\ndef cleanup', "    refresh(state)\n    if trigger and '_chance_tape' in state:\n        from chance_model import knives\n        knives(state, side, entity_id)\n\n\ndef cleanup")
s=s.replace("        if result.get('planning_mode')=='response' and cid=='NEW1_019':return None", "        if result.get('planning_mode')=='response' and cid=='NEW1_019':return None")
s=s.replace("if cid in PLAY_MINIONS | {'EX1_538','NEW1_031'} and any", "if '_chance_tape' not in result and cid in PLAY_MINIONS | {'EX1_538','NEW1_031'} and any")
s=s.replace('summon(result, y, cid, c["entity_id"], c, action.get("position"))','summon(result, y, cid, c["entity_id"], c, action.get("position"), trigger=False)')
s=s.replace("                # Enemy hero attack in the observation is zero outside its turn.", "                # Enemy hero attack in the observation is zero outside its turn.\n            if '_chance_tape' in result:\n                from chance_model import knives\n                knives(result, y, c['entity_id'])")
p.write_text(s)
