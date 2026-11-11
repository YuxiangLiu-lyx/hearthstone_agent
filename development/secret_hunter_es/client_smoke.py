"""Two official no-model client games of the exact extracted research ZIP."""
import json,subprocess,sys
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
from development.secret_hunter_es.run import reserve
candidate='development/secret_hunter_es/release/secret-hunter-program';out='experiments/es-client-smoke'
ledger=json.loads((ROOT/'docs/secret_hunter_es/budget.json').read_text())
if not any(r['out']==out for r in ledger['runs']):reserve(out,'client',2)
assert not list((ROOT/out).glob('g_*')), 'Inspect existing client games before any retry'
(ROOT/out).mkdir(parents=True,exist_ok=True)
write(ROOT/out/'config.json',{'candidate':candidate,'candidate_sha256':fingerprint(ROOT/candidate),
 'seed':381000,'games':2,'mode':'client','hypothesis':'Official client interface and exact Python relay for the frozen extracted ZIP'})
cmd=[str(ROOT/'.venv/bin/hs-arena'),'play','--p1','client:'+candidate,'--p2','greedy','--games','2','--parallel','1','--seed','381000','--out',out]
subprocess.run(cmd,check=True)
