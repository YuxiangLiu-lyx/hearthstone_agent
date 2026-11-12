"""Exact extracted-artifact games on already used retention seeds, not new evidence."""
import json
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import worker,snapshot,summarize
from development.secret_hunter_response.accounting import reserve,finish
from development.secret_hunter_dgm.deck_guard import check

def main():
 src=ROOT/'development/secret_hunter_response/release/secret-hunter-program';check(src)
 out=ROOT/'experiments/secret-hunter-response-zip-reproduction';assert not out.exists()
 popfile=ROOT/'development/teacher_eval/core.json';pop=json.loads(popfile.read_text());f=json.loads((ROOT/'docs/secret_hunter_response/freeze.json').read_text())['populations']['core']
 assert sha(popfile)==f['sha256'] and snapshot(pop)==f['opponents']
 reserve('zip-reproduction',full=48,final=True,seconds=600);out.mkdir()
 cfg={'candidate':str(src.relative_to(ROOT)),'candidate_sha256':fingerprint(src),'population_sha256':sha(popfile),'opponent_versions':snapshot(pop),'start':960200,'seeds':4,'split':'reproduction','name':'zip-reproduction','population':pop,'planned_games':48}
 write(out/'config.json',cfg);rows=[]
 with ProcessPoolExecutor(max_workers=6) as pool,(out/'results.jsonl').open('w') as log:
  fs=[pool.submit(worker,(str(src),o,seed,seat,str(out),'python')) for o in pop for seed in range(960200,960204) for seat in (1,2)]
  for future in as_completed(fs):
   r=future.result();rows.append(r);log.write(json.dumps(r)+'\n');log.flush()
 summary=summarize(rows);summary['primary']=.5*summary['by_group']['astra']['win_rate']+.5*summary['by_group']['bot2']['win_rate'];write(out/'summary.json',summary);finish('zip-reproduction',completed=len(rows));check(src)
 print('Completed extracted artifact reproduction',len(rows))
if __name__=='__main__':main()
