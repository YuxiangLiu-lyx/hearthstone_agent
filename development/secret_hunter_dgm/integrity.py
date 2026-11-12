"""Verify immutable boundaries, schedules, attempts and extracted release evidence."""
import json,time
from pathlib import Path
import hs_arena
from development.secret_hunter_program.common import ROOT,sha,readlines,write
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import snapshot,summarize
from development.secret_hunter_dgm.deck_guard import check
D=ROOT/'docs/secret_hunter_dgm';freeze=json.loads((D/'freeze.json').read_text());protected=json.loads((D/'protected.json').read_text())
assert all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in protected.items())
for n,h in freeze['baselines'].items():assert fingerprint(ROOT/'development/secret_hunter_dgm/candidates'/n)==h
for name,pop in freeze['populations'].items():
 assert sha(ROOT/pop['path'])==pop['sha256'] and snapshot(json.loads((ROOT/pop['path']).read_text()))==pop['opponents']
runtime=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text());engine=Path(hs_arena.__file__).parent
assert all(sha(engine/p)==h for p,h in runtime['installed_files'].items())
final=json.loads((D/'final-freeze.json').read_text());manifest=json.loads((ROOT/final['zip']).with_suffix('.manifest.json').read_text())
assert fingerprint(ROOT/final['source'])==final['source_sha256']==fingerprint(ROOT/manifest['extracted'])
assert sha(ROOT/final['zip'])==manifest['zip_sha256'];check(ROOT/manifest['extracted'])
runs=[];decisions=0;defects=0
for folder in sorted((ROOT/'experiments').glob('secret-hunter-dgm-*')):
 if not (folder/'config.json').exists():continue
 cfg=json.loads((folder/'config.json').read_text())
 if 'planned_games' not in cfg:continue
 rows=readlines(folder/'results.jsonl');expected={(o['name'],s,i) for o in cfg['population'] for s in range(cfg['start'],cfg['start']+cfg['seeds']) for i in (1,2)}
 assert len(rows)==len(expected)==cfg['planned_games'] and {(r['opponent'],r['seed'],r['seat']) for r in rows}==expected
 assert fingerprint(ROOT/cfg['candidate'])==cfg['candidate_sha256'];check(ROOT/cfg['candidate'])
 for r in rows:
  assert r['result']==json.loads((folder/'games'/r['game']/'result.json').read_text())
  assert r['first_player'] in (1,2) and not r.get('harness_error')
  bad=(not r['public_only'] or r['opponent_errors'] or r['policy_errors'] or r['fallbacks'] or r['over_2s'] or r.get('course_failure') or any(r['result']['illegal_counts'].values()) or any(r['result']['timeouts'].values()) or r['result']['reason'].startswith('forfeit'))
  defects+=bool(bad);decisions+=len(r['decision_times'])
 saved=json.loads((folder/'summary.json').read_text());actual=summarize(rows)
 for k in ('all','by_group','by_opponent','by_actual_first'):assert saved[k]==actual[k]
 runs.append({'name':folder.name,'n':len(rows),'wins':sum(r['score'] for r in rows)})
b=json.loads((D/'budget.json').read_text());assert all(r['status'] in ('completed','failed') for r in b['runs'])
full=sum(r['full'] for r in b['runs']);short=sum(r['short'] for r in b['runs']);seconds=sum(r['elapsed_s'] for r in b['runs']);assert full<=16000 and short<=80000 and seconds<=21600
cf=[c for tag in ('pilot','v2','adaptive','strong') for c in readlines(D/f'counterfactual-{tag}.jsonl')]
rollouts=[o for c in cf for a in c['alternatives'] for o in a['outcomes']];cferrors=sum(bool(o['error']) for o in rollouts)
completed=sum(r['n'] for r in runs)+len(rollouts)+2
rt=json.loads((D/'runtime-Y1.json').read_text());z=json.loads((D/'zip-reproduction.json').read_text());clients=json.loads((D/'client-audit.json').read_text())
report={'protected_historical_files':len(protected),'installed_engine_files':len(runtime['installed_files']),'fixed_populations_verified':True,'source_zip_hashes_match':True,'scheduled_python_games':sum(r['n'] for r in runs),'python_policy_decisions':decisions,'normal_game_defects_both_sides':defects,'terminal_counterfactuals':len(rollouts),'counterfactual_errors':cferrors,'client_games':2,'completed_full_games':completed,'full_attempt_charges':full,'unused_conservative_full_reservations':full-completed,'short_branch_charges':short,'experiment_wall_seconds_summed':seconds,'final_full_charges':sum(r['full'] for r in b['runs'] if r['final']),'failed_runs':[r for r in b['runs'] if r['status']=='failed'],'runtime_normal_cold_over_2s':rt['over_2s'],'unresolved_fault_test_timeout':True,'zip_exact_outcomes':z['same_outcomes'],'zip_exact_traces':z['same_action_traces'],'client_exact_actions':clients['decisions']-clients['relay_deviations'],'model_host_test_this_round':False,'model_cost':'No extra model/API calls; current Codex session billing not exposed.','runs':runs}
write(D/'integrity.json',report)
d=json.loads((D/'decision.json').read_text());d['gates']['reliability']=False;d['reliability']=report|{'runs':None};d['promotion']='not_promoted';d['recommended']='H7';d['reason']='Preserve H7. A >2.5s fault-injected full-CLI test remains unexplained; eight later correct refreshes do not erase it. Performance gates are reported independently. No post-final policy repair or seed reuse.';write(D/'decision.json',d)
print(json.dumps({k:v for k,v in report.items() if k!='runs'},indent=2))
