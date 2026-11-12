"""Retain a narrower verified-mechanics parent after broad lookahead regressed."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
W=ROOT/'development/secret_hunter_response';D=ROOT/'docs/secret_hunter_response';dest=W/'candidates/E1'
shutil.copytree(W/'candidates/Y1',dest,ignore=shutil.ignore_patterns('__pycache__','scratch'))
cfg=json.loads((dest/'config.json').read_text());cfg.update(version='response-E1',parent='Y1');write(dest/'config.json',cfg)
p=dest/'scripts/public_response.py';s=p.read_text()
s=s.replace("    best=initial;best_v=value(initial,cfg,after_response=True);nodes=0;frontier=[initial];seen=set();bounded=False", "    closed=m.end_effects(initial,'opponent')\n    if closed is None:return {'supported':False,'nodes':0,'reason':'unsupported_opponent_end_effect'}\n    best=closed;best_v=value(closed,cfg,after_response=True);nodes=0;frontier=[initial];seen=set();bounded=False")
s=s.replace("                seen.add(key);v=value(r,cfg,after_response=True)\n                if v<best_v:best,best_v=r,v", "                seen.add(key);closed=m.end_effects(r,'opponent')\n                if closed is None:return {'supported':False,'nodes':nodes,'reason':'unsupported_opponent_end_effect'}\n                v=value(closed,cfg,after_response=True)\n                if v<best_v:best,best_v=closed,v")
p.write_text(s)
a=json.loads((D/'candidates.json').read_text());a['E1']={'parent_ids':['Y1'],'status':'provisional','hypothesis':'Only correct the missing opposing Imp Master end-turn value in Y1 visible response endpoints. Preserve Y1 candidate generator and scoring instead of broad recovery search.','evidence':'B3 retention 317/384 vs Y1 321/384; expansion not reliably helpful. Exact end-turn mechanics passed differential checks and remain a separately testable parent.','source_sha256':fingerprint(dest)};write(D/'candidates.json',a)
