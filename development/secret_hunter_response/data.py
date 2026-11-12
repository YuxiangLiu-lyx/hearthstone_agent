"""Extract next-turn public response labels without reading the opponent's observation."""
import collections, json
from development.secret_hunter_program.common import ROOT, readlines, write, sha
from hs_arena.cards import load
D=ROOT/'docs/secret_hunter_response'; C=load()
LABELS=('develop','buff','taunt','removal','burn','visible_trade')
BUFF={'CS2_188','EX1_046','EX1_162','CS2_122','CS2_087','CS2_092','EX1_093','EX1_058','CS2_045','EX1_316','DS1_070','EX1_019'}
def labels(events,seat,hero_id):
 y=dict.fromkeys(LABELS,0);op=3-seat;active=False;context=None
 for e in events:
  if e['event']=='turn_start':
   if e['player']==seat:break
   active=True
  if not active:continue
  kind=e['event']
  if kind in ('play_card','attack','hero_power','end_turn'):context=e
  if kind=='play_card' and e['player']==op:
   cid=e.get('card_id');c=C.get(cid,{})
   y['develop']|=int(c.get('type')=='MINION' or cid in {'EX1_538','CS2_027','CS2_022'})
   y['buff']|=int(cid in BUFF and (e.get('target') is not None or cid in {'EX1_162','CS2_122','EX1_093','EX1_058'}))
   y['taunt']|=int('TAUNT' in c.get('mechanics',[]) or cid in {'EX1_093','EX1_058','DS1_070'})
  if kind=='attack' and e['player']==op:y['visible_trade']|=int((e.get('target') or {}).get('entity_id')!=hero_id)
  if kind=='damage' and e.get('player')==seat and e.get('amount',0)>0 and context and context['event']!='attack':
   if context.get('player')==op:
    y['burn' if e.get('entity_id')==hero_id else 'removal']=1
 return y

def public_features(s):
 y,o=s['you'],s['opponent'];e=s.get('public_opponent_evidence',{})
 return {'hero_class':o['hero']['hero_class'],'mana':max(0,min(10,o['max_mana']+1)-o.get('overload_next_turn',0)),
  'turn':s['turn'],'hand_size':o['hand_size'],'own_hand_size':len(y['hand']),
  'own_board':[{k:m.get(k) for k in ('card_id','attack','health','taunt','divine_shield')} for m in y['board']],
  'enemy_board':[{k:m.get(k) for k in ('card_id','attack','health','taunt','divine_shield')} for m in o['board']],
  'own_health':y['hero']['health']+y['hero'].get('armor',0),'enemy_health':o['hero']['health']+o['hero'].get('armor',0),
  'enemy_weapon':(o.get('weapon') or {}).get('attack',0),'own_weapon':(y.get('weapon') or {}).get('attack',0),
  'own_secrets':[c['card_id'] for c in y['secrets']], 'shown_cards':e.get('shown_cards',[]),
  'cheap_minions_played':e.get('cheap_minions_played',0),'face_attacks':e.get('face_attacks',0),'other_attacks':e.get('other_attacks',0)}
def main():
 src=ROOT/'experiments/secret-hunter-response-y1-response-data';rows=readlines(src/'results.jsonl');out=[];starts=[];gaps=[]
 for r in rows:
  obs=readlines(src/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl');seen_turns=set();own_turn=0
  for i,z in enumerate(obs):
   s=z['state']
   if s['phase']!='main':continue
   if s['turn'] not in seen_turns:
    own_turn+=1;seen_turns.add(s['turn'])
    attack_gap=sum(m['attack'] for m in s['opponent']['board'])-sum(m['attack'] for m in s['you']['board'])
    if own_turn==4:gaps.append({'seed':r['seed'],'game':r['game'],'opponent':r['opponent'],'first':r['first_player']==r['seat'],'win':r['score'],'attack_gap':attack_gap,'hand':[c['card_id'] for c in s['you']['hand']]})
    if 2<=own_turn<=4:starts.append({'source':str(src.relative_to(ROOT)),'row':r,'own_turn':own_turn,'observation':s,'original_action':z['action'],'original_plan':[x['action'] for x in obs[i:] if x['state'].get('turn')==s['turn'] and x['state']['phase']=='main']})
   if z['action']['type']!='end_turn':continue
   after=[]
   for zz in obs[i+1:]:
    after.extend(zz['state'].get('events',[]))
    if zz['state'].get('turn',s['turn'])!=s['turn'] or zz['state']['phase']=='game_over':break
   if not any(e['event']=='turn_start' and e['player']!=r['seat'] for e in after):continue
   out.append({'audit':{'seed':r['seed'],'game':r['game'],'opponent':r['opponent'],'seat':r['seat'],'first':r['first_player']==r['seat'],'win':r['score'],'seq':s['seq'],'own_turn':own_turn},'features':public_features(s),'labels':labels(after,r['seat'],s['you']['hero']['entity_id']),'public_events':after})
 with (D/'opponent_replies.jsonl').open('w') as f:
  for r in out:f.write(json.dumps(r,separators=(',',':'))+'\n')
 write(D/'turn-starts.json',starts)
 write(D/'turn4-inventory.json',gaps)
 stats={'games':len(rows),'responses':len(out),'seed_groups':len({r['audit']['seed'] for r in out}),'labels':{k:sum(r['labels'][k] for r in out) for k in LABELS},'by_split':dict(collections.Counter('test' if r['audit']['seed']%5==0 else 'calibration' if r['audit']['seed']%5==1 else 'fit' for r in out)),'turn4':{opp:{str(first):{'losses_reached_turn4':sum(not x['win'] for x in gaps if x['opponent']==opp and x['first']==first),'losses_gap4':sum(not x['win'] and x['attack_gap']>=4 for x in gaps if x['opponent']==opp and x['first']==first)} for first in (True,False)} for opp in sorted({x['opponent'] for x in gaps})}}
 historical=['counterfactual-pilot','counterfactual-v2','counterfactual-adaptive','counterfactual-strong']
 write(D/'data-manifest.json',{'requested_zip':'Not found in workspace, sibling worktrees, attachments, Downloads or Desktop; no claim of reproducing its 389/480 or 44/57 statistics.','source':str(src.relative_to(ROOT)),'config_sha256':sha(src/'config.json'),'responses_sha256':sha(D/'opponent_replies.jsonl'),'historical_counterfactual':{n:{'path':f'docs/secret_hunter_dgm/{n}.jsonl','sha256':sha(ROOT/f'docs/secret_hunter_dgm/{n}.jsonl'),'cases':len(readlines(ROOT/f'docs/secret_hunter_dgm/{n}.jsonl'))} for n in historical},'stats':stats})
 print(json.dumps(stats))
if __name__=='__main__':main()
