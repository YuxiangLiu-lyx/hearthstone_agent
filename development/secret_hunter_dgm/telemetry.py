"""Coverage and failure inventory from actual final public decision logs."""
import collections,json
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
D=ROOT/'docs/secret_hunter_dgm';allreport={};losses=[]
for arm in ('K0','K1','Y1'):
 folder=ROOT/f'experiments/secret-hunter-dgm-{arm.lower()}-final-core';records=[];groups=collections.defaultdict(list)
 for row in readlines(folder/'results.jsonl'):
  local=[]
  for z in readlines(folder/'games'/row['game']/f'p{row["seat"]}'/'observations.jsonl'):
   s=z['state'];i=z['info'];t=i.get('turn_search',{});c=i.get('chance',{});l=i.get('lethal',{})
   if s['phase']!='main':continue
   rec={'seq':s['seq'],'turn':s['turn'],'ordinary_supported':t.get('supported'),'normal_nodes':t.get('nodes',0),'early_exit':t.get('reason'),'stop_reason':t.get('stop_reason'),'ordinary_bounded':t.get('bounded_out',False),'proof':l.get('guaranteed',False),'lethal_bounded':l.get('bounded_out',False),'nodes':i.get('nodes',0),'time':z['elapsed_s'],'chance_active':c.get('active',False),'chance_complete':c.get('complete',False),'chance_changed':bool(c.get('action')),'chance_reason':c.get('reason'),'isolated_bad_roots':c.get('excluded_response_roots',0),'exact_distributions':c.get('exact_distributions',0),'sampled_distributions':c.get('sampled_distributions',0),'krush_hand':any(x['card_id']=='EX1_543' for x in s['you']['hand']),'misdirection_active':any(x['card_id']=='EX1_533' for x in s['you'].get('secrets',[]))}
   local.append(rec)
  records.extend(local);groups[f"{row['opponent']}|{'win' if row['score'] else 'loss'}|{'first' if row['first_player']==row['seat'] else 'second'}"].extend(local)
  if not row['score']:losses.append({'arm':arm,'seed':row['seed'],'game':row['game'],'opponent':row['opponent'],'seat':row['seat'],'actual_first':row['first_player']==row['seat'],'flags':{'unmodeled_top_action':any(r['early_exit']=='top_action_outside_effect_coverage' for r in local),'bounded_search':any(r['ordinary_bounded'] or r['lethal_bounded'] for r in local),'chance_rejection':any(r['chance_reason'] for r in local)},'first_important_error':'unresolved; observational flags do not establish recoverable loss'})
 def aggregate(rs):
  return {'main_states':len(rs),'pure_policy_seconds':quantiles([r['time'] for r in rs]),'internal_production_nodes':sum(r['nodes'] for r in rs),'ordinary_nodes':sum(r['normal_nodes'] for r in rs),'ordinary_known_supported':sum(r['ordinary_supported'] is True for r in rs),'ordinary_unentered_or_unknown':sum(r['ordinary_supported'] is None for r in rs),'ordinary_bounded':sum(r['ordinary_bounded'] for r in rs),'ordinary_stop_reasons':dict(collections.Counter(r['stop_reason'] for r in rs if r['stop_reason'])),'root_coverage_guards':dict(collections.Counter(r['early_exit'] for r in rs if r['early_exit'])),'guaranteed_proofs':sum(r['proof'] for r in rs),'chance_active':sum(r['chance_active'] for r in rs),'chance_complete':sum(r['chance_complete'] for r in rs),'chance_changed':sum(r['chance_changed'] for r in rs),'chance_reasons':dict(collections.Counter(r['chance_reason'] for r in rs if r['chance_reason'])),'isolated_bad_response_roots':sum(r['isolated_bad_roots'] for r in rs),'exact_distributions':sum(r['exact_distributions'] for r in rs),'sampled_distributions':sum(r['sampled_distributions'] for r in rs),'krush_hand_states':sum(r['krush_hand'] for r in rs),'misdirection_states':sum(r['misdirection_active'] for r in rs)}
 allreport[arm]={'all':aggregate(records),'groups':{k:aggregate(v) for k,v in groups.items()}}
allreport['limits']=['Observed policy state distributions differ; coverage is not causal win attribution.','K0 does not distinguish ordinary node/time stops. Missing telemetry is unknown, not zero exhaustion.','Guaranteed proof remains separate from chance endpoints. Single Misdirection experiment T1 is not in Y1; Snake/Juggler and multi-secret chance replies remain guarded.']
write(D/'final-telemetry.json',allreport);write(D/'final-loss-inventory.json',losses)
print(json.dumps({k:v['all'] for k,v in allreport.items() if k!='limits'}))
