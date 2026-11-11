"""Initial paired tactical ablations on the predeclared development block."""
import subprocess,sys,json
from development.secret_hunter_program.common import ROOT
for name in ('H1','H2','H3'):
    meta=json.loads((ROOT/f'docs/secret_hunter_tactics/{name}.json').read_text())
    cmd=[sys.executable,'-m','development.secret_hunter_tactics.run','--candidate',f'development/secret_hunter_tactics/candidates/{name}',
         '--out',f'experiments/tactics-{name.lower()}-development','--start','82100','--seeds','6','--hypothesis',meta['hypothesis']]
    print('RUN',name,flush=True)
    subprocess.run(cmd,check=True)
