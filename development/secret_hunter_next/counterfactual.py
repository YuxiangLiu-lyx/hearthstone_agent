"""Public-policy terminal continuations with explicit conditional-randomness limits."""
import argparse,copy,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_next.accounting import reserve,finish
from development.secret_hunter_next.features import features,NAMES
SRC=ROOT/'experiments/secret-hunter-next-d1-screen';C=ROOT/'development/secret_hunter_next/candidates/M1'

def worker(task):
 row,spec,index=task
 sys.path.insert(0,str(C/'scripts'))
 from hs_arena.engine import Engine
 from hs_arena.deck import load_deck
 from hs_arena.runner import build_state
 from hs_arena.protocol import Config
 from development.secret_hunter_tactics.run import opponent
 from program_policy import decide
 from secret_policy import rank
 from state_features import with_public_history
 from action_validator import legal
 import tactical_model as m
 cfg=json.loads((C/'config.json').read_text());seat=row['seat'];own=load_deck(C/'deck.json');other=load_deck(ROOT/spec['deck'])
 e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'],max_turns=180)
 obs={i:readlines(SRC/'games'/row['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};cases=[];selected=0
 # One state per game prevents leakage across training and validation.
 while not e.over:
  who,_=e.pending();z=obs[who][idx[who]];s=z['state']
  if s.get('turn',0)>13:break
  if who==seat and s['phase']=='main' and 5<=s['turn']<=12 and len(s['you']['board'])+len(s['opponent']['board'])>=3 and m.supported(s):
   ranking=rank(s,cfg,time.monotonic()+.5);new,info=decide(s,cfg);actions=[];seen=set()
   for a in [z['action'],new]+[a for _,a in ranking]:
    k=json.dumps(a,sort_keys=True)
    if k in seen or not legal(s,a):continue
    seen.add(k)
    endpoint=m.prepare({**s,'planning_mode':'response'}) if a['type']=='end_turn' else m.transition(m.prepare({**s,'planning_mode':'response'}),a)
    if endpoint is None:continue
    actions.append((a,features(endpoint)))
    if len(actions)==3:break
   if len(actions)==3 and any(a['type'] in ('attack','play_card') for a,_ in actions):
    policy=opponent(spec);samples=[]
    for ai,(action,fs) in enumerate(actions):
     outcomes=[]
     for sample in range(6):
      b=copy.deepcopy(e);b.game.random.seed(741000+index*100+sample)
      # Condition on the observed match's existing hands; randomize only unobserved future order.
      for p in b.game.players:b.game.random.shuffle(p.deck)
      trace=[];hist=[ev.view(seat) for ev in b.events if ev.view(seat) is not None];error=None
      try:
       assert b.step(seat,action).accepted
       steps=0
       while not b.over and steps<600:
        p,_=b.pending();public=build_state(b,'counterfactual',p,steps+1,None,Config(max_turns=180))
        if p==seat:
         history=[ev.view(seat) for ev in b.events if ev.view(seat) is not None]
         public=with_public_history(public,history);a,inf=decide(public,cfg)
         assert legal(public,a) and not inf.get('error')
        else:a=policy.fn(public)
        assert b.step(p,a).accepted;steps+=1
       if not b.over:error='continuation_limit'
      except Exception:error=traceback.format_exc()
      outcomes.append({'sample':sample,'win':int(b.over and b.winner==seat),'terminal':b.over,'reason':b.reason,'steps':steps,'error':error})
     samples.append({'action':action,'features':fs,'outcomes':outcomes,'win_rate':sum(x['win'] for x in outcomes)/6})
    return {'game':row['game'],'source_seed':row['seed'],'source_opponent':row['opponent'],'source_score':row['score'],'seq':s['seq'],'turn':s['turn'],'observation':s,'original_action':z['action'],'candidate_policy_action':new,'alternatives':samples,'split':'validation' if index%4==3 else 'train','continuation':'frozen M1 for own policy; frozen original opponent; full engine terminal rollouts','randomness':'Six future RNG/deck-order samples shared across alternatives. Existing private hands remain conditioned on the source match, never passed to a policy. Action divergence changes subsequent RNG consumption; samples are not identical draws.'}
  # Avoid completing the source game; its replay prefix is a diagnostic, not a rollout.
  if idx[who]+2>=len(obs[who]):break
  assert e.step(who,z['action']).accepted;idx[who]+=1
 return {'game':row['game'],'skipped':'no early supported three-action state'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--name',default='counterfactual-v2');parser.add_argument('--limit',type=int,default=24);args=parser.parse_args()
 rows=readlines(SRC/'results.jsonl');specs={s['name']:s for s in json.loads((SRC/'config.json').read_text())['population']}
 losses=sorted([r for r in rows if not r['score']],key=lambda r:(r['opponent'],r['seed'],r['seat']));wins=sorted([r for r in rows if r['score']],key=lambda r:(r['opponent'],r['seed'],r['seat']))
 selected=(losses[:16]+wins[:8])[:args.limit];reserve(args.name,full=len(selected)*18,short=1000)
 dest=ROOT/'docs/secret_hunter_next'/f'{args.name}.jsonl';out=[]
 with ProcessPoolExecutor(max_workers=6) as pool,dest.open('w') as f:
  fs=[pool.submit(worker,(r,specs[r['opponent']],i)) for i,r in enumerate(selected)]
  for future in as_completed(fs):
   result=future.result();out.append(result);f.write(json.dumps(result)+'\n');f.flush();print('cases',len(out),len(selected),flush=True)
 actual=sum(len(a['outcomes']) for c in out for a in c.get('alternatives',[]));finish(args.name,actual_full=actual,cases=len(out),errors=sum(bool(o['error']) for c in out for a in c.get('alternatives',[]) for o in a['outcomes']))
 print(json.dumps({'cases':len(out),'full_rollouts':actual,'skipped':sum('skipped' in x for x in out)}))
if __name__=='__main__':main()
