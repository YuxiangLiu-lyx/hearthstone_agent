"""H3: the sprint's sole one-card substitution, after H2's full-game review."""
import json,time
from development.secret_hunter_astra_sprint.study import RUN,HERE,register
from development.secret_hunter_astra_sprint.build import clone,audit
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

def main():
 db=ledger.connect(RUN)
 assert db.execute("select status from batches where id='round2-ranker'").fetchone()[0]=='done'
 review=json.loads((RUN/'hypotheses/H2-full-decision.json').read_text());assert review['reason']
 assert not ledger.meta(db,'selection_opened',False) and not ledger.meta(db,'final_opened',False)
 lineage=json.loads((HERE/'lineage.json').read_text())
 assert all(not r['deck']['changes'] or r['name']=='DA2' for r in lineage),'This sprint permits only one new card substitution hypothesis'
 hypothesis=('H3: In early Warlock board fights, the single three-mana random Deadly Shot often cannot precisely remove a two-health key attacker while also developing a minion. '
  'Replace only that card at slot 23 with a second one-mana Arcane Shot; keep the other 29 slots, all tactics, mulligan and search budgets identical to DARCL2. '
  'Predict positive fresh Astra macro gain from more precise clear-plus-development opportunities. Refute with nonpositive natural full-game gain, failed independent confirmation, or excessive loss of large-target removal in the frozen guardrail. '
  'This is the only new card substitution tested this sprint, not an assertion that card exposure implies causal value.')
 plan={'created':time.time(),'candidate':'DA2','parent':'DARCL2','hypothesis':hypothesis,
  'evidence':{n:sha(RUN/n) for n in ('single-slot-diagnosis.json','opening-resource-diagnosis.json','flame-clear-diagnosis.json')},
  'evidence_summary':'Unscreened 600 seen Astra games: precise key-clear opportunity with Deadly Shot in hand 132 games, including 45 original losses; paired Flame Imp clear subgroup 6 rescues / 0 regressions across 5 positive source seeds, development-only.',
  'fresh_full_test':{'batch':'round3-arcane','start':62150300,'seeds':40,'arms':['DARCL2','DA2'],'workers':6},
  'fixed_deck_change':{'slot_zero_based':23,'removed':'EX1_617','added':'DS1_185'},
  'negative_control':'Healthy taunts, Amani and larger bodies exceed Arcane Shot damage; compare original wins that become losses before further work.',
  'mulligan_unchanged':'Opening diagnostics did not establish a general opening failure; no repeat of the failed trap-keep rule.'}
 path=RUN/'hypotheses/H3-plan.json'
 if path.exists():assert json.loads(path.read_text())['hypothesis']==hypothesis
 else:ledger.atomic(path,plan)
 candidate=clone('DA2','DARCL2',changes=[('EX1_617','DS1_185')],hypothesis=hypothesis,generation=1)
 validation=audit(candidate);ledger.atomic(RUN/'DA2-deck-audit.json',validation);register(db)
 lock={'created':time.time(),'candidate':'DA2','hypothesis':hypothesis,'source_sha256':fingerprint(candidate),'plan_sha256':sha(path),'validation_passed':validation['valid']}
 target=RUN/'hypotheses/H3-lock.json'
 if target.exists():assert json.loads(target.read_text())['source_sha256']==lock['source_sha256']
 else:ledger.atomic(target,lock)
 print(json.dumps(lock,indent=2))
if __name__=='__main__':main()
