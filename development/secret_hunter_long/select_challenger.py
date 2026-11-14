"""Select exactly one immutable challenger after both complete CLI pools."""
import json
from fractions import Fraction
import time
from development.secret_hunter_long.study import RUN
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import paired

ERRORS=('illegal','timeouts','forfeits','harness_errors','opponent_errors','policy_errors','fallbacks','over_2s','public_input_violations')

def main():
    db=train.connect(RUN);assert not train.meta(db,'final_opened',False)
    plan=json.loads((RUN/'selection-plan.json').read_text());freeze=json.loads((RUN/'selection-freeze.json').read_text())
    reports={}
    for pool in ('core','guardrail'):
        block=plan[pool];batch=db.execute('select * from batches where id=?',(block['batch'],)).fetchone()
        assert batch and batch['status']=='done' and json.loads(batch['arms'])==plan['arms']
        report=json.loads((RUN/'batches'/block['batch']/'report.json').read_text())
        assert all(report['arms'][a]['all']['n']==block['seeds']*(12 if pool=='core' else 28) for a in plan['arms'])
        reports[pool]=report
    reliability={a:all(not r['arms'][a]['all'][k] for r in reports.values() for k in ERRORS) for a in plan['arms']}
    assert reliability['B'],'Reference reliability failed; inspect before freezing'
    rows={}
    for arm in plan['arms']:
        if not reliability[arm]:continue
        for pool in ('core','guardrail'):
            values=[json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=?',(plan[pool]['batch'],arm))]
            assert all(r.get('execution')=='full_cli' for r in values)
            if pool=='core':rows[arm]=values
    primary={a:paired(rows['B'],rows[a],groups=['astra','bot2'],equal_groups=True) for a in rows if a!='B'}
    # Rank exact terminal fractions: mathematically equal macro rates must use
    # the preregistered arm order, not floating-point summation roundoff.
    exact={}
    for arm in primary:
        rates=[]
        for group in ('astra','bot2'):
            values=[Fraction(r['score']) for r in rows[arm] if r['group']==group]
            assert values
            rates.append(sum(values)/len(values))
        exact[arm]=sum(rates)/2
    ranking=sorted([a for a in plan['arms'] if a!='B' and reliability[a]],
                   key=lambda a:(-exact[a],plan['arms'].index(a)))
    selected=ranking[0] if ranking else 'B'
    result={'created':time.time(),'challenger':selected,'ranking':ranking,'reliability':reliability,
       'fingerprints':freeze['fingerprints'],'plan':plan,
       'primary_rates':{a:primary[a]['b_rate'] for a in ranking},'primary_comparisons':primary,
       'exact_primary_fractions':{a:str(exact[a]) for a in ranking},
       'rule':'maximum equal-family Astra/Bot2 terminal rate among CLI-reliable challengers; ties use preregistered arms order; guardrail contributes reliability, final holdout independently enforces performance gates',
       'no_retuning':True}
    path=RUN/'selection-decision.json'
    if path.exists():assert {k:v for k,v in json.loads(path.read_text()).items() if k!='created'}=={k:v for k,v in result.items() if k!='created'}
    else:train.atomic(path,result)
    train.setmeta(db,'selected_challenger',selected);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
