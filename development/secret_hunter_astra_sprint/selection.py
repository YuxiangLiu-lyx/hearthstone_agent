"""Fresh selection, common-draw course interpretation, and capacity lock."""
import argparse
import difflib
import json
import random
import time
from fractions import Fraction
from development.secret_hunter_astra_sprint.study import ROOT,RUN,HERE,register
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.release import ERRORS,raw_reliability
from development.secret_hunter_program.common import sha

def prepare(candidates):
    db=ledger.connect(RUN);m=ledger.meta(db,'manifest');cs=register(db)
    assert not ledger.meta(db,'selection_opened',False) and not ledger.meta(db,'final_opened',False)
    assert not ledger.meta(db,'pid') and not ledger.meta(db,'cf_pid')
    assert 1<=len(candidates)<=2 and len(set(candidates))==len(candidates) and 'DARCL2' not in candidates
    evidence=json.loads((RUN/'development-decision.json').read_text())
    assert evidence['candidates']==candidates and evidence['reason']
    arms=['DARCL2',*candidates];load=json.loads((RUN/'throughput.json').read_text())
    workers=load['selected_concurrency'];rates=[load[f'pilot-c{workers}']['games_per_minute']]
    # Include completed full-CLI development of the proposed candidates; use a
    # 15% conservative throughput allowance, chosen before selection outcomes.
    for b in db.execute("select * from batches where phase='cli_development' and status='done'"):
        if not set(json.loads(b['arms'])).intersection(candidates):continue
        n,elapsed=db.execute('select count(*),max(a.finished)-min(a.started) from attempts a join tasks t on t.key=a.task where t.batch=?',(b['id'],)).fetchone()
        if n and elapsed:rates.append(n/elapsed*60)
    rate=.85*min(rates)
    used=db.execute('select count(*) from attempts').fetchone()[0]+db.execute('select count(*) from auxiliary_games').fetchone()[0]
    selection_count=len(arms)*(80*12+8*28)
    assert used+selection_count<=m['limits']['full_games']-5000
    def fits(groups):
        n=2*(12*groups+28*16)
        return used+selection_count+n+16<=18000 and time.time()+(selection_count+n)/rate*60+2700<m['deadline']
    groups=170 if fits(170) else 100
    assert fits(groups),'Only baseline acceptance fits; do not open selection/final'
    assert time.time()+selection_count/rate*60<m['candidate_generation_deadline']
    capacity={'created':time.time(),'before_selection':True,'groups':groups,'guard_groups':16,
        'conservative_games_per_minute':rate,'measured_rates':rates,'workers':workers,
        'used_full_attempts':used,'selection_games':selection_count,'final_games':2*(groups*12+448),
        'protocol_pack_margin_s':2700,'reserved_auxiliary_attempts':16}
    if groups!=m['final_target']['seeds_core']:
        ledger.atomic(RUN/'manifest-before-capacity.json',m)
        m['seed_blocks']['final_core'][1]=m['seed_blocks']['final_core'][0]+groups-1
        m['final_target'].update(seeds_core=groups,per_arm_core=groups*12)
        ledger.atomic(RUN/'manifest.json',m);ledger.setmeta(db,'manifest',m)
    plan={'created':time.time(),'arms':arms,'workers':workers,'capacity':capacity,
        'core':{'batch':'selection-core','start':62250000,'seeds':80},
        'guardrail':{'batch':'selection-guard','start':62251000,'seeds':8},
        'fingerprints':{a:cs[a]['sha256'] for a in arms},
        'development_decision_sha256':sha(RUN/'development-decision.json'),
        'simulation_plan_sha256':sha(RUN/'score-simulation-plan.json'),
        'selection_rule':'Among reliable challengers: Astra macro, within 0.5pp common-draw positive score above 10, fewer changed source lines, stable name. No tuning after opening.'}
    assert not (RUN/'selection-plan.json').exists()
    ledger.atomic(RUN/'final-capacity.json',capacity);ledger.atomic(RUN/'selection-plan.json',plan)
    print(json.dumps(plan,indent=2))

