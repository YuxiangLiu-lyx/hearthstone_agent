"""Two no-model official client games against the existing official Mage opponent."""
import subprocess,json
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_response.accounting import reserve,finish
reserve('winrate-exact-zip-client',full=2,final=True)
out=ROOT/'experiments/secret-hunter-winrate-client';assert not out.exists()
r=subprocess.run([str(ROOT/'.venv/bin/hs-arena'),'play','--p1','client:development/secret_hunter_winrate/release/secret-hunter-winrate-w3','--p2','greedy','--games','2','--parallel','1','--seed','984000','--out',str(out)],cwd=ROOT,capture_output=True,text=True)
(ROOT/'docs/secret_hunter_winrate/client.log').write_text(r.stdout+r.stderr)
finish('winrate-exact-zip-client',returncode=r.returncode,completed=len(list(out.glob('g_*/result.json'))))
assert r.returncode==0,r.stderr
print(r.stdout[-2000:])
