"""Post-decision, exact public-state/action/terminal replay of fixed flip examples."""
import json,time
from development.secret_hunter_astra_sprint.study import RUN,ROOT,check
from development.secret_hunter_astra_sprint.tactical import setup,visible
from development.secret_hunter_astra_sprint import ledger
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha

def main():
 db=ledger.connect(RUN);m=ledger.meta(db,'manifest');check(m)
 assert all(db.execute('select status from batches where id=?',(b,)).fetchone()[0]=='done' for b in ('final-core','final-guard'))
 decision=json.loads((ROOT/'docs/secret_hunter_astra_sprint/recommendation.json').read_text());challenger=decision['challenger']
 report=json.loads((RUN/'batches/final-core/report.json').read_text());flips=report['comparisons'].get(challenger,{}).get('flips',[])
 selected=[]
 for sign in (1,-1):
  rows=[r for r in flips if r['opponent'].startswith('astra-') and (r['b_win']-r['a_win'])*sign>0]
  if rows:selected.append(min(rows,key=lambda r:(r['seed'],r['opponent'],r['seat'])))
 selection={'created':time.time(),'rule':'First Astra rescue and first Astra regression by (source seed, opponent, seat), each replayed for both frozen arms after promotion decision. If a sign is absent, skip it; no replacement fishing.','cases':selected,'maximum_auxiliary_attempts':4,'outcomes_used_for_selection':False}
 path=RUN/'final-case-plan.json'
 if path.exists():assert json.loads(path.read_text())['cases']==selected
 else:ledger.atomic(path,selection)
 setup('DARCL2')
 from hs_arena.engine import Engine
 from hs_arena.deck import load_deck
 specs={s['name']:s for s in json.loads((ROOT/'development/teacher_eval/core.json').read_text())};packages={r['name']:r for r in json.loads((RUN/'release-candidates.json').read_text())};records=[]
 for case in selected:
  name,seed,seat=case['opponent'],case['seed'],case['seat']
  for arm in ('DARCL2',challenger):
   key=f'final-case-{arm}-{seed}-{name}-s{seat}';old=db.execute('select * from auxiliary_games where key=?',(key,)).fetchone()
   if old:
    assert old['status']=='done';records.append(json.loads(old['result']));continue
   count=db.execute('select count(*) from attempts').fetchone()[0]+db.execute('select count(*) from auxiliary_games').fetchone()[0]
   assert count<m['limits']['full_games'] and time.time()<m['deadline']
   candidates=[json.loads(r[0]) for r in db.execute("select result from tasks where batch='final-core' and candidate=? and seed=? and seat=?",(arm,seed,seat))]
   result=next(r for r in candidates if r['opponent']==name);folder=RUN/'batches/final-core'/arm/'games'/result['game']
   logs={i:[json.loads(l) for l in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
   source=ROOT/packages[arm]['extracted'];assert fingerprint(source)==packages[arm]['source_sha256']
   with db:db.execute('insert into auxiliary_games values (?,?,?,?,?)',(key,'running',time.time(),None,None))
   try:
    decks={seat:load_deck(source/'deck.json'),3-seat:load_deck(ROOT/specs[name]['deck'])};e=Engine(decks[1],decks[2],seed,max_turns=180);ix={1:0,2:0};trace=[]
    while not e.over:
     active,_=e.pending();r=logs[active][ix[active]];s=e.view(active);assert visible(s)==visible(r['state']),(key,active,ix[active]);before=visible(e.view(seat))
     assert e.step(active,r['action']).accepted
     trace.append({'player':active,'turn':s['turn'],'action':r['action'],'before_public':before,'after_public':visible(e.view(seat))});ix[active]+=1
    assert e.winner==result['result']['winner'] and all(ix[i]==len(logs[i]) for i in (1,2))
    evidence=RUN/'case-replays'/(key+'.json');ledger.atomic(evidence,{'key':key,'arm':arm,'source_game':str(folder),'winner':e.winner,'steps':len(trace),'own_actions':[r for r in trace if r['player']==seat],'all_actions':trace})
    rec={'key':key,'arm':arm,'seed':seed,'opponent':name,'seat':seat,'winner':e.winner,'own_win':e.winner==seat,'steps':len(trace),'all_visible_states_and_actions_verified':True,'source_sha256':packages[arm]['source_sha256'],'evidence_sha256':sha(evidence),'path':str(evidence)}
    with db:db.execute("update auxiliary_games set status='done',finished=?,result=? where key=?",(time.time(),json.dumps(rec),key))
    records.append(rec)
   except Exception as exc:
    with db:db.execute("update auxiliary_games set status='error',finished=?,result=? where key=?",(time.time(),json.dumps({'error':repr(exc)}),key))
    raise
 ledger.atomic(RUN/'final-case-replay-audit.json',records);ledger.atomic(ROOT/'docs/secret_hunter_astra_sprint/final-case-replay-audit.json',records);print(json.dumps(records,indent=2))
if __name__=='__main__':main()
