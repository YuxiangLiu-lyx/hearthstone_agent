"""Separate coverage telemetry from causal claims about lost games."""
import collections,json
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
from development.teacher_eval.compare import index
D=ROOT/'docs/secret_hunter_response';E=ROOT/'experiments';out={}
for arm in ('B1','C1','B2','C2','B3','C3','E1'):
 stage='retain' if arm in ('B3','C3','E1') else 'pilot';folder=E/f'secret-hunter-response-{arm.lower()}-{stage}';base=E/f'secret-hunter-response-y1-{stage}'
 a,b=index(readlines(base/'results.jsonl')),index(readlines(folder/'results.jsonl'));counts=collections.Counter();nodes=[];elapsed=[];differences=[]
 for key,r in b.items():
  zs=readlines(folder/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl')
  for z in zs:
   q=z.get('info',{}).get('response',{})
   if q.get('reason'):counts[q['reason']]+=1
   if 'generated_endpoints' in q:counts['endpoint_searches']+=1
   if q.get('candidates'):nodes.append(q['nodes']);elapsed.append(q['elapsed_s'])
   if q.get('hypotheses'):counts['with_hypotheses']+=1
  if a[key]['score']==r['score']:continue
  old=readlines(base/'games'/a[key]['game']/f"p{r['seat']}"/'observations.jsonl')
  for x,y in zip(old,zs):
   if x['action']==y['action']:continue
   same=all(x['state'].get(k)==y['state'].get(k) for k in ('turn','you','opponent','legal_actions'))
   q=y.get('info',{}).get('response',{});basepaths=[v['path'] for v in q.get('candidates',[]) if v['path'][0]==x['action']]
   coin=next((c['card_id'] for c in x['state'].get('you',{}).get('hand',[]) if c['entity_id']==x['action'].get('card')),None)=='GAME_005'
   generation_gap=bool(coin and basepaths and len(basepaths[0])==2)
   differences.append({'pair':key,'baseline_win':a[key]['score'],'candidate_win':r['score'],'seq':x['state']['seq'],'same_public_state':same,'baseline_action':x['action'],'candidate_action':y['action'],'baseline_coin_without_followup_in_comparison':generation_gap,'candidate_root_was_generated':any(v['path'][0]==y['action'] for v in q.get('candidates',[])),'classification':'baseline_plan_generation_gap' if generation_gap else 'evaluation_or_continuation_unresolved','causal_status':'First policy divergence, not a certified first important error.'});break
 out[arm]={'stage':stage,'telemetry':dict(counts),'nodes':quantiles(nodes) if nodes else None,'response_elapsed_s':quantiles(elapsed) if elapsed else None,'discordant_games':differences,'baseline_only':sum(x['baseline_win'] for x in differences),'candidate_only':sum(x['candidate_win'] for x in differences),'classification_counts':dict(collections.Counter(x['classification'] for x in differences if x['baseline_win']))}
write(D/'failure-diagnostics.json',out);print(json.dumps({k:{'baseline_only':v['baseline_only'],'candidate_only':v['candidate_only'],'classifications':v['classification_counts']} for k,v in out.items()}))
