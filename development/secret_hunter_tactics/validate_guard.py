"""One explicitly accounted additional validation arm, before final confirmation."""
import json,shutil,subprocess,sys
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.compare import compare
D=ROOT/'development/secret_hunter_tactics';O=ROOT/'docs/secret_hunter_tactics'
assert (O/'validation.json').exists()
old=json.loads((O/'validation.json').read_text());write(O/'validation-initial.json',old)
cmd=[sys.executable,'-m','development.secret_hunter_tactics.run','--candidate','development/secret_hunter_tactics/candidates/H7',
 '--out','experiments/tactics-h7-validation','--start','83000','--seeds','10','--split','validation',
 '--hypothesis','Additional coverage-guard candidate predeclared in validation-amendment.json; no final holdout inspected.']
with open('/tmp/tactics-h7-validation.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
s=json.loads((ROOT/'experiments/tactics-h7-validation/summary.json').read_text())
old['arms'].append({'candidate':'H7','summary':s,'out':'experiments/tactics-h7-validation'})
old['comparisons']['H7']=compare(ROOT/'experiments/tactics-b0-validation',ROOT/'experiments/tactics-h7-validation')
old['coin_guard_ablation']=compare(ROOT/'experiments/tactics-h4-validation',ROOT/'experiments/tactics-h7-validation')
selected=max(old['arms'][1:],key=lambda r:(r['summary']['primary']['wins'],r['summary']['base']['wins'],r['candidate']=='H7'))['candidate']
old['selected']=selected;write(O/'validation.json',old)
# This is still a pre-holdout package; archive the first provisional selection rather than discard it.
write(O/'final-freeze-provisional.json',json.loads((O/'final-freeze.json').read_text()))
dest=D/'package/secret-hunter-program';shutil.move(str(dest),str(D/'package-provisional'))
shutil.copytree(D/'candidates'/selected,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
freeze={'selected':selected,'frozen_utc':datetime.now(timezone.utc).isoformat(),'tree_sha256':fingerprint(dest),
 'config_sha256':sha(dest/'config.json'),'deck_sha256':sha(dest/'deck.json'),'baseline_sha256':fingerprint(D/'candidates/B0'),
 'seeds':list(range(291000,291040)),'promotion_gate':'Primary paired seed-cluster lower 95% bound >0, >=1 pp gain, reliability/latency/relay gates.'}
write(O/'final-freeze.json',freeze);write(O/'holdout-ready.json',freeze)
print('H7',s['primary']['wins'],s['primary']['n'],'FROZEN FINALIST',selected,flush=True)
