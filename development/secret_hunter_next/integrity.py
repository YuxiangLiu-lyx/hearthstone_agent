"""Freeze, schedule, engine, archive, and attempt-budget verification."""
import json,time
from pathlib import Path
import hs_arena
from development.secret_hunter_program.common import ROOT,readlines,write,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot,summarize
D=ROOT/'docs/secret_hunter_next';freeze=json.loads((D/'freeze.json').read_text());protected=json.loads((D/'protected.json').read_text())
assert all((ROOT/p).is_file() and sha(ROOT/p)==digest for p,digest in protected.items()),'Historical file changed'
for n,digest in freeze['baselines'].items():assert fingerprint(ROOT/'development/secret_hunter_next/candidates'/n)==digest
for name,pop in freeze['populations'].items():
 assert sha(ROOT/pop['path'])==pop['sha256'];assert snapshot(json.loads((ROOT/pop['path']).read_text()))==pop['opponents']
runtime=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text());engine=Path(hs_arena.__file__).parent
assert all(sha(engine/p)==digest for p,digest in runtime['installed_files'].items())
final=json.loads((D/'final-freeze.json').read_text());manifest=json.loads((ROOT/'dist/secret-hunter-next-m1.manifest.json').read_text())
assert fingerprint(ROOT/final['source'])==final['source_sha256']==fingerprint(ROOT/manifest['extracted'])
assert sha(ROOT/manifest['zip'])==manifest['zip_sha256']
runs=[];production_decisions=0;defects=0
for folder in sorted((ROOT/'experiments').glob('secret-hunter-next-*')):
 if not (folder/'config.json').exists():continue
 cfg=json.loads((folder/'config.json').read_text());rows=readlines(folder/'results.jsonl')
 if 'planned_games' not in cfg:continue
 expected={(o['name'],s,i) for o in cfg['population'] for s in range(cfg['start'],cfg['start']+cfg['seeds']) for i in (1,2)}
 assert len(rows)==len(expected)==cfg['planned_games']
 assert {(r['opponent'],r['seed'],r['seat']) for r in rows}==expected
 assert fingerprint(ROOT/cfg['candidate'])==cfg['candidate_sha256']
 assert {p.name for p in (folder/'games').iterdir() if p.is_dir()}=={r['game'] for r in rows}
 for r in rows:
  assert json.loads((folder/'games'/r['game']/'result.json').read_text())==r['result']
  assert r['first_player'] in (1,2) and not r.get('harness_error')
  assert r['public_only'] and not r['opponent_errors'] and not r['policy_errors'] and not r['fallbacks'] and not r['over_2s'] and not r.get('course_failure')
  assert not any(r['result']['illegal_counts'].values()) and not any(r['result']['timeouts'].values())
  assert not r['result']['reason'].startswith('forfeit')
  production_decisions+=len(r['decision_times'])
 saved=json.loads((folder/'summary.json').read_text());actual=summarize(rows)
 for k in ('all','by_group','by_opponent','by_actual_first'):assert saved[k]==actual[k]
 runs.append({'run':folder.name,'games':len(rows),'wins':sum(r['score'] for r in rows)})
budget=json.loads((D/'budget.json').read_text());assert all(r['status']=='completed' for r in budget['runs']),[r for r in budget['runs'] if r['status']!='completed']
full=sum(r['full'] for r in budget['runs']);short=sum(r['short'] for r in budget['runs']);elapsed=sum(r['elapsed_s'] for r in budget['runs'])
assert full<=8000 and short<=30000 and elapsed<=14400
cf=readlines(D/'counterfactual-v2.jsonl')+readlines(D/'counterfactual-smoke.jsonl');cf_completed=sum(o['terminal'] and not o['error'] for c in cf for a in c['alternatives'] for o in a['outcomes'])
failed=readlines(D/'counterfactual.jsonl');cf_errors=sum(bool(o['error']) for c in failed for a in c['alternatives'] for o in a['outcomes'])
report={'protected_historical_files':len(protected),'installed_engine_files':len(runtime['installed_files']),'fixed_populations_verified':True,'scheduled_python_matches':sum(r['games'] for r in runs),'terminal_counterfactual_continuations':cf_completed,'failed_counterfactual_attempts_charged':cf_errors,'client_matches':2,'complete_engine_games_including_continuations':sum(r['games'] for r in runs)+cf_completed+2,'full_attempt_charges':full,'conservative_unused_full_reservations':full-sum(r['games'] for r in runs)-cf_completed-cf_errors-2,'short_branch_charges':short,'experiment_elapsed_seconds_sum_conservative':elapsed,'production_decisions_python_harness':production_decisions,'unexpected_execution_defects':0,'final_reserved_games':budget['final_reserve'],'final_charges':sum(r['full'] for r in budget['runs'] if r['final']),'source_and_zip_hashes_match':True,'runs':runs,'note':'Overlapping experiment wall times are summed conservatively. Mechanism microfixtures are short branches; all terminal counterfactual continuations and failed rollout attempts are full charges. Search-internal nodes are separate in final-telemetry.json.'}
write(D/'integrity.json',report);print(json.dumps({k:v for k,v in report.items() if k!='runs'},indent=2))
