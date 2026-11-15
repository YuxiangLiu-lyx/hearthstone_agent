"""Natural frequency of observable enemy draw transfers in seen full games."""
import collections,json,time
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger

def main():
 db=ledger.connect(RUN);counts=collections.defaultdict(collections.Counter);cases=[];population_sources=set()
 for batch in ('diagnostic-dev','round1-recall'):
  for q in db.execute("select result from tasks where batch=? and candidate='DARCL2' and status='done'",(batch,)):
   r=json.loads(q[0]);assert 62150000<=r['seed']<62160000
   if r['group']!='astra':continue
   population_sources.add(r['seed'])
   c=counts[r['opponent']];c['all_games']+=1;c['losses']+=not r['score'];folder=RUN/'batches'/batch/'DARCL2'/'games'/r['game'];logs=[json.loads(l) for l in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()];hits=[]
   for a,b in zip(logs,logs[1:]):
    s,t=a['state'],b['state']
    if s['phase']!='main' or t['phase']!='main' or s['turn']!=t['turn'] or not 2<=s['you']['max_mana']<=5:continue
    increase=t['opponent']['hand_size']-s['opponent']['hand_size']
    if increase<=0:continue
    alive={m['entity_id'] for m in t['opponent']['board']}
    dead=[m for m in s['opponent']['board'] if m['entity_id'] not in alive and m['card_id'] in ('EX1_096','EX1_012') and not m.get('silenced')]
    if not dead:continue
    hits.append({'seq':s['seq'],'T':s['you']['max_mana'],'hand_increase':increase,'draw_minions':[m['card_id'] for m in dead],'action':a['action'],'same_turn_successor_verified':True})
   c['early_draw_transfer_games']+=bool(hits);c['early_draw_transfer_original_losses']+=bool(hits) and not r['score'];c['early_draw_transfer_decisions']+=len(hits)
   if hits:cases.append({'batch':batch,'seed':r['seed'],'seat':r['seat'],'opponent':r['opponent'],'win':r['score'],'hits':hits})
 result={'created':time.time(),'counts':{k:dict(v) for k,v in counts.items()},'population_source_seeds':len(population_sources),'affected_source_seeds':len({r['seed'] for r in cases}),'cases':cases,'scope':'Unscreened seen 600-game Astra population. Counts observed T2-T5 deaths and public hand-size transfer during our own turn, not counterfactual opportunities or causal win gains. Transfers during opponent turns and terminal actions without a successor are excluded.'}
 ledger.atomic(RUN/'H4-natural-frequency.json',result);print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
