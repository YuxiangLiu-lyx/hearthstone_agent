"""Official-engine full-turn plan search and disjoint paired future validation.

The engine retains source hidden hands for conditional diagnosis only. Proposal
scoring and all policies see normal public observations. A saved plan prefix is
used only while its public-state gates match; observed chance divergence causes
immediate public-policy replanning, never blind execution of a stored sequence.
"""
import argparse,collections,copy,hashlib,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.accounting import reserve,finish
D=ROOT/'docs/secret_hunter_response';C=ROOT/'development/secret_hunter_response/candidates/Y1'
def public_key(s):
 fields={k:{f:s[k].get(f) for f in ('hero','board','hand','hand_size','mana','max_mana','weapon','secrets','secrets_count','deck_remaining')} for k in ('you','opponent')}
 return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
def reconstruct(case):
 from hs_arena.engine import Engine
 from hs_arena.deck import load_deck
 r=case['row'];seat=r['seat'];src=ROOT/case['source'];spec=next(o for o in json.loads((src/'config.json').read_text())['population'] if o['name']==r['opponent'])
 own=load_deck(C/'deck.json');other=load_deck(ROOT/spec['deck']);e=Engine(own if seat==1 else other,other if seat==1 else own,r['seed'],max_turns=180)
 import gzip
 archive=ROOT/'docs/secret_hunter_response/replay-prefixes.jsonl.gz'
 if archive.exists():
  records=[json.loads(l) for l in gzip.open(archive,'rt')]
  record=next((x for x in records if x['game']==r['game'] and x['seq']==case['observation']['seq']),None)
  if record:
   for step in record['actions']:assert e.step(step['player'],step['action']).accepted
   assert public_key(e.view(seat))==public_key(case['observation'])
   return e,spec,len(record['actions'])
 obs={i:readlines(src/'games'/r['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};prefix=0
 while True:
  who,_=e.pending();z=obs[who][idx[who]]
  if who==seat and z['state']['seq']==case['observation']['seq']:break
  assert e.step(who,z['action']).accepted and not e.over;idx[who]+=1;prefix+=1
 assert public_key(e.view(seat))==public_key(case['observation'])
 return e,spec,prefix

def worker(task):
 case,index,selection_samples,validation_samples=task;sys.path.insert(0,str(C/'scripts'))
 from program_policy import decide
 from secret_policy import rank
 from action_validator import legal
 from state_features import with_public_history
 from race_plan import value
 from development.secret_hunter_tactics.run import opponent
 cfg=json.loads((C/'config.json').read_text());seat=case['row']['seat'];e,spec,prefix=reconstruct(case);other=opponent(spec)
 def visible(b,p):
  s=b.view(p);s.update(player=p,seq=0,game_id='offline-public-plan')
  return with_public_history(s,[v for ev in b.events if (v:=ev.view(p)) is not None])
 def decide_public(b,p):
  s=visible(b,p)
  if p!=seat:return other.fn(s)
  a,info=decide(s,cfg);assert legal(s,a) and not info.get('error'),info;return a
 # A bounded official-engine beam creates complete endpoints, not one root per plan.
 beam=[(e,[],[])];ends=[];seen=set();nodes=0
 for depth in range(7):
  nxt=[]
  for b,path,gates in beam:
   s=visible(b,seat);gate=public_key(s)
   # Explicitly preserve the opportunity to end at every reachable state.
   ends.append((value(s,cfg),path+[{'type':'end_turn'}],gates+[gate],s))
   choices=[a for _,a in rank(s,cfg,time.monotonic()+1) if a['type'] not in ('end_turn','concede')]
   unique=[];rootkeys=set()
   for a in choices:
    cid=next((c['card_id'] for c in s['you']['hand'] if c['entity_id']==a.get('card')),None)
    k=json.dumps(a if cid=='EX1_162' else {k:v for k,v in a.items() if k!='position'},sort_keys=True)
    if k not in rootkeys:unique.append(a);rootkeys.add(k)
   for a in unique[:10]:
    if nodes>=130:break
    q=copy.deepcopy(b);accepted=q.step(seat,a).accepted;nodes+=1;assert accepted
    if q.over:
     ends.append((1e6 if q.winner==seat else -1e6,path+[a],gates+[gate],visible(q,seat)));continue
    p,_=q.pending()
    if p!=seat:continue
    sq=visible(q,seat);key=public_key(sq)
    if key in seen:continue
    seen.add(key);nxt.append((value(sq,cfg),q,path+[a],gates+[gate]))
   if nodes>=130:break
  nxt.sort(key=lambda x:x[0],reverse=True);beam=[(b,p,g) for _,b,p,g in nxt[:5]]
  if nodes>=130 or not beam:break
 ends.sort(key=lambda x:x[0],reverse=True);plans=[{'id':'Y1','kind':'public_policy','actions':case['original_plan'],'gates':[]}];endkeys=set();rootcounts=collections.Counter()
 for v,path,gates,s in ends:
  # At most two endpoints per first action; different suffixes remain eligible.
  key=public_key(s);root=json.dumps(path[0],sort_keys=True)
  if key in endkeys or rootcounts[root]>=2 or path==case['original_plan']:continue
  endkeys.add(key);rootcounts[root]+=1;plans.append({'id':'plan-'+str(len(plans)),'kind':'gated_complete_turn','actions':path,'gates':gates,'proposal_value':v})
  if len(plans)==4:break
 if case.get('_frozen_plans'):plans=case['_frozen_plans']
 out=[]
 for plan in plans:
  outcomes=[]
  for split,count,offset in [('selection',selection_samples,1),('validation',validation_samples,case.get('_validation_offset',51))]:
   for sample in range(count):
    b=copy.deepcopy(e);rng_seed=964000+index*100+offset+sample;b.game.random.seed(rng_seed)
    for p in b.game.players:b.game.random.shuffle(p.deck)
    steps=0;turn=b.game.turn;trace=[];prefix_active=True;cursor=0;closed=False;endstate=None;nextstate=None;error=None
    try:
     while not b.over and steps<600:
      p,_=b.pending();s=visible(b,p)
      in_turn=p==seat and s['turn']==turn
      if plan['kind']=='gated_complete_turn' and in_turn and prefix_active and cursor<len(plan['actions']) and public_key(s)==plan['gates'][cursor] and legal(s,plan['actions'][cursor]):
       a=plan['actions'][cursor];cursor+=1
      else:
       if in_turn:prefix_active=False
       a=decide_public(b,p)
      if in_turn:trace.append(a)
      if in_turn and a['type']=='end_turn':endstate=projection(s)
      if p==seat and s['turn']!=turn and nextstate is None:nextstate=projection(s)
      assert b.step(p,a).accepted;steps+=1
     if not b.over:error='continuation_limit'
    except Exception:error=traceback.format_exc()
    outcomes.append({'split':split,'sample':sample,'future_rng_seed':rng_seed,'win':int(b.over and b.winner==seat),'terminal':b.over,'error':error,'steps':steps,'prefix_steps':cursor,'own_first_turn_plan':trace,'end_of_own_turn':endstate,'start_of_next_own_turn':nextstate})
  out.append({**plan,'outcomes':outcomes})
 selected=max(out,key=lambda p:sum(o['win'] for o in p['outcomes'] if o['split']=='selection'))['id']
 return {'case_id':index,'case':case,'plans':out,'selected_on_selection_only':selected,'generation_nodes':nodes,'prefix_actions':prefix,'evidence_kind':'conditional_source_hidden_hands; future deck order and random streams resampled','caveat':'Paired seeds do not guarantee identical future random consumption. Public gate mismatch replans. No source hidden card is a predictor.','original_replay_plan_retained':True}
def projection(s):
 return {'own_hp':s['you']['hero']['health'],'enemy_hp':s['opponent']['hero']['health'],'own_attack':sum(m['attack'] for m in s['you']['board']),'enemy_attack':sum(m['attack'] for m in s['opponent']['board']),'own_board':[m['card_id'] for m in s['you']['board']],'enemy_board':[m['card_id'] for m in s['opponent']['board']]}
def select(n):
 xs=json.loads((D/'turn-starts.json').read_text());buckets=collections.defaultdict(list)
 for x in xs:
  r=x['row'];x['row']={k:r[k] for k in ('seed','seat','game','opponent','first_player','score')}
  # Fit/calibration source seeds only; response prediction test is not tuned here.
  if r['seed']%5==0:continue
  if len(x['observation']['legal_actions'])<4:continue
  buckets[(r['opponent'],r['score'],r['seat']==r['first_player'],x['own_turn'])].append(x)
 selected=[];games=set()
 for k in buckets:buckets[k].sort(key=lambda x:(x['row']['seed'],x['row']['seat']))
 while len(selected)<n and any(buckets.values()):
  for k in sorted(buckets,key=lambda k:(k[3],k[1],k[2],k[0])):
   while buckets[k] and buckets[k][0]['row']['game'] in games:buckets[k].pop(0)
   if buckets[k] and len(selected)<n:
    c=buckets[k].pop(0);selected.append(c);games.add(c['row']['game'])
 return selected
def main():
 p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=24);p.add_argument('--selection',type=int,default=3);p.add_argument('--validation',type=int,default=5);p.add_argument('--name',default='counterfactual-pilot');a=p.parse_args()
 cases=select(a.n);write(D/(a.name+'-selection.json'),cases)
 reserve(a.name,full=len(cases)*4*(a.selection+a.validation),short=len(cases)*300,seconds=1800);rows=[]
 with ProcessPoolExecutor(max_workers=6) as pool,(D/(a.name+'.jsonl')).open('w') as f:
  futures=[pool.submit(worker,(c,i,a.selection,a.validation)) for i,c in enumerate(cases)]
  for future in as_completed(futures):
   try:r=future.result()
   except Exception:r={'error':traceback.format_exc()}
   rows.append(r);f.write(json.dumps(r,separators=(',',':'))+'\n');f.flush();print('completed',len(rows),len(cases),flush=True)
 actual=sum(len(p['outcomes']) for r in rows for p in r.get('plans',[]));errors=[r['error'] for r in rows if r.get('error')]+[o['error'] for r in rows for p in r.get('plans',[]) for o in p['outcomes'] if o['error']]
 finish(a.name,actual_full=actual,actual_short=sum(r.get('generation_nodes',0)+r.get('prefix_actions',0) for r in rows),errors=errors);assert not errors,errors
 print(json.dumps({'cases':len(rows),'full_continuations':actual,'errors':0}))
if __name__=='__main__':main()
