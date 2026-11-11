"""Reproducible (2+4) ES: fresh common blocks, parent re-evaluation, 21 sigmas.

This uses multiplicative log-normal sigma adaptation, explicitly differing from
arXiv v1 equation 9's printed addition. No competitive coevolution is performed.
"""
import json,math,random,shutil,subprocess,sys
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
D=ROOT/'development/secret_hunter_es';O=ROOT/'docs/secret_hunter_es'
BOUNDS=dict(own_attack=(.5,2.8),own_health=(.1,1.5),enemy_attack=(.5,2.8),enemy_health=(.1,1.5),
 shield=(.3,4),taunt=(.1,3.5),stealth=(0,1.5),windfury=(0,1.5),poison=(.3,5),death=(.3,2),engine=(.3,2.5),
 face=(.4,2.5),hero_health=(.03,.7),hand=(.1,2.5),weapon=(.1,1.5),risk=(.5,8),secret=(.2,2.5),
 exposure=(0,1.5),beast=(0,1.5),mana=(0,.5),finish=(0,1.5))

def main():
 rng=random.Random(2026111107);n=len(BOUNDS);tau=1/math.sqrt(2*math.sqrt(n));global_tau=1/math.sqrt(2*n)
 parents=['C2','C3'];sigmas={name:{k:.12 for k in BOUNDS} for name in parents}
 archive={'algorithm':'(2+4) self-adaptive ES; fixed opponents; fresh parent re-evaluation',
          'rng_seed':2026111107,'bounds':BOUNDS,'generations':[],'sigma_rule':'clip(sigma * exp(tau*N_i + global_tau*N), .01, .35)'}
 assert not (O/'evolution.json').exists()
 for generation in range(3):
  offspring=[];mutations=[]
  for j in range(4):
   parent=parents[j%2];name=f'E{generation+1}{j+1}';dest=D/'candidates'/name
   shutil.copytree(D/'candidates'/parent,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
   cfg=json.loads((dest/'config.json').read_text());shared=rng.gauss(0,1);sigma={};weights={}
   for k,(lo,hi) in BOUNDS.items():
    sigma[k]=max(.01,min(.35,sigmas[parent][k]*math.exp(tau*rng.gauss(0,1)+global_tau*shared)))
    gene=(cfg['weights'][k]-lo)/(hi-lo)
    gene=max(0,min(1,gene+rng.gauss(0,sigma[k])))
    weights[k]=round(lo+(hi-lo)*gene,6)
   cfg.update(version=name,parent=parent,weights=weights)
   for k,choices in [('turn_width',[6,10,14]),('turn_depth',[7,9,11]),('turn_nodes',[250,350,550])]:
    if rng.random()<.45:cfg[k]=rng.choice(choices)
   # Keep the same conservative time budget; explicit node/width/depth mutations.
   write(dest/'config.json',cfg);sigmas[name]=sigma;offspring.append(name)
   mutations.append({'name':name,'parent':parent,'sigma':sigma,'weights':weights,
                     'search':{k:cfg[k] for k in ['turn_width','turn_depth','turn_nodes']},'tree_sha256':fingerprint(dest)})
  fitness=[]
  for name in parents+offspring:
   out=f'experiments/es-g{generation+1}-{name.lower()}'
   cmd=[sys.executable,'-m','development.secret_hunter_es.run','--candidate',str((D/'candidates'/name).relative_to(ROOT)),
        '--out',out,'--start',str(78200+10*generation),'--seeds','4','--hypothesis',
        f'ES generation {generation+1}: shared new seeds, both seats, frozen pool; evaluate parents and offspring']
   with open(f'/tmp/es-g{generation+1}-{name.lower()}.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
   s=json.loads((ROOT/out/'summary.json').read_text())
   fitness.append({'name':name,'primary_wins':s['primary']['wins'],'primary_n':s['primary']['n'],'base_wins':s['base']['wins'],'out':out})
   print(generation+1,fitness[-1],flush=True)
  ordered=sorted(fitness,key=lambda f:(-f['primary_wins'],-f['base_wins']))
  parents=[f['name'] for f in ordered[:2]]
  archive['generations'].append({'index':generation+1,'offspring':mutations,'fitness':fitness,'retained':parents})
  archive['final_parents']=parents;write(O/'evolution.json',archive)
  print('Retained',parents,flush=True)
if __name__=='__main__':main()