def simulate(rows):
    plan=json.loads((RUN/'score-simulation-plan.json').read_text())
    arms=list(rows);indexed={a:{(r['opponent'],r['seed'],r['seat']):r['score'] for r in rs} for a,rs in rows.items()}
    assert all(indexed[a].keys()==indexed[arms[0]].keys() for a in arms)
    seeds=sorted({r['seed'] for r in rows[arms[0]]});rng=random.Random(plan['rng_seed'])
    b2=['bot2-face-proxy','bot2-trade-proxy'];astra=['astra-board-proxy','astra-sticky-proxy','astra-tempo-proxy']
    scores={a:[] for a in arms};caps={a:[0,0] for a in arms}
    for _ in range(plan['replicates']):
        selected=rng.choices(seeds,k=3);o2=rng.choice(b2);oa=rng.choice(astra)
        for arm in arms:
            ix=indexed[arm]
            w1=sum(ix['bot1-mage-proxy',s,seat] for s in selected for seat in (1,2))
            w2=sum(ix[o2,s,seat] for s in selected[:2] for seat in (1,2))
            wa=sum(ix[oa,s,seat] for s in selected[:2] for seat in (1,2))
            score=5+(3 if w1>=5 else 2 if w1>=3 else 1 if w1>=1 else 0)+(2 if w2>=3 else 1 if w2>=1 else 0)+wa
            scores[arm].append(score);caps[arm][0]+=w1>=5;caps[arm][1]+=w2>=3
    n=plan['replicates'];result={}
    for arm,values in scores.items():
        result[arm]={'frequency_score_above_10':sum(v>10 for v in values)/n,
            'mean_max_score_minus_10_zero':sum(max(v-10,0) for v in values)/n,
            'mean_score':sum(values)/n,'bot1_cap_frequency':caps[arm][0]/n,'bot2_cap_frequency':caps[arm][1]/n}
        result[arm]['paired_positive_score_delta']=sum(max(b-10,0)-max(a-10,0) for a,b in zip(scores['DARCL2'],values))/n
    return {'plan':plan,'results':result,'scope':'Paired local proxy interpretation; not calibrated to formal course scores.'}

def changed_lines(arm):
    base=HERE/'candidates/DARCL2';other=HERE/'candidates'/arm;n=0
    paths={p.relative_to(base) for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    paths|={p.relative_to(other) for p in other.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for relative in paths:
        a=(base/relative).read_text().splitlines() if (base/relative).exists() else []
        b=(other/relative).read_text().splitlines() if (other/relative).exists() else []
        n+=sum(1 for line in difflib.ndiff(a,b) if line.startswith(('- ','+ ')))
    return n

def choose():
    db=ledger.connect(RUN);assert not ledger.meta(db,'final_opened',False)
    plan=json.loads((RUN/'selection-plan.json').read_text());freeze=json.loads((RUN/'selection-freeze.json').read_text())
    assert sha(RUN/'score-simulation-plan.json')==plan['simulation_plan_sha256']
    reports={}
    for pool in ('core','guardrail'):
        b=plan[pool];assert db.execute('select status from batches where id=?',(b['batch'],)).fetchone()[0]=='done'
        reports[pool]=json.loads((RUN/'batches'/b['batch']/'report.json').read_text())
    reliable={a:all(all(not reports[p]['arms'][a]['all'][k] for k in ERRORS)
        and raw_reliability(db,plan[p]['batch'],a) for p in reports) for a in plan['arms']}
    assert reliable['DARCL2'],'Baseline execution invalid; inspect before selection'
    rows={a:[json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=?',(plan['core']['batch'],a))] for a in plan['arms']}
    simulation=simulate(rows);ledger.atomic(RUN/'selection-score-simulation.json',simulation)
    exact={a:sum(Fraction(r['score']) for r in rs if r['group']=='astra')/sum(r['group']=='astra' for r in rs) for a,rs in rows.items()}
    challengers=[a for a in plan['arms'][1:] if reliable[a]]
    best=max((exact[a] for a in challengers),default=Fraction(0))
    near=[a for a in challengers if best-exact[a]<=Fraction(1,200)]
    edits={a:changed_lines(a) for a in challengers}
    ranking=sorted(near,key=lambda a:(-simulation['results'][a]['mean_max_score_minus_10_zero'],edits[a],a))
    ranking+=sorted([a for a in challengers if a not in near],key=lambda a:(-exact[a],edits[a],a))
    selected=ranking[0] if ranking else 'DARCL2'
    result={'created':time.time(),'challenger':selected,'ranking':ranking,'reliability':reliable,
        'fingerprints':freeze['fingerprints'],'primary_rates':{a:float(v) for a,v in exact.items()},
        'exact_primary_fractions':{a:str(v) for a,v in exact.items()},'changed_lines':edits,
        'near_tie_candidates':near,'simulation':simulation,'plan':plan,'no_retuning':True}
    assert not (RUN/'selection-decision.json').exists()
    ledger.atomic(RUN/'selection-decision.json',result);ledger.setmeta(db,'selected_challenger',selected)
    print(json.dumps({k:v for k,v in result.items() if k not in ('simulation','plan')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','choose']);p.add_argument('--candidates',nargs='+')
    a=p.parse_args();prepare(a.candidates) if a.command=='prepare' else choose()
