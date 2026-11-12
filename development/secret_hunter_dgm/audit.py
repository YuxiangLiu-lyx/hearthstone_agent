"""Stratify public decisions without dropping unsupported original actions."""
import collections,json
from development.secret_hunter_program.common import ROOT,readlines,write
D=ROOT/'docs/secret_hunter_dgm'
def main():
 result={};cases=[]
 for name in ('k0-pilot','k1-pilot','c0-pilot'):
  folder=ROOT/'experiments'/('secret-hunter-dgm-'+name)
  if not (folder/'summary.json').exists():continue
  counts=collections.Counter();examples=collections.defaultdict(list);mull=[]
  for r in sorted(readlines(folder/'results.jsonl'),key=lambda r:(r['opponent'],r['seed'],r['seat'])):
   for z in readlines(folder/'games'/r['game']/f'p{r["seat"]}'/'observations.jsonl'):
    s=z['state'];info=z.get('info',{});y=s.get('you',{});o=s.get('opponent',{})
    if s['phase']=='mulligan':mull.append({'opponent':r['opponent'],'win':r['score'],'first':r['first_player']==r['seat'],'hand':[c['card_id'] for c in y['hand']],'action':z['action']})
    if s['phase']!='main':continue
    counts['main']+=1
    tags=[]
    if any(c['card_id']=='EX1_543' for c in y['hand']):tags.append('krush_in_hand')
    if any(c['card_id']=='EX1_543' and c['cost']<=min(10,y['max_mana']+1) for c in y['hand']):tags.append('krush_next_mana')
    if any(c['card_id']=='NEW1_031' and c['cost']<=y['mana'] for c in y['hand']) and not any(m['card_id']=='NEW1_019' for m in y['board']):tags.append('companion_without_juggler')
    if any(c['card_id']=='EX1_533' for c in y.get('secrets',[])):tags.append('misdirection_active')
    if any(c['card_id']=='NEW1_019' for c in y['board']):tags.append('juggler_active')
    for key in ('turn_search','chance'):
     q=info.get(key,{})
     if q.get('reason'):tags.append(key+':'+q['reason'])
    for t in tags:
     counts[t]+=1
     if len(examples[t])<4:examples[t].append({'game':r['game'],'seed':r['seed'],'opponent':r['opponent'],'win':r['score'],'seq':s['seq'],'turn':s['turn'],'action':z['action']})
    if name=='k1-pilot':cases.append({'source':str(folder.relative_to(ROOT)),'row':r,'observation':s,'original_action':z['action'],'source_info':info,'tags':tags,'stage':'early' if s['turn']<=5 else 'mid' if s['turn']<=11 else 'late','first':r['first_player']==r['seat'],'split':'validation' if r['seed']%3==2 else 'train'})
  result[name]={'counts':dict(counts),'examples':dict(examples),'mulligans':mull}
 write(D/'pilot-audit.json',result)
 # One state per source game, balanced opponent/seat and rotating stage/boundary.
 selected=[];seen=set();groups=collections.defaultdict(list)
 for c in cases:groups[c['row']['game']].append(c)
 games=sorted(groups,key=lambda g:(groups[g][0]['row']['opponent'],groups[g][0]['row']['seed'],groups[g][0]['row']['seat']))
 buckets=collections.defaultdict(list)
 for g in games:
  cs=groups[g];r=cs[0]['row'];desired=('early','mid','late')[(r['seed']+r['seat'])%3]
  preferred=[c for c in cs if c['stage']==desired] or cs
  boundary=[c for c in preferred if any(t in c['tags'] for t in ('juggler_active','companion_without_juggler','krush_next_mana','misdirection_active'))]
  chosen=(boundary or preferred)[len(boundary or preferred)//2]
  buckets[(r['opponent'],r['score'],chosen['first'])].append(chosen)
 while len(selected)<60 and any(buckets.values()):
  for k in sorted(buckets):
   if buckets[k] and len(selected)<60:selected.append(buckets[k].pop(0))
 write(D/'counterfactual-selection.json',selected)
 print(json.dumps({k:v['counts'] for k,v in result.items()},indent=2))
 print('selected',len(selected),'stages',dict(collections.Counter(c['stage'] for c in selected)),'opponents',dict(collections.Counter(c['row']['opponent'] for c in selected)))
if __name__=='__main__':main()
