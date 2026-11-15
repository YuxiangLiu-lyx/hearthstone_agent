"""H4: public resource conservation after a draw deathrattle or visible bounce."""
import json,time
from development.secret_hunter_astra_sprint.study import RUN,HERE,register
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.build import clone,audit
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

def main():
 db=ledger.connect(RUN)
 assert db.execute("select status from batches where id='round3-arcane'").fetchone()[0]=='done'
 assert json.loads((RUN/'hypotheses/H3-full-decision.json').read_text())['reason']
 assert not ledger.meta(db,'selection_opened',False) and not ledger.meta(db,'final_opened',False)
 hypothesis=('H4: The public effect model transfers a killed Loot Hoarder into one extra opponent hand card, but race evaluation drops that future resource while rewarding removal of its deathrattle value. '
  'Price opponent public hand_size symmetrically with our hand using the existing turn_hand coefficient 0.973, without predicting card identities. '
  'This should reduce overvalued draw-deathrattle clears and visible bounce lines while preserving high-attack clear alternatives. '
  'Parent DARCL2, one scoring expression only, identical deck/mulligan/search caps. Refute if actual policy continuations do not produce repeatable net rescues, or fresh full games fail to show Astra gain. '
  'Unlike PRR this does not learn/reweight board, race, secret or own-hand features; unlike TRPLY it adds no reply or recovery nodes.')
 plan={'created':time.time(),'candidate':'EHC','parent':'DARCL2','hypothesis':hypothesis,
  'evidence':{'consideration_sha256':sha(RUN/'hypotheses/H4-consideration.json'),'flame_clear_sha256':sha(RUN/'flame-clear-diagnosis.json'),'PRR_flip_inspection_sha256':sha(RUN/'H2-original-world-flip-inspection.json')},
  'fixed_coefficient':'Reuse cfg turn_hand=0.973; no grid search or fitted new coefficient.',
  'continuation_screen':{'sources':'All initial/late1 TRAIN roots only, 264 roots and 792 paired worlds; all already seen. No independent label holdout claim.','advance_if':'worlds 0/1 total paired actual-policy net > 0 and at least two net-positive source seeds; report world2 but it is also seen.'},
  'fresh_full_test':{'batch':'round4-hand-resource','start':62150400,'seeds':40,'arms':['DARCL2','EHC'],'workers':6},
  'negative_controls':'Visible Freezing Trap bounce increases opponent public hand count too; check resulting original-win regressions and non-Astra families.',
  'causal_limit':'The motivating teacher routes also change development or target sequence, so missing resource value is a hypothesis, not a proven explanation of those wins.'}
 path=RUN/'hypotheses/H4-plan.json'
 if path.exists():assert json.loads(path.read_text())['hypothesis']==hypothesis
 else:ledger.atomic(path,plan)
 def edit(dest):
  p=dest/'scripts/race_plan.py';s=p.read_text();old="score+=.2*hp+cfg.get('turn_hand',.973)*len(y['hand'])";new="score+=.2*hp+cfg.get('turn_hand',.973)*(len(y['hand'])-o.get('hand_size',0))"
  assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
 candidate=clone('EHC','DARCL2',edit=edit,hypothesis=hypothesis,generation=1);validation=audit(candidate);ledger.atomic(RUN/'EHC-deck-audit.json',validation);register(db)
 lock={'created':time.time(),'candidate':'EHC','hypothesis':hypothesis,'source_sha256':fingerprint(candidate),'plan_sha256':sha(path),'validation_passed':validation['valid']}
 target=RUN/'hypotheses/H4-lock.json'
 if target.exists():assert json.loads(target.read_text())['source_sha256']==lock['source_sha256']
 else:ledger.atomic(target,lock)
 print(json.dumps(lock,indent=2))
if __name__=='__main__':main()
