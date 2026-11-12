"""Test complementary capabilities together; improvements are never assumed additive."""
import shutil,json
from development.secret_hunter_dgm.create_round1 import child,W,D
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_dgm.deck_guard import check
p=W/'T1/scripts/chance_reply.py';s=p.read_text().replace("distribution=transitions(s,a);count+=1","distribution=transitions(s,a);count+=len(distribution) if distribution else 1");p.write_text(s)
x=child('X1','S1','Combine response-selected chance continuations, corrected Krush clock, and independently retained M2 local effects; test interaction and regressions.')
shutil.copyfile(W/'B1/scripts/race_plan.py',x/'scripts/race_plan.py')
s=(x/'scripts/tactical_model.py').read_text();m1=(W/'K1/scripts/tactical_model.py').read_text();m2=(W/'E1/scripts/tactical_model.py').read_text()
import difflib
# Apply only the four explicitly audited local-effect hunks, preserving chance hooks.
s=s.replace('if not m.get("silenced") and m["card_id"] not in SAFE:', 'if not m.get("silenced") and m["card_id"] not in SAFE and not (side is state["opponent"] and m["card_id"] in {"EX1_608", "NEW1_012"}):')
s=s.replace('"planning_mode": state.get("planning_mode", "base")}', '"planning_mode": state.get("planning_mode", "base"), "public_owner": state["you"]["hero"]["entity_id"]}')
s=s.replace('            if cid in ("EX1_096", "EX1_012"):\n                return False', '''            if cid in ("EX1_096", "EX1_012"):
                if side['hero']['entity_id'] == state.get('public_owner') or side.get('deck_remaining', 0) <= 0 or side.get('hand_size', 0) >= 10:
                    return False
                side['hand_size'] = side.get('hand_size', 0) + 1
                side['deck_remaining'] -= 1''')
s=s.replace("    values.append(tuple(c['card_id'] for c in state['you'].get('secrets', [])))","    values.append((state['opponent'].get('hand_size',0), state['opponent'].get('deck_remaining',0)))\n    values.append(tuple(c['card_id'] for c in state['you'].get('secrets', [])))")
(x/'scripts/tactical_model.py').write_text(s)
a=json.loads((D/'candidates.json').read_text());a['X1']['parent_ids']=['S1','B1','E1'];write(D/'candidates.json',a)
check(x);check(W/'T1')
