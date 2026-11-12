"""Archive evidence-driven descendants; never overwrite an evaluated parent."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_response';W=ROOT/'development/secret_hunter_response';a=json.loads((D/'candidates.json').read_text())
for child,parent in [('B2','B1'),('C2','C1')]:
 dest=W/'candidates'/child;shutil.copytree(W/'candidates'/parent,dest,ignore=shutil.ignore_patterns('__pycache__','scratch'))
 cfg=json.loads((dest/'config.json').read_text());cfg.update(version='response-'+child,parent=parent);write(dest/'config.json',cfg)
 p=dest/'scripts/response_search.py';s=p.read_text();s=s.replace("best=value(r,cfg,True);front=[r];seen=set();nodes=0", "base=value(s,cfg,True)\n    recovery_cfg={**cfg,'race_face_bonus':0,'hand_clock_bonus':0,'board_clock_bonus':0}\n    best=value(r,recovery_cfg,True);initial=best;front=[r];seen=set();nodes=0\n    def conservative():return base+.15*min(6,max(0,best-initial))")
 s=s.replace("return best,nodes\n                q=m.transition", "return conservative(),nodes\n                q=m.transition")
 s=s.replace("seen.add(key);v=value(q,cfg,True);best=max(best,v)","seen.add(key);v=value(q,recovery_cfg,True);best=max(best,v)")
 s=s.replace("    return best,nodes\n\ndef hypotheses", "    return conservative(),nodes\n\ndef hypotheses")
 p.write_text(s)
 a[child]={'parent_ids':[parent],'status':'provisional','hypothesis':'B1/C1 lost early tempo by replacing current value with a shallow next-turn value that advanced the hand clock again. Keep post-response value and use a bounded recovery increment with future clock bonuses disabled.','evidence':'pilot: Y1 81/96, B1 76/96, C1 75/96. Examples: seed 960102 Astra board seat 2 seq 7, seed 960101 Bot2 seats 1 seq 5.','source_sha256':fingerprint(dest)}
for n in ('B1','C1'):
 a[n]['status']='rejected';a[n]['source_sha256']=fingerprint(W/'candidates'/n);a[n]['failure']='Pilot degraded early tempo; recovery endpoint value overwhelms current-turn safety.'
write(D/'candidates.json',a)
