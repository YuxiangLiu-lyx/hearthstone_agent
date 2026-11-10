"""Paired seed-cluster bootstrap; draws are losses under coursework scoring."""
import argparse,json,random,statistics
from collections import defaultdict
from pathlib import Path

def compare(base, challenger):
 def read(p):
  return {(g['seed'],g['opponent'],g['candidate_seat']):g for g in map(json.loads,(Path(p)/'games.jsonl').read_text().splitlines())}
 a,b=read(base),read(challenger)
 if a.keys()!=b.keys(): raise ValueError('Unmatched seed/opponent/seat schedules')
 ma=json.loads((Path(base)/'manifest.json').read_text()); mb=json.loads((Path(challenger)/'manifest.json').read_text())
 if ma['population']!=mb['population']:raise ValueError('Opponent configuration differs')
 byseed=defaultdict(list); byopp=defaultdict(list)
 for k in a:
  if a[k]['reason'] in ('void_engine_error','harness_error','aborted') or b[k]['reason'] in ('void_engine_error','harness_error','aborted'):
   raise ValueError('An engine/harness failure invalidates paired comparison; inspect first')
  delta=b[k]['score']-a[k]['score'];byseed[k[0]].append(delta);byopp[k[1]].append(delta)
 values=[statistics.mean(v) for v in byseed.values()]
 rng=random.Random(88217)
 boot=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(5000))
 ci=[boot[125],boot[4874]]
 summary=json.loads((Path(challenger)/'summary.json').read_text())
 stable=all(summary[k]==0 for k in ('illegal','timeouts','early_exits','policy_errors','void_or_errors'))
 groups={k:statistics.mean(v) for k,v in byopp.items()}
 return {'base':str(base),'challenger':str(challenger),'paired_games':len(a),'seed_clusters':len(values),
         'delta_win_rate':statistics.mean(values),'cluster_bootstrap95':ci,'group_deltas':groups,
         'execution_stable':stable,'gate_pass':ci[0]>0 and min(groups.values())>=-.10 and stable,
         'gate':'positive lower 95% paired seed-cluster CI; no group decline > 10 percentage points; zero execution defects',
         'note':'Exploratory comparisons require independent holdout before promotion. Multiple candidate selection can inflate training gains.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('challenger');p.add_argument('--out');a=p.parse_args()
 r=compare(a.base,a.challenger);print(json.dumps(r,indent=2))
 if a.out:Path(a.out).write_text(json.dumps(r,indent=2))
