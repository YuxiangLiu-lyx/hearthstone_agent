"""Persist lineage, same-block evidence, immutable source hashes and resumable state."""
import json,time
from development.secret_hunter_program.common import ROOT,readlines,write,sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check
D=ROOT/'docs/secret_hunter_dgm';W=ROOT/'development/secret_hunter_dgm'
def main():
 archive=json.loads((D/'candidates.json').read_text());ledger=json.loads((D/'budget.json').read_text());runs=[]
 for folder in sorted((ROOT/'experiments').glob('secret-hunter-dgm-*')):
  if not (folder/'summary.json').exists():continue
  cfg=json.loads((folder/'config.json').read_text());summary=json.loads((folder/'summary.json').read_text());cost=next((r for r in ledger['runs'] if r['name']==cfg['name']),{})
  runs.append({'run':folder.name,'candidate':cfg['candidate'].split('/')[-1],'seeds':list(range(cfg['start'],cfg['start']+cfg['seeds'])),'population':cfg['population_sha256'],'split':cfg['split'],'source_hash':cfg['candidate_sha256'],'primary':summary['primary'],'overall':summary['all'],'by_opponent':summary['by_opponent'],'by_actual_first':summary['by_actual_first'],'latency':summary['latency_s'],'cost':cost})
 for name,c in archive.items():
  src=W/'candidates'/name;c.update(id=name,source_sha256=fingerprint(src),config_sha256=sha(src/'config.json'),deck=check(src),strategy_files={str(p.relative_to(src)):sha(p) for p in sorted(src.rglob('*.py'))},tool_sha256={p.name:sha(p) for p in sorted(W.glob('*.py'))},runs=[r for r in runs if r['candidate']==name])
  assert all(r['source_hash']==c['source_sha256'] for r in c['runs']),name+' mutated after evaluation'
 write(D/'candidates.json',archive)
 records=readlines(D/'archive.jsonl');known={(r['id'],r['source_sha256'],r['run_count'],r['status']) for r in records}
 with (D/'archive.jsonl').open('a') as f:
  for name,c in archive.items():
   if (name,c['source_sha256'],len(c['runs']),c['status']) not in known:f.write(json.dumps({'timestamp':time.time(),'run_count':len(c['runs']),**c})+'\n')
 used=set(json.loads((D/'seed-audit.json').read_text())['used_seeds'])
 for r in runs:used.update(r['seeds'])
 write(D/'checkpoint.json',{'archive':'docs/secret_hunter_dgm/candidates.json','archive_events':'docs/secret_hunter_dgm/archive.jsonl','used_seed_values':sorted(used),'reserved_blocks':json.loads((D/'plan.json').read_text())['seed_blocks'],'budget':'docs/secret_hunter_dgm/budget.json','candidate_hashes':{n:c['source_sha256'] for n,c in archive.items()},'final_opened':(D/'final-results.json').exists(),'generator':'Current Codex session reads evidence and proposes code; scheduler does not invent strategies.','new_round':'Read this checkpoint and all older reservations; choose a new ledger and unseen final blocks after current final is opened.'})
 print(json.dumps([{'id':n,'status':c['status'],'runs':len(c['runs'])} for n,c in archive.items()]))
if __name__=='__main__':main()
