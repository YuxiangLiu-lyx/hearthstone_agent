"""Audit frozen boundaries, package contents, raw outcomes and budget closure."""
import json,zipfile,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write,sha,readlines
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot
D=ROOT/'docs/secret_hunter_response';W=ROOT/'development/secret_hunter_response'
def main():
 protected=json.loads((D/'protected.json').read_text());changed=[name for name,digest in protected.items() if sha(ROOT/name)!=digest];assert not changed,changed
 import hs_arena
 engine=Path(hs_arena.__file__).parent;engine_manifest=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text())
 for file,digest in engine_manifest['installed_files'].items():assert sha(engine/file)==digest,file
 frozen=json.loads((D/'freeze.json').read_text());final=json.loads((D/'final-freeze.json').read_text())
 for n,pop in frozen['populations'].items():
  file=ROOT/f'development/teacher_eval/{n}.json';assert sha(file)==pop['sha256'] and snapshot(json.loads(file.read_text()))==pop['opponents']
 for name,digest in final['source_hashes'].items():assert fingerprint(W/'candidates'/name)==digest
 from development.secret_hunter_dgm.deck_guard import check
 for p in (W/'candidates').iterdir():
  if p.is_dir():check(p)
 check(W/'release/secret-hunter-program')
 manifest=json.loads((ROOT/final['zip']).with_suffix('.manifest.json').read_text());assert sha(ROOT/final['zip'])==manifest['zip_sha256'];assert fingerprint(W/'release/secret-hunter-program')==final['source_sha256']
 with zipfile.ZipFile(ROOT/final['zip']) as z:
  names=z.namelist();assert len({n.split('/')[0] for n in names})==1
  assert all(Path(n).suffix in ('.py','.md','.json') and not any(x in n for x in ('offline','bigram','models-','training','game/','scratch/','__pycache__')) for n in names)
  assert sum(i.file_size for i in z.infolist())<10_000_000
 rows=[];cfgs=[]
 for folder in sorted((ROOT/'experiments').glob('secret-hunter-response-*')):
  if (folder/'results.jsonl').exists():
   rs=readlines(folder/'results.jsonl');cfg=json.loads((folder/'config.json').read_text());assert len(rs)==cfg['planned_games'];assert not any(r.get('harness_error') or r.get('policy_errors') or not r.get('public_only',True) for r in rs);rows+=rs;cfgs.append(str(folder.relative_to(ROOT)))
 normal={'games':len(rows),'own_decisions':sum(len(r.get('decision_times',[])) for r in rows),'illegal_both_players':sum(sum(r['result']['illegal_counts'].values()) for r in rows),'timeouts_both_players':sum(sum(r['result']['timeouts'].values()) for r in rows),'fallbacks':sum(r.get('fallbacks',0) for r in rows),'over_2s':sum(r.get('over_2s',0) for r in rows)}
 b=json.loads((D/'budget.json').read_text());assert all(r['status']!='reserved' for r in b['runs']),[r['name'] for r in b['runs'] if r['status']=='reserved']
 full=sum(r['full'] for r in b['runs']);short=sum(r['short'] for r in b['runs']);elapsed=sum(r['elapsed_s'] for r in b['runs']);assert full<=16000 and short<=80000 and elapsed<=21600
 runtime=json.loads((D/'runtime-release.json').read_text());cold=json.loads((D/'chance-cold.json').read_text());fault=json.loads((D/'release-isolated-stale.json').read_text());client=json.loads((D/'client-audit.json').read_text());repro=json.loads((D/'zip-reproduction.json').read_text())
 passed=not any(normal[k] for k in ('illegal_both_players','timeouts_both_players','fallbacks','over_2s')) and runtime['over_2s']==0 and cold['over_2s']==0 and all(r['refresh_required'] and not r['stale_action'] and r['elapsed_s']<2 for r in fault['cases']) and client['relay_deviations']==0 and repro['same_outcomes']==48
 report={'installed_engine_files':len(engine_manifest['installed_files']),'protected_files':len(protected),'changed_protected':changed,'normal':normal,'budget':{'full_attempts_charged':full,'short_charged':short,'experiment_wall_s_sum':elapsed,'development_elapsed_wall_s':time.time()-json.loads((D/'plan.json').read_text())['started'],'conservative_charges_include_unused_failed_reservations':True,'failed_runs':[r for r in b['runs'] if r['status']=='failed']},'package':manifest,'reliability_pass':passed,'trace_reproduction':{'outcomes':repro['same_outcomes'],'actions':repro['same_action_traces'],'n':48},'model_cost':'No paid APIs, external models or model-host matches. Codex session token/currency cost not available.','prior_timeout':'Historical Y1 concurrent fault retained. This round independently passed 8 stale/hang checks; no claim of hard real-time guarantee.'}
 write(D/'integrity.json',report)
 decision=json.loads((D/'decision.json').read_text());decision['reliability']=passed;decision['promotion']='confirmed_champion' if decision['performance_pass'] and passed else 'not_promoted';decision['recommendation']='Retain Y1 as research baseline; E1 is a reproducible research artifact, not a promoted release.' if decision['promotion']=='not_promoted' else 'E1 meets the preregistered performance and reliability gates.';write(D/'decision.json',decision)
 a=json.loads((D/'candidates.json').read_text());a['E1']['status']='confirmed_champion' if decision['promotion']=='confirmed_champion' else 'stepping_stone'
 for arm,v in a.items():v['source_sha256']=fingerprint(W/'candidates'/arm);v['config_sha256']=sha(W/'candidates'/arm/'config.json');v['runs']=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'experiments').glob('secret-hunter-response-'+arm.lower()+'-*')) if (p/'summary.json').exists()]
 write(D/'candidates.json',a)
 with (D/'archive.jsonl').open('a') as f:
  for arm,v in a.items():f.write(json.dumps({'event':'final_audit','id':arm,**v})+'\n')
 seeds=set(json.loads((D/'seed-audit.json').read_text())['used_seed_values'])
 for start,count in json.loads((D/'plan.json').read_text())['seed_blocks'].values():seeds.update(range(start,start+count))
 checkpoint={'parent_checkpoint':'docs/secret_hunter_dgm/checkpoint.json','archive':'docs/secret_hunter_response/candidates.json','budget':'docs/secret_hunter_response/budget.json','used_seed_values':sorted(seeds),'candidate_hashes':{n:v['source_sha256'] for n,v in a.items()},'candidate_status':{n:v['status'] for n,v in a.items()},'final_opened':True,'next_hypothesis':'Replace shallow endpoint value with continuation-consistent ranking on public-compatible multi-card responses, and audit equal root coverage before increasing depth. Keep fitted models offline.','generator':'Codex reads archived failures and proposes code; Python scheduler alone does not generate strategies.'};write(D/'checkpoint.json',checkpoint)
 print(json.dumps({k:v for k,v in report.items() if k not in ('package','budget')},indent=2));print(json.dumps(report['budget']))
if __name__=='__main__':main()
