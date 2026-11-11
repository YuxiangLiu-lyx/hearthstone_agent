"""Localize opaque enemy draws instead of rejecting the entire tactical branch."""
import json,shutil
from pathlib import Path
base=Path('development/secret_hunter_next/candidates');d=base/'M2';shutil.copytree(base/'M1',d,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
p=d/'scripts/tactical_model.py';s=p.read_text()
s=s.replace('if not m.get("silenced") and m["card_id"] not in SAFE:', 'if not m.get("silenced") and m["card_id"] not in SAFE and not (side is state["opponent"] and m["card_id"] in {"EX1_608", "NEW1_012"}):')
s=s.replace('"planning_mode": state.get("planning_mode", "base")}', '"planning_mode": state.get("planning_mode", "base"), "public_owner": state["you"]["hero"]["entity_id"]}')
s=s.replace('            if cid in ("EX1_096", "EX1_012"):\n                return False', '''            if cid in ("EX1_096", "EX1_012"):
                if side['hero']['entity_id'] == state.get('public_owner') or side.get('deck_size', 0) <= 0 or side.get('hand_size', 0) >= 10:
                    return False
                # No identity is fabricated. Enemy draws do not change current public actions.
                side['hand_size'] = side.get('hand_size', 0) + 1
                side['deck_size'] -= 1''')
s=s.replace('values.append(tuple(c[\'card_id\'] for c in state[\'you\'].get(\'secrets\', [])))',"values.append((state['opponent'].get('hand_size',0), state['opponent'].get('deck_size',0)))\n    values.append(tuple(c['card_id'] for c in state['you'].get('secrets', [])))")
p.write_text(s)
c=json.loads((d/'config.json').read_text());c.update(version='next-M2',parent='M1');(d/'config.json').write_text(json.dumps(c,indent=2)+'\n')
