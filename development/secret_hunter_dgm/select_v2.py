"""Increase feedback yield: nonforced, distinct tactical roots from new trajectories."""
import collections,json,sys,time
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_dgm.accounting import reserve,finish
D=ROOT/'docs/secret_hunter_dgm';src=ROOT/'experiments/secret-hunter-dgm-c1-screen'
sys.path.insert(0,str(ROOT/'development/secret_hunter_dgm/candidates/C1/scripts'))
from secret_policy import rank
from action_validator import legal
reserve('select-v2',short=6000)
options=[];examined=0
for row in sorted(readlines(src/'results.jsonl'),key=lambda r:(r['opponent'],r['seed'],r['seat'])):
 bystage=collections.defaultdict(list)
 for z in readlines(src/'games'/row['game']/f'p{row["seat"]}'/'observations.jsonl'):
  s=z['state']
  if s['phase']!='main':continue
  examined+=1
  ranked=rank(s,json.loads((ROOT/'development/secret_hunter_dgm/candidates/C1/config.json').read_text()),time.monotonic()+.1)
  def key(a):return tuple((k,v) for k,v in sorted(a.items()) if k!='position')
  roots={key(a) for _,a in ranked if legal(s,a)}
  if len(roots)<3:continue
  stage='early' if s['turn']<=5 else 'mid' if s['turn']<=11 else 'late'
  cards=s['you']['board']+s['you']['hand'];ids={c['card_id'] for c in cards};tags=[]
  if 'NEW1_019' in ids:tags.append('juggler')
  if 'NEW1_031' in ids:tags.append('companion')
  if 'EX1_543' in ids:tags.append('krush')
  if any(c['card_id']=='EX1_533' for c in s['you'].get('secrets',[])):tags.append('misdirection')
  c={'source':str(src.relative_to(ROOT)),'row':row,'observation':s,'original_action':z['action'],'source_info':z['info'],'tags':tags,'stage':stage,'first':row['seat']==row['first_player'],'split':'validation' if row['seed']%3==2 else 'train','distinct_roots':len(roots),'tool_version':'v2-diverse-nonforced-new-trajectory'}
  bystage[stage].append(c)
 desired=('early','mid','late')[(row['seed']+row['seat'])%3]
 cs=bystage.get(desired) or [c for cs in bystage.values() for c in cs]
 if cs:options.append(max(cs,key=lambda c:(len(c['tags']),min(8,c['distinct_roots']),-c['observation']['seq'])))
buckets=collections.defaultdict(list)
for c in options:buckets[(c['row']['opponent'],c['row']['score'],c['first'])].append(c)
selected=[]
while len(selected)<60 and any(buckets.values()):
 for k in sorted(buckets):
  if buckets[k] and len(selected)<60:selected.append(buckets[k].pop(0))
write(D/'counterfactual-selection-v2.json',selected)
summary={'eligible_games':len(options),'selected':len(selected),'examined':examined,'opponents':dict(collections.Counter(c['row']['opponent'] for c in selected)),'stages':dict(collections.Counter(c['stage'] for c in selected)),'losses':sum(not c['row']['score'] for c in selected),'expected_root_comparison_fraction':1.0,'v1_actual_roots':160,'v1_max_roots':180,'split_unit':'Entire source seed cluster; no final seeds touched'}
write(D/'selection-v2-summary.json',summary);finish('select-v2',actual_short=examined);print(json.dumps(summary))
