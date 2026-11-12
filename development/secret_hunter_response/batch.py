"""Run arms sequentially in isolated interpreters with a fixed paired schedule."""
import argparse,subprocess,sys
from development.secret_hunter_program.common import ROOT
p=argparse.ArgumentParser();p.add_argument('--arms',required=True);p.add_argument('--label',required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--population',default='core');p.add_argument('--final',action='store_true');a=p.parse_args()
for arm in a.arms.split(','):
 cmd=[sys.executable,'-m','development.secret_hunter_response.run','--candidate','development/secret_hunter_response/candidates/'+arm,'--name',arm.lower()+'-'+a.label,'--start',str(a.start),'--seeds',str(a.seeds),'--population',a.population,'--workers','6']+(['--final'] if a.final else [])
 subprocess.run(cmd,cwd=ROOT,check=True,timeout=1750)
