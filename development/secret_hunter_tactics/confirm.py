"""Evaluate immutable release and F2 on the predeclared untouched 40-seed block."""
import json,subprocess,sys
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.compare import compare
D=ROOT/'development/secret_hunter_tactics';O=ROOT/'docs/secret_hunter_tactics'
freeze=json.loads((O/'final-freeze.json').read_text());manifest=json.loads((ROOT/'dist/secret-hunter-tactics.manifest.json').read_text())
assert fingerprint(ROOT/manifest['extracted'])==freeze['tree_sha256']
for name,candidate in [('b0','development/secret_hunter_tactics/candidates/B0'),('final',manifest['extracted'])]:
 out=f'experiments/tactics-{name}-confirmation'
 cmd=[sys.executable,'-m','development.secret_hunter_tactics.run','--candidate',candidate,'--out',out,
      '--start','291000','--seeds','40','--split','confirmation','--hypothesis','Frozen 40-seed paired final confirmation; no selection or tuning after opening this block']
 with open(f'/tmp/tactics-{name}-confirmation.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(name,json.loads((ROOT/out/'summary.json').read_text())['primary'],flush=True)
report=compare(ROOT/'experiments/tactics-b0-confirmation',ROOT/'experiments/tactics-final-confirmation')
write(O/'final-paired.json',report)
print(json.dumps(report['primary']),flush=True)
