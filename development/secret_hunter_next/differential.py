"""Recorded development prefixes and short official-engine action branches."""
import copy,json,sys
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_next.accounting import reserve,finish
sys.path.insert(0,str(ROOT/'development/secret_hunter_next/candidates/M1/scripts'))
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
import tactical_model as m
from action_validator import legal
from public_response import prepare_reply,attack,attacks

def project(s):
 out={}
 for key in ('you','opponent'):
  x=s[key];out[key]={'hero':[x['hero']['health'],x['hero'].get('armor',0)],'board':[[z['card_id'],z['attack'],z['health'],bool(z.get('taunt')),bool(z.get('divine_shield')),bool(z.get('frozen')),bool(z.get('stealth'))] for z in x['board']],'secrets':[z['card_id'] for z in x.get('secrets',[])],'weapon':[(x.get('weapon') or {}).get(z) for z in ('card_id','attack','durability')]}
 return out

def main():
 reserve('development-differential',full=40,short=1200)
 src=ROOT/'experiments/secret-hunter-next-d1-screen';specs={x['name']:x for x in json.loads((src/'config.json').read_text())['population']};cases=[];prefixes=0;terminal=0
 rows=sorted(readlines(src/'results.jsonl'),key=lambda r:(r['score'],r['opponent'],r['seed'],r['seat']))[:16]
 for row in rows:
  seat=row['seat'];own=load_deck(ROOT/'development/secret_hunter_next/candidates/M1/deck.json');other=load_deck(ROOT/specs[row['opponent']]['deck']);e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'])
  obs={i:readlines(src/'games'/row['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};selected=0
  while not e.over and selected<10:
   who,_=e.pending();z=obs[who][idx[who]];s=z['state']
   if s.get('turn',0)>16:break
   if who==seat and s['phase']=='main' and m.supported(s) and s.get('turn',0)>=4:
    initial=m.prepare({**s,'planning_mode':'response'});options=[z['action']]+list(m.options(initial))[:6];seen=set()
    for a in options:
     if a['type']=='end_turn' or json.dumps(a,sort_keys=True) in seen or not legal(s,a):continue
     seen.add(json.dumps(a,sort_keys=True));pred=m.transition(initial,a)
     if pred is None:continue
     if min(pred[k]['hero']['health'] for k in ('you','opponent'))<=0:continue
     b=copy.deepcopy(e);ok=b.step(who,a).accepted;terminal+=int(b.over);l,r=project(pred),project(b.view(seat))
     cases.append({'game':row['game'],'seq':s['seq'],'kind':'action','action':a,'equal':ok and l==r,'predicted':l if l!=r else None,'actual':r if l!=r else None})
    if z['action']['type']=='end_turn':
     pred=prepare_reply(initial);b=copy.deepcopy(e);b.step(who,z['action'])
     if b.over:terminal+=1
     elif pred is not None:
      for a in list(attacks(pred))[:3]:
       rpred=attack(pred,a)
       if rpred is None or min(rpred[k]['hero']['health'] for k in ('you','opponent'))<=0:continue
       branch=copy.deepcopy(b);ok=branch.step(3-seat,a).accepted;terminal+=int(branch.over);l,r=project(rpred),project(branch.view(seat))
       cases.append({'game':row['game'],'seq':s['seq'],'kind':'reply','action':a,'equal':ok and l==r,'predicted':l if l!=r else None,'actual':r if l!=r else None})
    selected+=1
   # Stop prefixes before a known final action; terminal counterfactuals charged separately.
   if idx[who]+1==len(obs[who]) and z['state'].get('phase')=='game_over':break
   assert e.step(who,z['action']).accepted;terminal+=int(e.over);idx[who]+=1;prefixes+=1
 report={'n':len(cases),'matches':sum(c['equal'] for c in cases),'terminal_attempts':terminal,'prefix_actions':prefixes,'cases':cases}
 write(ROOT/'docs/secret_hunter_next/development-differential.json',report);finish('development-differential',actual_short=len(cases),actual_full=terminal)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'}));print(json.dumps([c for c in cases if not c['equal']])[:10000])
if __name__=='__main__':main()
