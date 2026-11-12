"""Summarize complete-plan evidence with source-seed-cluster uncertainty."""
import collections,json,random,statistics
from development.secret_hunter_program.common import ROOT,readlines,write
D=ROOT/'docs/secret_hunter_response';rows=readlines(D/'counterfactual-balanced.jsonl');groups=collections.defaultdict(list);stats=collections.Counter();examples=[]
for r in rows:
 base=r['plans'][0];chosen=next(p for p in r['plans'] if p['id']==r['selected_on_selection_only']);wins=lambda p:sum(o['win'] for o in p['outcomes'] if o['split']=='validation')
 groups[r['case']['row']['seed']].append((wins(base),wins(chosen),5));stats['baseline_wins']+=wins(base);stats['selected_wins']+=wins(chosen);stats['changed']+=chosen['id']!='Y1';stats['shared_first_action']+=len({json.dumps(p['actions'][0],sort_keys=True) for p in r['plans']})<len(r['plans']);stats['errors']+=sum(bool(o['error']) for p in r['plans'] for o in p['outcomes'])
 stats['actual_original_win']+=r['case']['row']['score'];stats['actual_first']+=r['case']['row']['seat']==r['case']['row']['first_player']
 seeds=list(groups);rng=random.Random(171);draws=[]
for _ in range(10000):
 pairs=[x for s in rng.choices(seeds,k=len(seeds)) for x in groups[s]];draws.append(sum(b-a for a,b,n in pairs)/sum(n for a,b,n in pairs))
draws.sort();extended=[]
for r in readlines(D/'counterfactual-extended.jsonl'):
 base,alt=r['plans'];pairs=list(zip(base['outcomes'],alt['outcomes']));delta=[b['win']-a['win'] for a,b in pairs];samples=sorted(statistics.mean(rng.choices(delta,k=len(delta))) for _ in range(10000))
 extended.append({'case_id':r['case_id'],'seed':r['case']['row']['seed'],'opponent':r['case']['row']['opponent'],'seat':r['case']['row']['seat'],'seq':r['case']['observation']['seq'],'own_turn':r['case']['own_turn'],'source_win':r['case']['row']['score'],'Y1_wins':sum(o['win'] for o in base['outcomes']),'alternative_wins':sum(o['win'] for o in alt['outcomes']),'n_each':20,'paired_future_95_descriptive':[samples[250],samples[9749]],'original_plan':base['actions'],'alternative_plan':alt['actions'],'caveat':'Single conditional source position selected adaptively; interval is not an out-of-sample strategy effect.'})
report={'cases':len(rows),'future_validation_per_plan':5,'source_seed_groups':len(groups),**stats,'selected_minus_Y1':(stats['selected_wins']-stats['baseline_wins'])/(len(rows)*5),'paired_source_seed_95':[draws[250],draws[9749]],'by_opponent':dict(collections.Counter(r['case']['row']['opponent'] for r in rows)),'by_own_turn':dict(collections.Counter(r['case']['own_turn'] for r in rows)),'extended_cases':extended,'evidence_gap':'No statistically secure general strategy gain. Positive local examples remain conditional, selection-sensitive and continuation-dependent. The harm example is substantially clearer.'}
write(D/'counterfactual-analysis.json',report);print(json.dumps({k:v for k,v in report.items() if k!='extended_cases'}))
