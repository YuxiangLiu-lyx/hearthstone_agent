"""Freeze H2's learned coefficients into a standard-library-only candidate."""
import json,time
from development.secret_hunter_astra_sprint.study import RUN,HERE,register
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.build import clone,audit
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

def main():
    plan=json.loads((RUN/'hypotheses/H2-plan.json').read_text());fit=json.loads((RUN/'H2-fitted-ranker.json').read_text())
    def edit(dest):
        source=(HERE/'rank_features.py').read_text()
        source+='\nCOEFFICIENTS = '+repr(fit['coef'])+'\n\ndef correction(state,reply):\n    if not eligible(state):return 0.\n    return max(-4.,min(4.,sum(a*b for a,b in zip(vector(state,reply),COEFFICIENTS))))\n'
        (dest/'scripts/paired_ranker.py').write_text(source)
        p=dest/'scripts/turn_search.py';s=p.read_text()
        old="if response['visible_lethal_found']:v-=100000"
        new="from paired_ranker import correction\n            learned=correction(endpoint,response['state'])\n            v+=learned\n            report.setdefault('paired_ranker',[]).append({'root':path[0] if path else {'type':'end_turn'},'correction':learned})\n            if response['visible_lethal_found']:v-=100000"
        assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
    source=clone('PRR','DARCL2',edit=edit,hypothesis=plan['hypothesis'],generation=1)
    validation=audit(source);ledger.atomic(RUN/'PRR-deck-audit.json',validation)
    register(ledger.connect(RUN))
    lock={'created':time.time(),'candidate':'PRR','hypothesis':plan['hypothesis'],'source_sha256':fingerprint(source),
          'plan_sha256':sha(RUN/'hypotheses/H2-plan.json'),'fitted_model_sha256':sha(RUN/'H2-fitted-ranker.json'),
          'validation_passed':validation['valid'],'caution':'Grouped CV only improved two route-world outcomes versus prior endpoint scores; it does not establish natural-frequency benefit. Require actual policy continuation and fresh full-game evidence.'}
    path=RUN/'hypotheses/H2-lock.json'
    if path.exists():assert json.loads(path.read_text())['source_sha256']==lock['source_sha256']
    else:ledger.atomic(path,lock)
    print(json.dumps(lock,indent=2))
if __name__=='__main__':main()
