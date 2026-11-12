"""Recompute all estimates and paired cluster intervals from the complete final schedule."""
import json
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import compare,paired,index
from development.teacher_eval.run import summarize
D=ROOT/'docs/secret_hunter_chance';E=ROOT/'experiments'
def path(arm,pop):return E/f'secret-hunter-chance-{arm.lower()}-final-{pop}'
result={'summaries':{},'paired':{}}
for pop in ('core','guard'):
 for arm in ('D1','H7','C2'):
  p=path(arm,pop);rows=readlines(p/'results.jsonl');cfg=json.loads((p/'config.json').read_text());actual=index(rows)
  expected={(o['name'],seed,seat) for o in cfg['population'] for seed in range(cfg['start'],cfg['start']+cfg['seeds']) for seat in (1,2)}
  assert actual.keys()==expected and len(rows)==cfg['planned_games']
  assert all(r['first_player'] in (1,2) for r in rows)
  assert all(not any(r['result']['illegal_counts'].values()) and not any(r['result']['timeouts'].values()) and not r['opponent_errors'] and not r['policy_errors'] and not r['fallbacks'] and not r.get('course_failure') for r in rows)
  s=summarize(rows)
  if pop=='core':s['primary']=.5*s['by_group']['astra']['win_rate']+.5*s['by_group']['bot2']['win_rate']
  result['summaries'][arm+'-'+pop]=s
 for baseline in ('D1','H7'):
  a,b=path(baseline,pop),path('C2',pop);r=compare(a,b);ar,br=readlines(a/'results.jsonl'),readlines(b/'results.jsonl')
  names=sorted({x['opponent'] for x in ar});r['by_opponent']={n:paired([x for x in ar if x['opponent']==n],[x for x in br if x['opponent']==n]) for n in names}
  r['actual_first_player_matches']=all(index(ar)[k]['first_player']==index(br)[k]['first_player'] for k in index(ar))
  result['paired'][baseline+'-'+pop]=r
r=result['paired']['D1-core'];primary=r['hard_family_macro'];old=result['paired']['H7-guard']
gates={'primary_gain_at_least_one_point':primary['gain']>=.01,'primary_paired_lower_positive':primary['gain_seed_cluster_95'][0]>0,'families_no_drop_over_five_points':all(r['by_group'][g]['gain']>=-.05 for g in ('astra','bot2')),'old_pool_overall_no_drop_over_three_points':old['all']['gain']>=-.03,'old_pool_each_no_drop_over_ten_points':all(v['gain']>=-.10000001 for v in old['by_opponent'].values())}
specialist=all(gates[k] for k in ('primary_gain_at_least_one_point','primary_paired_lower_positive','families_no_drop_over_five_points'));general=specialist and all(gates.values())
write(D/'final-results.json',result)
write(D/'decision.json',{'candidate':'C2','specialist_promoted':specialist,'general_promoted':general,'gates':gates,'primary_vs_D1':primary,'primary_vs_H7':result['paired']['H7-core']['hard_family_macro'],'old_pool_vs_H7':old['all'],'canonical_marker_preserved':'H7','recommended_general':'C2' if general else 'H7','retained_specialist':'C2' if specialist else 'D1','research_zip':'dist/secret-hunter-chance-c2.zip','reason':'All predeclared performance gates pass; reliability still required.' if general else 'Specialist gates pass; general guard fails.' if specialist else 'At least one predeclared specialist gate fails; keep D1/H7 recommendations.','final_candidate_changed':False,'official_submission':False})
if (D/'integrity.json').exists() and (D/'zip-reproduction.json').exists() and (D/'client-audit.json').exists():
 d=json.loads((D/'decision.json').read_text());i=json.loads((D/'integrity.json').read_text());z=json.loads((D/'zip-reproduction.json').read_text());c=json.loads((D/'client-audit.json').read_text());rt=json.loads((D/'runtime-C2.json').read_text())
 d['reliability']={'scheduled_games_both_sides_errors':i['unexpected_execution_defects'],'unexpected_policy_fallbacks':0,'exact_zip_outcomes':z['same_outcomes'],'exact_zip_action_traces':z['same_action_traces'],'client_exact_actions':c['decisions']-c['relay_deviations'],'cli_observed_over_2s':rt['over_2s'],'source_zip_and_frozen_opponents_verified':i['source_and_zip_hashes_match'] and i['fixed_populations_verified'],'offline_harness_failures_separately_charged':i['failed_counterfactual_attempts_charged']}
 write(D/'decision.json',d)
# Apply the predeclared reliability gate after artifact/runtime audits are present.
d=json.loads((D/'decision.json').read_text())
if d.get('reliability'):
 cold=json.loads((D/'chance-cold.json').read_text());pipe=json.loads((D/'pipeline-checks.json').read_text());terminal=json.loads((D/'terminal-semantics.json').read_text())
 rel=d['reliability'];ok=(rel['scheduled_games_both_sides_errors']==0 and rel['unexpected_policy_fallbacks']==0 and rel['exact_zip_outcomes']==48 and rel['exact_zip_action_traces']==48 and rel['client_exact_actions']==c['decisions'] and rel['cli_observed_over_2s']==0 and rel['source_zip_and_frozen_opponents_verified'] and cold['over_2s']==0 and pipe['errors']==0 and pipe['stale_while_hung']['refresh_required'])
 d['gates']['reliability']=ok;d['specialist_promoted'] &= ok;d['general_promoted'] &= ok
 d['recommended_general']='C2' if d['general_promoted'] else 'H7'
 d['retained_specialist']='C2' if d['specialist_promoted'] else 'D1'
 d['reason']='All predeclared specialist, practical general-pool, and reliability gates pass. Recommend C2; preserve historical H7/D1 sources and marker. Fixed proxies only, no real Astra or official submission result.' if d['general_promoted'] else 'At least one predeclared gate failed; see gates and reports.'
 d['fixture_harness_failures_archived']=i['fixture_harness_failures_archived'];d['terminal_projection_differences']={'raw_exact':terminal['raw_exact_matches'],'cases':terminal['n'],'nonterminal_exact':terminal['nonterminal_exact'],'terminal_payoffs_equal':terminal['terminal_payoff_equal'],'explanation':terminal['reason']}
 write(D/'decision.json',d)
print(json.dumps(d,indent=2))
