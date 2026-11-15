"""Natural-frequency public witnesses for the one permitted card-slot test."""
import collections,json,time
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.study import RUN

def main():
 db=ledger.connect(RUN);counts=collections.defaultdict(collections.Counter);cases=[]
 for batch in ('diagnostic-dev','round1-recall'):
  for row in db.execute("select result from tasks where batch=? and candidate='DARCL2' and status='done'",(batch,)):
   r=json.loads(row[0]);assert 62150000<=r['seed']<62160000
   if r['group']!='astra':continue
   c=counts[r['opponent']];c['all_games']+=1;c['losses']+=not r['score'];folder=RUN/'batches'/batch/'DARCL2'/'games'/r['game']
   logs=[json.loads(z) for z in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()];hits={}
   for z in logs:
    s=z['state']
    if s['phase']!='main' or not 2<=s['you']['max_mana']<=5:continue
    y,o=s['you'],s['opponent'];deadly=next((x for x in y['hand'] if x['card_id']=='EX1_617'),None)
    if not deadly:continue
    hits.setdefault('deadly_in_early_hand',z)
    weak=[m for m in o['board'] if m['health']<=2 and not any(m.get(f) for f in ('divine_shield','immune','stealth')) and m['attack']>=2]
    keys=[m for m in weak if m['card_id'] in ('EX1_162','NEW1_019','EX1_319')]
    if weak and y['mana']>=1:hits.setdefault('cheap_clear_public_target',z)
    if keys and len(o['board'])>1 and y['mana']>=1:hits.setdefault('cheap_precise_key_clear',z)
    if weak and any(x.get('type')=='MINION' and x['cost']+1<=y['mana']<x['cost']+3 for x in y['hand']) and len(y['board'])<7:
     hits.setdefault('clear_plus_body_instead_of_deadly_only',z)
   for k,z in hits.items():
    c[k]+=1;c[k+'_losses']+=not r['score']
    if k in ('cheap_precise_key_clear','clear_plus_body_instead_of_deadly_only'):
     cases.append({'batch':batch,'seed':r['seed'],'seat':r['seat'],'opponent':r['opponent'],'win':r['score'],'pattern':k,'witness':z})
 result={'created':time.time(),'counts':{k:dict(v) for k,v in counts.items()},'cases':cases,
  'scope':'Public opportunity witnesses from unscreened seen games, not counterfactual wins. Arcane Shot does not kill healthy Voidwalkers/Amani or larger bodies; loss of hard removal must be checked in paired full games and guardrails.'}
 ledger.atomic(RUN/'single-slot-diagnosis.json',result)
 print(json.dumps({'counts':result['counts'],'loss_source_seeds':len({c['seed'] for c in cases if not c['win']}),'examples':[(c['seed'],c['opponent'],c['seat'],c['pattern']) for c in cases if not c['win']][:12]},indent=2))
if __name__=='__main__':main()
