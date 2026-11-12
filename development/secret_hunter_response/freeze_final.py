"""Freeze one challenger and two diagnostic ablations before opening final seeds."""
import json,time
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check
D=ROOT/'docs/secret_hunter_response';W=ROOT/'development/secret_hunter_response'
def main():
 assert not (D/'final-freeze.json').exists()
 for name,digest in json.loads((D/'protected.json').read_text()).items():assert sha(ROOT/name)==digest,name
 for n,digest in json.loads((D/'freeze.json').read_text())['baselines'].items():assert fingerprint(W/'candidates'/n)==digest
 arms=['Y1','K1','E1','B3','C3']
 for arm in arms:check(W/'candidates'/arm)
 for n in ('y1-isolated-stale','e1-isolated-stale'):
  r=json.loads((D/(n+'.json')).read_text());assert len(r['cases'])==8 and all(x['refresh_required'] and not x['stale_action'] and x['elapsed_s']<2 for x in r['cases'])
 plan=json.loads((D/'plan.json').read_text());plan['amendments'].append({'stage':'before final opening','time':time.time(),'change':'Keep E1 as the sole promotion-eligible challenger. Add frozen B3/C3 as diagnostic core-only A/B/C ablations (960 games each) to answer the response question on the same genuinely new seed block. No post-final selection or promotion of these diagnostic arms. Guardrail remains Y1/K1/E1. Total final matches 6480; within the 16000-attempt cap.'})
 plan['final_core']['arms']=arms;plan['final_core']['games']=4800;write(D/'plan.json',plan)
 freeze={'created':time.time(),'challenger':'E1','source':'development/secret_hunter_response/candidates/E1','source_sha256':fingerprint(W/'candidates/E1'),'source_hashes':{n:fingerprint(W/'candidates'/n) for n in arms},'arms_core':arms,'arms_guardrail':['Y1','K1','E1'],'diagnostic_only':['B3','C3'],'zip':'dist/secret-hunter-krush-response-e1.zip','reason':'Across three common development blocks E1 ties Y1 primary (85.091%), while B3/C3 fall below it (84.701%/84.440%). E1 is the smallest verified mechanics change; no evidence-based expectation of superiority is asserted.','no_more_policy_changes':True,'no_final_driven_selection':True}
 write(D/'final-freeze.json',freeze)
 a=json.loads((D/'candidates.json').read_text())
 for n,v in a.items():
  v['source_sha256']=fingerprint(W/'candidates'/n);v['deck_sha256']=sha(W/'candidates'/n/'deck.json')
  v['runs']=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'experiments').glob('secret-hunter-response-'+n.lower()+'-*')) if (p/'summary.json').exists()]
  if n in ('B2','C2','B3','C3'):v['status']='stepping_stone';v['limitation']='Mechanism/candidate coverage improved; no retained development win-rate gain.'
 a['E1']['status']='provisional';write(D/'candidates.json',a)
 with (D/'archive.jsonl').open('a') as f:
  for n,v in a.items():f.write(json.dumps({'event':'pre_final_freeze','id':n,**v})+'\n')
 print(json.dumps(freeze,indent=2))
if __name__=='__main__':main()
