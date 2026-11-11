"""Fresh eight-seed ablation and finalist selection, before any final evaluation."""
import json,shutil,subprocess,sys
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.compare import compare
D=ROOT/'development/secret_hunter_es';O=ROOT/'docs/secret_hunter_es'

def main():
 evolution=json.loads((O/'evolution.json').read_text());assert len(evolution['generations'])==3
 fitness=evolution['generations'][-1]['fitness']
 trained=sorted([f for f in fitness if f['name'].startswith('E')],key=lambda f:(-f['primary_wins'],-f['base_wins']))[0]['name']
 cfg=json.loads((D/'candidates'/trained/'config.json').read_text());untrained='C3' if cfg['response_exposure'] else 'C2'
 arms=['B0','D1','C1',untrained,trained]
 write(O/'validation-plan.json',{'frozen_before_validation_utc':datetime.now(timezone.utc).isoformat(),'arms':arms,
 'trained_selection':'Best evolved individual from final generation, even if an unmutated parent outranks it',
 'seeds':list(range(79000,79008)),'hashes':{a:fingerprint(D/'candidates'/a) for a in arms}})
 results=[]
 for a in arms:
  out=f'experiments/es-{a.lower()}-validation'
  cmd=[sys.executable,'-m','development.secret_hunter_es.run','--candidate',str((D/'candidates'/a).relative_to(ROOT)),
       '--out',out,'--start','79000','--seeds','8','--split','validation','--hypothesis',
       'Fresh same-block comparison: F2, minimal snake fix, coverage, untrained features, evolved features']
  with open(f'/tmp/es-{a.lower()}-validation.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  s=json.loads((ROOT/out/'summary.json').read_text());results.append({'candidate':a,'summary':s,'out':out})
  print(a,s['primary']['wins'],s['primary']['n'],s['base']['wins'],flush=True)
 # Pick the best new candidate; the baseline is a reference, not a proposal.
 candidates=results[1:];selected=max(candidates,key=lambda r:r['summary']['primary']['wins'])['candidate']
 report={'arms':results,'selected':selected,'evolved':trained,'untrained':untrained,
         'comparisons':{r['candidate']:compare(ROOT/results[0]['out'],ROOT/r['out']) for r in results[1:]},
         'trained_vs_untrained':compare(ROOT/f'experiments/es-{untrained.lower()}-validation',ROOT/f'experiments/es-{trained.lower()}-validation')}
 write(O/'validation.json',report)
 src=D/'candidates'/selected;dest=D/'package/secret-hunter-program'
 shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
 # Preserve exact selected config and policy bytes; package name is already canonical.
 write(O/'final-freeze.json',{'selected':selected,'frozen_utc':datetime.now(timezone.utc).isoformat(),
 'tree_sha256':fingerprint(dest),'config_sha256':sha(dest/'config.json'),'deck_sha256':sha(dest/'deck.json'),
 'baseline_sha256':fingerprint(D/'candidates/B0'),'seeds':list(range(281000,281040)),
 'promotion_gate':'Primary seed-cluster paired lower 95% bound > 0, gain >= .01, and reliability/latency gates'})
 print('Frozen finalist',selected,flush=True)
if __name__=='__main__':main()
