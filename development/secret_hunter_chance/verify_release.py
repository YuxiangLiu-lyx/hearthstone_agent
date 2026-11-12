"""Verify extracted-code reruns and exact current-sequence no-model client relay."""
import json
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import index
from development.secret_hunter_program.relay_audit import audit
D=ROOT/'docs/secret_hunter_chance';A=ROOT/'experiments/secret-hunter-chance-c2-final-core';B=ROOT/'experiments/secret-hunter-chance-zip-reproduction'
a,b=index(readlines(A/'results.jsonl')),index(readlines(B/'results.jsonl'));assert len(b)==48 and b.keys()<=a.keys();details=[]
for k,r in sorted(b.items()):
 original=a[k];same=all(original['result'][f]==r['result'][f] for f in ('winner','reason','turns','first_player'))
 traces=[[z['action'] for z in readlines(p/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl')] for p,row in ((A,original),(B,r))]
 details.append({'pair':k,'outcome_equal':same,'trace_equal':traces[0]==traces[1],'decisions':[len(t) for t in traces]})
report={'games':len(b),'same_outcomes':sum(x['outcome_equal'] for x in details),'same_action_traces':sum(x['trace_equal'] for x in details),'details':details,'scope':'Used confirmation seeds, exact artifact reproduction only. A wall-time-bounded planner may produce different legal traces on different hardware/load; differences are reported, not removed.'}
write(D/'zip-reproduction.json',report)
clients=[audit(p,1) for p in sorted((ROOT/'experiments/secret-hunter-chance-client').glob('g_*')) if (p/'result.json').exists()];assert len(clients)==2
r={'games':2,'decisions':sum(x['decisions'] for x in clients),'relay_deviations':sum(x['relay_deviations'] for x in clients),'reports':clients,'scope':'Official no-model local client against the existing official Mage; no model-host or Astra evaluation.'}
assert all(not x['worker_errors'] and not x['fallbacks'] and not x['relay_deviations'] for x in clients)
assert all(not any(x['result']['illegal_counts'].values()) and not any(x['result']['timeouts'].values()) for x in clients)
write(D/'client-audit.json',r)
print(json.dumps({k:v for k,v in report.items() if k!='details'}));print(json.dumps({k:v for k,v in r.items() if k!='reports'}))
