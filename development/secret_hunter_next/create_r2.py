"""Retest the scenario direction on the localized mechanism parent with actual deck count."""
import json,shutil
from pathlib import Path
B=Path('development/secret_hunter_next/candidates');d=B/'R2';shutil.copytree(B/'M2',d,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
for name in ('state_features.py','public_response.py','race_plan.py'):
 shutil.copyfile(B/'R1/scripts'/name,d/'scripts'/name)
p=d/'scripts/public_response.py';s=p.read_text().replace("o.get('deck_size', 20)","o.get('deck_remaining', 20)");p.write_text(s)
p=d/'scripts/tactical_model.py';s=p.read_text().replace('"public_owner": state["you"]["hero"]["entity_id"]}', '"public_owner": state["you"]["hero"]["entity_id"], "public_opponent_evidence": copy.deepcopy(state.get("public_opponent_evidence", {}))}');p.write_text(s)
c=json.loads((d/'config.json').read_text());c.update(version='next-R2',parent='M2',hidden_scenarios=True,generator_value=.8,reply_budget_s=.24);(d/'config.json').write_text(json.dumps(c,indent=2)+'\n')
