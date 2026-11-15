"""Paired action paths for a card substitution; never call these identical states."""
import argparse,collections,json
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.tactical import digest
from development.teacher_eval.compare import index

def main(batch,arm):
 db=ledger.connect(RUN);b=db.execute('select * from batches where id=?',(batch,)).fetchone();assert b['status']=='done'
 if b['phase'].startswith('final'):assert all(db.execute('select status from batches where id=?',(p,)).fetchone()[0]=='done' for p in ('final-core','final-guard'))
 maps={a:index([json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=?',(batch,a))]) for a in ('DARCL2',arm)}
 assert maps['DARCL2'].keys()==maps[arm].keys();counts=collections.Counter();examples=[]
 for key,base in maps['DARCL2'].items():
  other=maps[arm][key];logs=[]
  for a,r in [('DARCL2',base),(arm,other)]:
   folder=RUN/'batches'/batch/a/'games'/r['game'];logs.append([json.loads(l) for l in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()])
  counts['paired_games']+=1;mulls=[next(z for z in rows if z['state']['phase']=='mulligan')['action'] for rows in logs];counts['mulligan_actions_differ']+=mulls[0]!=mulls[1]
  first=None;exposure=None
  for ix,(a,z) in enumerate(zip(*logs)):
   if a['state']['phase']=='main' and z['state']['phase']=='main' and exposure is None:
    ah={c['entity_id']:c['card_id'] for c in a['state']['you']['hand']};bh={c['entity_id']:c['card_id'] for c in z['state']['you']['hand']}
    changed=[{'entity':i,'baseline':ah[i],'candidate':bh[i]} for i in ah.keys()&bh.keys() if ah[i]!=bh[i]]
    if changed:exposure={'index':ix,'seq':a['state']['seq'],'T':a['state']['you']['max_mana'],'identity_changes':changed}
   if a['action']!=z['action']:
    first={'index':ix,'a':a,'b':z,'same_public_state':digest(a['state'])==digest(z['state'])};break
  if first:counts['executed_action_path_differences']+=1;counts['same_public_state_at_first_action_difference']+=first['same_public_state']
  if base['score']!=other['score']:counts['rescues' if other['score']>base['score'] else 'regressions']+=1
  if first or base['score']!=other['score']:examples.append({'key':key,'a_win':base['score'],'b_win':other['score'],'mulligan_actions_equal':mulls[0]==mulls[1],'first_hand_identity_difference_before_action_change':exposure,'first_action_difference':first})
 result={'batch':batch,'candidate':arm,'counts':dict(counts),'examples':examples,'scope':'One card slot changes public remaining-deck counts from the beginning. Equal action prefixes are not equal public-state prefixes; first action divergence is descriptive. No observed future or opponent hidden hand enters policy.'}
 ledger.atomic(RUN/'analysis'/f'{batch}-DARCL2-{arm}-action-paths.json',result);print(json.dumps(result['counts']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('arm');a=p.parse_args();main(a.batch,a.arm)
