"""Official-engine conditional diagnosis retaining original roots and full turn traces."""
import argparse,copy,json,subprocess,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_dgm.accounting import reserve,finish
from development.secret_hunter_dgm.deck_guard import check
D=ROOT/'docs/secret_hunter_dgm'; C=ROOT/'development/secret_hunter_dgm/candidates/K1'
def worker(task):
 case,index,samples,proposal,continuation,diverse=task;C=ROOT/continuation;row=case['row'];seat=row['seat'];src=ROOT/case['source']
 sys.path.insert(0,str(C/'scripts'))
 from program_policy import decide
 from secret_policy import rank
 from state_features import with_public_history
 from action_validator import legal
 import tactical_model as m
 from hs_arena.engine import Engine
 from hs_arena.deck import load_deck
 from hs_arena.runner import build_state
 from hs_arena.protocol import Config
 from development.secret_hunter_tactics.run import opponent
 specs=json.loads((src/'config.json').read_text())['population'];spec=next(s for s in specs if s['name']==row['opponent'])
 own=load_deck(C/'deck.json');other=load_deck(ROOT/spec['deck']);cfg=json.loads((C/'config.json').read_text());s=case['observation']
 e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'],max_turns=180)
 obs={i:readlines(src/'games'/row['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};prefix=0
 while True:
  who,_=e.pending();z=obs[who][idx[who]]
  if who==seat and z['state']['seq']==s['seq']:break
  assert e.step(who,z['action']).accepted and not e.over;idx[who]+=1;prefix+=1
 assert e.view(seat)['you']['hand']==s['you']['hand']
 candidates=[case['original_action']]
 code='import sys,json;from pathlib import Path;p=Path(sys.argv[1]);sys.path.insert(0,str(p/"scripts"));from program_policy import decide;s=json.load(sys.stdin);print(json.dumps(decide(s,json.loads((p/"config.json").read_text()))[0]))'
 proposed=json.loads(subprocess.check_output([sys.executable,'-c',code,str(ROOT/proposal)],input=json.dumps(s),text=True))
 for a in [proposed]+[a for _,a in rank(s,cfg,time.monotonic()+1)]:
  key=lambda x:{k:v for k,v in x.items() if k!='position'}
  distinct=all(key(a)!=key(old) for old in candidates) if diverse else a not in candidates
  if legal(s,a) and distinct:candidates.append(a)
  if len(candidates)==3:break
 policy=opponent(spec);alternatives=[]
 for action in candidates:
  predicted=m.transition(m.prepare({**s,'planning_mode':'proof'}),action) if action['type']!='end_turn' else m.prepare(s)
  outcomes=[]
  for sample in range(samples):
   b=copy.deepcopy(e)
   if sample:
    b.game.random.seed(954000+index*100+sample)
    for p in b.game.players:b.game.random.shuffle(p.deck)
   steps=0;error=None;turn_trace=[action];start_turn=b.view(seat)['turn'];turn_closed=False
   try:
    assert b.step(seat,action).accepted
    while not b.over and steps<600:
     p,_=b.pending();public=build_state(b,'conditional-krush',p,steps+1,None,Config(max_turns=180))
     if p==seat:
      history=[ev.view(seat) for ev in b.events if ev.view(seat) is not None]
      a,info=decide(with_public_history(public,history),cfg)
      assert legal(public,a) and not info.get('error')
      if not turn_closed and public['turn']==start_turn:turn_trace.append(a)
     else:a=policy.fn(public);turn_closed=True
     assert b.step(p,a).accepted;steps+=1
    if not b.over:error='continuation_limit'
   except Exception:error=traceback.format_exc()
   outcomes.append({'sample':sample,'unchanged_source_randomness':sample==0,'win':int(b.over and b.winner==seat),'terminal':b.over,'steps':steps,'error':error,'own_first_turn_plan':turn_trace})
  alternatives.append({'action':action,'is_original':action==case['original_action'],'fast_model_supported':predicted is not None,'engine_accepted':all(not x['error'] for x in outcomes),'outcomes':outcomes,'win_rate':sum(o['win'] for o in outcomes)/samples})
 return {**case,'alternatives':alternatives,'proposal':proposed,'prefix_actions':prefix,'continuation_policy':continuation+' for all roots; frozen source opponent','evidence_kind':'conditional_source_hidden_state_diagnostic','randomness':'Sample 0 preserves the source RNG and deck order. Other samples resample future order/RNG, retaining source hands. Changed actions consume RNG differently; no claim of identical future draws.','first_important_error':'unresolved','public_belief_coverage':'Not reconstructed; no unknown-hand win guarantee.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--selection',default='counterfactual-selection.json');p.add_argument('--name',default='counterfactual-pilot');p.add_argument('--samples',type=int,default=3);p.add_argument('--proposal',default='development/secret_hunter_dgm/candidates/C0');p.add_argument('--continuation',default='development/secret_hunter_dgm/candidates/K1');p.add_argument('--diverse',action='store_true');a=p.parse_args()
 check(ROOT/a.continuation);check(ROOT/a.proposal);cases=json.loads((D/a.selection).read_text())
 reserve(a.name,full=len(cases)*3*a.samples,short=len(cases)*180,seconds=1800)
 out=[]
 with ProcessPoolExecutor(max_workers=6) as pool,(D/(a.name+'.jsonl')).open('w') as f:
  fs=[pool.submit(worker,(c,i,a.samples,a.proposal,a.continuation,a.diverse)) for i,c in enumerate(cases)]
  for future in as_completed(fs):
   try:r=future.result()
   except Exception:r={'error':traceback.format_exc()}
   out.append(r);f.write(json.dumps(r)+'\n');f.flush();print('cases',len(out),len(cases),flush=True)
 errors=sum(bool(c.get('error')) for c in out)+sum(bool(o['error']) for c in out for x in c.get('alternatives',[]) for o in x['outcomes'])
 actual=sum(len(x['outcomes']) for c in out for x in c.get('alternatives',[]));short=sum(c.get('prefix_actions',0)+3 for c in out)
 finish(a.name,actual_full=actual,actual_short=short,errors=errors)
 summary={'cases':len(out),'original_included':sum(any(x['is_original'] for x in c.get('alternatives',[])) for c in out),'original_outside_fast_model':sum(any(x['is_original'] and not x['fast_model_supported'] for x in c.get('alternatives',[])) for c in out),'full':actual,'errors':errors,'first_errors_certified':0}
 write(D/(a.name+'-summary.json'),summary);print(json.dumps(summary));assert not errors
if __name__=='__main__':main()
