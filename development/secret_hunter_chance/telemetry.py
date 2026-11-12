"""Read-only final search coverage, grouping losses without inventing their causes."""
import json,collections,sys,importlib.util
from development.secret_hunter_program.common import ROOT,write,readlines,quantiles
from development.secret_hunter_chance.audit import reasons
D=ROOT/'docs/secret_hunter_chance';C=ROOT/'development/secret_hunter_chance/candidates'
sys.path.insert(0,str(C/'C2/scripts'))
def model(name):
 spec=importlib.util.spec_from_file_location('audit_'+name,C/name/'scripts/tactical_model.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def aggregate(rs):
 n=len(rs)
 return {'main_states':n,'supported':sum(r['supported'] for r in rs),'supported_rate':sum(r['supported'] for r in rs)/n if n else None,'ordinary_search_entered':sum(r['normal_entered'] for r in rs),'ordinary_action_selected':sum(r['normal_selected'] for r in rs),'ordinary_bounded':sum(r['normal_bounded'] for r in rs),'ordinary_stop_reasons':dict(collections.Counter(r['stop_reason'] for r in rs if r['stop_reason'])),'ordinary_early_exit':dict(collections.Counter(r['early_exit'] for r in rs if r['early_exit'])),'lethal_bounded':sum(r['lethal_bounded'] for r in rs),'lethal_upper_bound_pruned':sum(r['upper_pruned'] for r in rs),'proof_found':sum(r['proof'] for r in rs),'beam_pruned_nodes':sum(r['beam_pruned'] for r in rs),'deduplicated_nodes':sum(r['dedup'] for r in rs),'excluded_transitions':sum(r['excluded'] for r in rs),'unsupported_reasons':dict(collections.Counter(x for r in rs for x in r['unsupported_reasons'])),'reply_comparable':dict(collections.Counter(str(r['reply_comparable']) for r in rs)),'latency_policy_only_s':quantiles([r['time'] for r in rs]),'internal_nodes':quantiles([r['nodes'] for r in rs]),'total_internal_nodes':sum(r['nodes'] for r in rs)}
report={};losses=[]
for arm in ('D1','C2'):
 m=model(arm);folder=ROOT/'experiments'/f'secret-hunter-chance-{arm.lower()}-final-core';allrows=[];groups=collections.defaultdict(list)
 for row in readlines(folder/'results.jsonl'):
  records=[]
  for z in readlines(folder/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl'):
   s=z['state'];i=z['info'];t=i.get('turn_search',{});l=i.get('lethal',{})
   if s['phase']!='main':continue
   r={'seq':s['seq'],'turn':s['turn'],'supported':m.supported(s),'normal_entered':bool(t.get('nodes')),'normal_selected':bool(t.get('action')),'normal_bounded':bool(t.get('bounded_out')),'stop_reason':t.get('stop_reason'),'early_exit':t.get('reason'),'lethal_bounded':bool(l.get('bounded_out')),'upper_pruned':bool(l.get('pruned_by_upper_bound')),'proof':bool(l.get('guaranteed')),'beam_pruned':t.get('beam_pruned',0),'dedup':t.get('deduplicated',0),'excluded':t.get('excluded',0),'unsupported_reasons':reasons(s,m),'reply_comparable':t.get('reply',{}).get('comparable'),'time':z['elapsed_s'],'nodes':i.get('nodes',0),'chance':i.get('chance',{})}
   records.append(r)
  key=f"{row['opponent']}|{'win' if row['score'] else 'loss'}|{'first' if row['first_player']==row['seat'] else 'second'}"
  groups[key].extend(records);allrows.extend(records)
  if not row['score']:
   flags={'unsupported_public_state':any(not x['supported'] for x in records),'unmodelled_top_action':any(x['early_exit']=='top_action_outside_effect_coverage' for x in records),'normal_budget_hit':any(x['normal_bounded'] for x in records),'lethal_budget_hit':any(x['lethal_bounded'] for x in records)}
   losses.append({'arm':arm,'game':row['game'],'opponent':row['opponent'],'seed':row['seed'],'seat':row['seat'],'observed_flags':flags,'earliest_flag_seq':next((x['seq'] for x in records if not x['supported'] or x['normal_bounded'] or x['early_exit']),None),'causal_status':'Unresolved. An observed coverage/budget limitation is not proof that the loss was recoverable.'})
 report[arm]={'all':aggregate(allrows),'groups':{k:aggregate(v) for k,v in groups.items()}}
 def chance_summary(rs):
  active=[r['chance'] for r in rs if r['chance'].get('active')]
  return {'active':len(active),'complete':sum(bool(q.get('complete')) for q in active),'changed':sum(bool(q.get('action')) for q in active),'nodes':sum(q['nodes'] for q in active),'exact_distributions':sum(q['exact_distributions'] for q in active),'sampled_distributions':sum(q['sampled_distributions'] for q in active),'reply_bounded':sum(q.get('reply_bounded',0) for q in active),'reasons':dict(collections.Counter(q.get('reason','complete') for q in active))}
 report[arm]['chance']=chance_summary(allrows)
 report[arm]['chance_groups']={k:chance_summary(v) for k,v in groups.items()}
report['limitations']=['State distributions differ after decisions diverge; coverage improvement is not itself a causal win attribution.','Historical D1 did not log beam pruning or separate node/time stops; zero missing counters are not evidence of exhaustive search.','Dedicated lethal bounded_out combines finite depth/node/time exhaustion; visible reply per-path exhaustion is not fully retained.','Guaranteed proof and ordinary terminal scoring are distinct entrypoints; the deterministic entry can still reject random roots while a separate chance comparison runs. Chance estimates are never proof. Unknown Snake/Juggler replies invalidate C2 comparison.']
write(D/'final-telemetry.json',report);write(D/'final-loss-inventory.json',losses)
print(json.dumps({a:r['all'] for a,r in report.items() if a in ('D1','C2')}))
