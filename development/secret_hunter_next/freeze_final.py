"""Freeze one eligible candidate after the predeclared final development retention block."""
import json
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.compare import compare
D=ROOT/'docs/secret_hunter_next';E=ROOT/'experiments'
rows=json.loads((D/'candidates.json').read_text())
reasons={'M1':'Retained: highest eligible primary in the new 24-seed retention block; simpler and faster than R1. Final confirmation remains unopened.', 'R1':'Rejected: initial +1/144 did not replicate; -1/288 versus M1 in retention, with higher latency.', 'L1':'Research only: lower held-game preference quality despite +3/144 development wins; current course forbids bundled model weights. Not a publishable learned-model candidate.', 'M2':'Rejected: same total 143/192 as M1 but primary down 1.04 pp; broader local coverage was not sufficient benefit.', 'R2':'Rejected: +3/192 over M2 but only +0.52 pp primary over M1, with materially higher latency; no demonstrated gain warrants the extra combined mechanisms.'}
for r in rows:
 name=r['candidate'];r['source_sha256']=fingerprint(ROOT/'development/secret_hunter_next/candidates'/name)
 r['runs']=[]
 for p in E.glob('secret-hunter-next-*/summary.json'):
  cfg=json.loads((p.parent/'config.json').read_text())
  if cfg['candidate'].endswith('/'+name):r['runs'].append({'run':p.parent.name,'summary':json.loads(p.read_text())})
 r['retention_reason']=reasons[name];r['status']='final_frozen' if name=='M1' else 'rejected'
write(D/'candidates.json',rows)
for left,right in [('d1-retain','m1-retain'),('m1-retain','r1-retain')]:write(D/f'{left}-vs-{right}.json',compare(E/('secret-hunter-next-'+left),E/('secret-hunter-next-'+right)))
c=ROOT/'development/secret_hunter_next/candidates/M1'
write(D/'final-freeze.json',{'candidate':'M1','source':str(c.relative_to(ROOT)),'source_sha256':fingerprint(c),'deck_sha256':sha(c/'deck.json'),'config_sha256':sha(c/'config.json'),'frozen_utc':datetime.now(timezone.utc).isoformat(),'core_start':931000,'core_seeds':40,'guardrail_start':932000,'guardrail_seeds':20,'arms':['M1','D1','H7'],'gates_unchanged':True,'production_has_learned_model':False,'no_post_final_changes':True,'rationale':reasons['M1']})
print(json.dumps(json.loads((D/'final-freeze.json').read_text()),indent=2))
