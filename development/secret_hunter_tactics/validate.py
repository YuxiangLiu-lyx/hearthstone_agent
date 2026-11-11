"""Independent ten-seed ablations and a frozen finalist before holdout access."""
import json,shutil,subprocess,sys
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.compare import compare
D=ROOT/'development/secret_hunter_tactics';O=ROOT/'docs/secret_hunter_tactics'

def main():
    tuning=json.loads((O/'tuning.json').read_text());trained=tuning['best_mutation']
    arms=['B0','H1','H5','H4',trained]
    write(O/'validation-plan.json',{'frozen_before_validation_utc':datetime.now(timezone.utc).isoformat(),'arms':arms,
      'selection':'Best primary wins among new candidates, then Greedy wins, then earlier simpler arm on an exact tie.',
      'seeds':list(range(83000,83010)),'hashes':{a:fingerprint(D/'candidates'/a) for a in arms}})
    results=[]
    for a in arms:
        out=f'experiments/tactics-{a.lower()}-validation'
        cmd=[sys.executable,'-m','development.secret_hunter_tactics.run','--candidate',str((D/'candidates'/a).relative_to(ROOT)),
             '--out',out,'--start','83000','--seeds','10','--split','validation','--hypothesis',
             'Fresh paired ablation: F2, combo/coverage, race without response, race with response, trained combination']
        with open(f'/tmp/tactics-{a.lower()}-validation.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        s=json.loads((ROOT/out/'summary.json').read_text());results.append({'candidate':a,'summary':s,'out':out})
        print(a,s['primary']['wins'],s['primary']['n'],s['base']['wins'],flush=True)
    selected=max(results[1:],key=lambda r:(r['summary']['primary']['wins'],r['summary']['base']['wins']))['candidate']
    write(O/'validation.json',{'arms':results,'selected':selected,'trained':trained,
      'comparisons':{r['candidate']:compare(ROOT/results[0]['out'],ROOT/r['out']) for r in results[1:]},
      'response_ablation':compare(ROOT/'experiments/tactics-h5-validation',ROOT/'experiments/tactics-h4-validation'),
      'trained_vs_parent':compare(ROOT/'experiments/tactics-h4-validation',ROOT/f'experiments/tactics-{trained.lower()}-validation')})
    src=D/'candidates'/selected;dest=D/'package/secret-hunter-program';shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    write(O/'final-freeze.json',{'selected':selected,'frozen_utc':datetime.now(timezone.utc).isoformat(),
      'tree_sha256':fingerprint(dest),'config_sha256':sha(dest/'config.json'),'deck_sha256':sha(dest/'deck.json'),
      'baseline_sha256':fingerprint(D/'candidates/B0'),'seeds':list(range(291000,291040)),
      'promotion_gate':'Primary paired seed-cluster lower 95% bound >0, >=1 pp gain, reliability/latency/relay gates.'})
    print('Frozen finalist',selected,flush=True)
if __name__=='__main__':main()
