"""H1: restore deterministic standalone-Juggler coverage at T2-T5."""
import json
import time
from development.secret_hunter_astra_sprint.study import RUN,HERE,register
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.build import clone,audit
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

def main():
    db=ledger.connect(RUN)
    assert not ledger.meta(db,'selection_opened',False) and not ledger.meta(db,'final_opened',False)
    hypothesis=('H1: T2-T5 standalone Knife Juggler is a deterministic play when no friendly unsilenced Juggler is already present. '
        'The response-mode exclusion currently skips the entire turn search when this card is ranked first, so alternate development and key clears are never compared. '
        'Allow this one play class in response projection, retaining all existing random-trigger exclusions, the original Juggler route, '
        '350 own nodes, width 10, depth 9, 6x48 reply nodes and original time limits. Predict greater route recall and positive fresh Astra paired full-game gain; '
        'refute if recall does not reach rescued routes, or changed actions fail to produce net full-game wins. Deck and mulligan fixed.')
    plan={'created':time.time(),'candidate':'RJC','parent':'DARCL2','hypothesis':hypothesis,
        'evidence':{name:sha(RUN/name) for name in ('juggler-coverage-train-labels.json','natural-juggler-coverage.json','labels-train-worlds-01.json')},
        'training_evidence':'Alternative development: 17 roots / 9 seeds / 34 paired route-worlds, 6 rescues and 1 regression, positive net at 5 seeds and negative at 1.',
        'fresh_full_test':{'batch':'round1-recall','start':62150100,'seeds':40,'arms':['DARCL2','RJC'],'pool':'core','workers':6},
        'heldout_not_opened':True,'mechanism_only':'Two response-mode coverage predicates; no scoring, deck, mulligan, chance model or budget modification.'}
    path=RUN/'hypotheses/H1-plan.json'
    if path.exists():assert json.loads(path.read_text())['hypothesis']==hypothesis
    else:ledger.atomic(path,plan)
    def edit(dest):
        p=dest/'scripts/tactical_model.py';source=p.read_text()
        for mode,ending in [('state','continue'),('result','return None')]:
            old=f"if {mode}.get('planning_mode')=='response' and cid=='NEW1_019':{ending}"
            new=f"if {mode}.get('planning_mode')=='response' and cid=='NEW1_019' and not 2<=y['max_mana']<=5:{ending}"
            assert source.count(old)==1
            source=source.replace(old,new)
        p.write_text(source)
    candidate=clone('RJC','DARCL2',edit=edit,hypothesis=hypothesis,generation=1)
    validation=audit(candidate);ledger.atomic(RUN/'RJC-deck-audit.json',validation)
    cs=register(db);lock={'created':time.time(),'candidate':'RJC','hypothesis':hypothesis,
        'source_sha256':fingerprint(candidate),'plan_sha256':sha(path),'validation_passed':validation['valid']}
    destination=RUN/'hypotheses/H1-lock.json'
    if destination.exists():assert json.loads(destination.read_text())['source_sha256']==lock['source_sha256']
    else:ledger.atomic(destination,lock)
    print(json.dumps(lock,indent=2))

if __name__=='__main__':main()
