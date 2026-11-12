"""Sequential isolated-arm scheduling; never mixes same-named runtime modules."""
import argparse,json,subprocess,sys
from development.secret_hunter_program.common import ROOT
p=argparse.ArgumentParser();p.add_argument('--arms',nargs='+',required=True);p.add_argument('--stage',required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--population',default='core');p.add_argument('--final',action='store_true');a=p.parse_args()
for arm in a.arms:
 name=arm.lower()+'-'+a.stage
 with (ROOT/'docs/secret_hunter_dgm'/f'{name}.log').open('w') as f:
  cmd=[sys.executable,'-m','development.secret_hunter_dgm.run','--candidate','development/secret_hunter_dgm/candidates/'+arm,'--name',name,'--start',str(a.start),'--seeds',str(a.seeds),'--population',a.population,'--workers','6']
  if a.final:cmd+=['--final']
  subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=1750)
 print(name,json.loads((ROOT/'experiments'/('secret-hunter-dgm-'+name)/'summary.json').read_text())['all']['wins'],flush=True)
