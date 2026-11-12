"""Analyze the unopened five-arm diagnostic design without reselecting a challenger."""
import collections,json,random,statistics
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import compare,paired,index
from development.teacher_eval.run import summarize
D=ROOT/'docs/secret_hunter_response';E=ROOT/'experiments'
def path(arm,pop):return E/f'secret-hunter-response-{arm.lower()}-final-{pop}'
def primary_interval(rows):
 seeds=sorted({r['seed'] for r in rows});values=[]
 for seed in seeds:
  groups=collections.defaultdict(list)
  for r in rows:
   if r['seed']==seed:groups[r['group']].append(r['score'])
  values.append(.5*statistics.mean(groups['astra'])+.5*statistics.mean(groups['bot2']))
 rng=random.Random(20261111);samples=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(10000));return [samples[250],samples[9749]]
def main():
 freeze=json.loads((D/'final-freeze.json').read_text());out={'summaries':{},'paired':{}}
 for pop,arms in [('core',freeze['arms_core']),('guard',freeze['arms_guardrail'])]:
  for arm in arms:
   folder=path(arm,pop);rows=readlines(folder/'results.jsonl');cfg=json.loads((folder/'config.json').read_text());ix=index(rows)
   expected={(o['name'],s,i) for o in cfg['population'] for s in range(cfg['start'],cfg['start']+cfg['seeds']) for i in (1,2)}
   assert ix.keys()==expected and len(rows)==cfg['planned_games'];assert all(r['public_only'] and not r['policy_errors'] for r in rows)
   summary=summarize(rows)
   if pop=='core':summary.update(primary=.5*summary['by_group']['astra']['win_rate']+.5*summary['by_group']['bot2']['win_rate'],primary_seed95=primary_interval(rows))
   out['summaries'][arm+'-'+pop]=summary
  pairs=[('Y1',arm) for arm in arms if arm!='Y1']+[('K1','E1')]+([('B3','C3')] if pop=='core' else [])
  for left,right in pairs:
   r=compare(path(left,pop),path(right,pop));ar,br=readlines(path(left,pop)/'results.jsonl'),readlines(path(right,pop)/'results.jsonl')
   r['by_opponent']={n:paired([x for x in ar if x['opponent']==n],[x for x in br if x['opponent']==n]) for n in sorted({x['opponent'] for x in ar})}
   r['by_actual_first']={str(first):paired([{**x,'seat':1} for x in ar if (x['seat']==x['first_player'])==first],[{**x,'seat':1} for x in br if (x['seat']==x['first_player'])==first]) for first in (True,False)}
   assert all(index(ar)[k]['first_player']==index(br)[k]['first_player'] for k in index(ar));out['paired'][left+'-'+right+'-'+pop]=r
 primary=out['paired']['Y1-E1-core']['hard_family_macro'];old=out['paired']['Y1-E1-guard'];p=out['paired']['Y1-E1-core']
 gates={'primary_gain_at_least_one_point':primary['gain']>=.01,'paired_lower_positive':primary['gain_seed_cluster_95'][0]>0,'families_drop_no_more_than_five_points':all(p['by_group'][g]['gain']>=-.05 for g in ('astra','bot2')),'old_overall_drop_no_more_than_three_points':old['all']['gain']>=-.03,'old_per_opponent_drop_no_more_than_ten_points':all(v['gain']>=-.10000001 for v in old['by_opponent'].values())}
 write(D/'final-results.json',out);write(D/'decision.json',{'challenger':'E1','gates':gates,'performance_pass':all(gates.values()),'reliability':'pending extracted artifact audit','promotion':'pending reliability' if all(gates.values()) else 'not_promoted','recommendation':'Retain Y1 research baseline unless all performance and reliability gates pass. Existing H7 champion pointer is preserved.','no_final_driven_strategy_change':True,'diagnostic_arms_not_eligible_for_posthoc_promotion':['B3','C3'],'primary_vs_Y1':primary,'primary_vs_K1':out['paired']['K1-E1-core']['hard_family_macro'],'response_vs_no_response':out['paired']['B3-C3-core']['hard_family_macro'],'scope':'Frozen course proxy pool, not real Astra or official course evaluation.'})
 print(json.dumps(json.loads((D/'decision.json').read_text()),indent=2))
if __name__=='__main__':main()
