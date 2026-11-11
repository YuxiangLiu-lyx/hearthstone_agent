"""Use the same nearest-rank percentile definition for all saved latency reports."""
import json,math
from development.secret_hunter_program.common import ROOT,write
D=ROOT/'docs/secret_hunter_next'
for name in ('M1','M2'):
 p=D/f'runtime-{name}.json';r=json.loads(p.read_text())
 if 'legacy_floor_order_quantiles' not in r:r['legacy_floor_order_quantiles']={k:r[k] for k in ('all_latency_s','cold_latency_s')}
 def stats(xs):
  xs=sorted(xs);return {str(q):xs[min(len(xs)-1,math.ceil(len(xs)*q)-1)] for q in (.5,.95,.99,1)}
 r['all_latency_s']=stats([c['elapsed_s'] for c in r['details']]);r['cold_latency_s']=stats([c['elapsed_s'] for c in r['details'] if c['tag'].startswith('cold')]);r['percentile_definition']='nearest rank: sorted[ceil(n*q)-1]. Original console logs used floor((n-1)*q); preserved under legacy_floor_order_quantiles.'
 write(p,r)
 print(name,r['cold_latency_s'])
