"""One unopened matched confirmation, whole-seed paired bootstrap and fixed gates."""
import collections,json,random,statistics
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import compare,paired,index
from development.teacher_eval.run import summarize
D=ROOT/'docs/secret_hunter_dgm';E=ROOT/'experiments';freeze=json.loads((D/'final-freeze.json').read_text());challenger=freeze['challenger'];arms=['K0','K1',challenger]
def path(arm,pop):return E/f'secret-hunter-dgm-{arm.lower()}-final-{pop}'
def primary_interval(rows):
 seeds=sorted({r['seed'] for r in rows});values=[]
 for seed in seeds:
  bygroup=collections.defaultdict(list)
  for r in rows:
   if r['seed']==seed:bygroup[r['group']].append(r['score'])
  values.append(.5*statistics.mean(bygroup['astra'])+.5*statistics.mean(bygroup['bot2']))
 rng=random.Random(20261111);samples=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(10000))
 return [samples[250],samples[9749]]
result={'summaries':{},'paired':{}}
for pop in ('core','guard'):
 for arm in arms:
  p=path(arm,pop);rows=readlines(p/'results.jsonl');cfg=json.loads((p/'config.json').read_text());ix=index(rows)
  expected={(o['name'],s,i) for o in cfg['population'] for s in range(cfg['start'],cfg['start']+cfg['seeds']) for i in (1,2)}
  assert ix.keys()==expected and len(rows)==cfg['planned_games']
  assert all(r['first_player'] in (1,2) and r['public_only'] for r in rows)
  s=summarize(rows)
  if pop=='core':s.update(primary=.5*s['by_group']['astra']['win_rate']+.5*s['by_group']['bot2']['win_rate'],primary_seed95=primary_interval(rows))
  result['summaries'][arm+'-'+pop]=s
 for base in ('K0','K1'):
  a,b=path(base,pop),path(challenger,pop);r=compare(a,b);ar,br=readlines(a/'results.jsonl'),readlines(b/'results.jsonl')
  r['by_opponent']={n:paired([x for x in ar if x['opponent']==n],[x for x in br if x['opponent']==n]) for n in sorted({x['opponent'] for x in ar})}
  r['actual_first_player_matches']=all(index(ar)[k]['first_player']==index(br)[k]['first_player'] for k in index(ar))
  result['paired'][base+'-'+pop]=r
primary=result['paired']['K0-core']['hard_family_macro'];old=result['paired']['K0-guard']
gates={'primary_gain_at_least_one_point':primary['gain']>=.01,'primary_paired_lower_positive':primary['gain_seed_cluster_95'][0]>0,'families_no_drop_over_five_points':all(result['paired']['K0-core']['by_group'][g]['gain']>=-.05 for g in ('astra','bot2')),'old_pool_overall_no_drop_over_three_points':old['all']['gain']>=-.03,'old_pool_each_no_drop_over_ten_points':all(v['gain']>=-.10000001 for v in old['by_opponent'].values())}
write(D/'final-results.json',result)
write(D/'decision.json',{'candidate':challenger,'performance_gates_pass':all(gates.values()),'gates':gates,'primary_vs_K0':primary,'primary_vs_K1':result['paired']['K1-core']['hard_family_macro'],'guardrail_vs_K0':old['all'],'promotion':'pending_reliability' if all(gates.values()) else 'not_promoted','release_zip':freeze['zip'],'no_final_driven_policy_change':True,'no_additional_confirmation':True,'official_submission':False,'scope':'Original 30-card Krush/Misdirection deck; fixed proxies, not real Astra. Old D1/C2 results excluded.'})
print(json.dumps(json.loads((D/'decision.json').read_text()),indent=2))
