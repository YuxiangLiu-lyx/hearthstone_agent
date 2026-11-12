"""Load existing research state without resetting lineage, budget or seeds."""
import json
from development.secret_hunter_program.common import ROOT,sha
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_dgm'
c=json.loads((D/'checkpoint.json').read_text());a=json.loads((ROOT/c['archive']).read_text());b=json.loads((ROOT/c['budget']).read_text())
for name,h in c['candidate_hashes'].items():assert fingerprint(ROOT/'development/secret_hunter_dgm/candidates'/name)==h
for p,h in json.loads((D/'protected.json').read_text()).items():assert sha(ROOT/p)==h,p
print(json.dumps({'checkpoint':c,'candidates':{n:{'parents':x['parent_ids'],'status':x['status'],'hypothesis':x['hypothesis']} for n,x in a.items()},'budget_charged':{k:sum(r[k] for r in b['runs']) for k in ('full','short')},'unfinished_reservations':[r for r in b['runs'] if r['status']!='completed'],'next_action':'Codex must inspect diagnostics and propose a new child. Never rerun setup or reuse opened final seeds.'},indent=2))
