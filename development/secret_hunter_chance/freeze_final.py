"""Freeze C2 before touching either final seed block."""
import json,subprocess
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_chance';C=ROOT/'development/secret_hunter_chance/candidates/C2'
assert not (D/'final-freeze.json').exists()
for p in ('runtime-C2.json','development-differential.json','mechanisms-v2.json','proof-checks-v2.json'):assert (D/p).exists()
plan=json.loads((D/'plan.json').read_text());budget=json.loads((D/'budget.json').read_text());assert all(r['status']=='completed' for r in budget['runs'])
assert sum(r['full'] for r in budget['runs'])+3200<=8000
write(D/'final-freeze.json',{'candidate':'C2','source':str(C.relative_to(ROOT)),'source_sha256':fingerprint(C),'config_sha256':sha(C/'config.json'),'deck_sha256':sha(C/'deck.json'),'frozen_utc':datetime.now(timezone.utc).isoformat(),'controls':json.loads((D/'freeze.json').read_text())['baselines'],'plan':plan,'selection':'Independent retention: C2 328/384, C1 327/384, M1 325/384, D1 319/384. C2 vs M1 primary +1.04167 pp CI [-0.26042,+2.86458]; vs D1 +2.60417 pp CI [+0.52083,+4.6875]. Development-selected; final independent confirmation still required.','final_results_seen':False,'no_final_driven_edits':True})
write(D/'STATUS.json',{'stage':'M2_complete_C2_frozen','candidate':'C2','promoted':False,'remaining':['final paired core','final old pool','release reproduction and client checks','report']})
print(json.dumps({'candidate':'C2','source_sha256':fingerprint(C)}))
