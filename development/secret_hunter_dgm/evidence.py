"""Summarize adaptive diagnostics without relabeling conditional wins as repairs."""
import collections,json,random,statistics
from development.secret_hunter_program.common import ROOT,readlines,write
D=ROOT/'docs/secret_hunter_dgm';reports={}
for tag in ('pilot','v2','adaptive','strong'):
 cs=readlines(D/f'counterfactual-{tag}.jsonl');rows=[]
 for c in cs:
  original=c['alternatives'][0];s=c['observation'];ids={x['entity_id']:x.get('card_id') for side in ('you','opponent') for x in s[side]['board']+s[side].get('hand',[])+[s[side]['hero']]}
  comparisons=[]
  for other in c['alternatives'][1:]:
   delta=[b['win']-a['win'] for a,b in zip(original['outcomes'],other['outcomes'])];rng=random.Random(7)
   boot=sorted(statistics.mean(rng.choices(delta,k=len(delta))) for _ in range(3000))
   comparisons.append({'original_action':original['action'],'alternative':other['action'],'alternative_card':ids.get(other['action'].get('card')),'original_wins':sum(x['win'] for x in original['outcomes']),'alternative_wins':sum(x['win'] for x in other['outcomes']),'samples':len(delta),'conditional_gain':statistics.mean(delta),'descriptive_paired95':[boot[75],boot[2924]],'sample0_original_win':original['outcomes'][0]['win'],'sample0_alternative_win':other['outcomes'][0]['win']})
  rows.append({'game':c['row']['game'],'source_seed':c['row']['seed'],'seq':s['seq'],'opponent':c['row']['opponent'],'turn':s['turn'],'split':c['split'],'comparisons':comparisons,'first_important_error':'unresolved'})
 reports[tag]={'cases':len(cs),'source_games':len({c['row']['game'] for c in cs}),'all_originals_preserved':all(c['alternatives'][0]['action']==c['original_action'] for c in cs),'cases_with_three_roots':sum(len(c['alternatives'])==3 for c in cs),'originals_unsupported_by_fast_model':sum(not c['alternatives'][0]['fast_model_supported'] for c in cs),'errors':sum(bool(o['error']) for c in cs for a in c['alternatives'] for o in a['outcomes']),'opponents':dict(collections.Counter(c['row']['opponent'] for c in cs)),'stages':dict(collections.Counter(c['stage'] for c in cs)),'details':rows}
reports['scope']={'distinct_source_games':120,'adaptive_cases_revisit_existing_games':True,'adaptive_selection_bias':'Extra samples selected after initial noisy outcomes. Conditional intervals are descriptive, not confirmatory or multiplicity-corrected. Validation diagnostics were inspected and are now development data.','public_scenarios':'No reconstructed unknown-hand belief benchmark; all rollouts condition on source private hands, which are never inputs to policies. No general hidden-hand win guarantee.','first_important_error':'No earliest causal error certified. Unsupported is a coverage label, not an error label.','effect_of_tool_evolution':'V1 had 160 roots/180 maximum; v2 had 180/180, using new C1 trajectories and distinct nonforced roots. Original unsupported actions retained 5/60 then 20/60. The C2 root-local rejection fix is exercised by the Bot2 Juggler/Hounds diagnostic and actual subsequent games.','conditional_rng_range_reserved':[954000,6000]}
write(D/'counterfactual-evidence.json',reports)
print(json.dumps({k:{f:v[f] for f in ('cases','cases_with_three_roots','originals_unsupported_by_fast_model','errors')} for k,v in reports.items() if k!='scope'}))
