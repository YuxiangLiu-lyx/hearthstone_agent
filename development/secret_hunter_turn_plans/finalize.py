"""Strict completed-arm final estimates; no strategy selection or mutation."""
import json
import sqlite3
import time

from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import RUN,ROOT
from development.teacher_eval.compare import paired
from development.teacher_eval.run import summarize,snapshot


def main():
    db=sqlite3.connect(f'file:{RUN}/ledger.sqlite?mode=ro',uri=True)
    freeze=json.loads((RUN/'final-freeze.json').read_text())
    manifest=json.loads((RUN/'manifest.json').read_text())
    for name,digest in freeze['fingerprints'].items():
        assert fingerprint(Y1 if name=='Y1' else HERE/'candidates'/name)==digest,name
    for path,digest in manifest['protected'].items():assert sha(ROOT/path)==digest,path
    for path,versions in manifest['opponents'].items():
        assert snapshot(json.loads((ROOT/path).read_text()))==versions,path
    result={'scope':'Frozen local proxy opponents; full Python CLI at every atomic decision.',
            'freeze':freeze,'created':time.time(),'batches':{}}
    for batch,expected in [('final-core',480),('final-guard',224)]:
        assert not db.execute("select 1 from tasks where batch=? and status!='done' limit 1",(batch,)).fetchone(),batch
        arms={}
        for arm in freeze['arms']:
            arms[arm]=[json.loads(r[0]) for r in db.execute(
                "select result from tasks where batch=? and candidate=? and status='done' order by seed,opponent,seat",(batch,arm))]
            assert len(arms[arm])==expected,(batch,arm,len(arms[arm]))
            assert all(r['execution']=='full_cli' and not r.get('harness_error') for r in arms[arm])
        comparisons={}
        for baseline,candidate in [('Y1','engine-trap-v2'),('Y1','E2-finish-minions'),('engine-trap-v2','E2-finish-minions')]:
            a,b=arms[baseline],arms[candidate]
            pair={'all':paired(a,b),'by_opponent':{}}
            for name in sorted({r['opponent'] for r in a}):
                pair['by_opponent'][name]=paired([r for r in a if r['opponent']==name],
                                                  [r for r in b if r['opponent']==name])
            if batch=='final-core':
                pair['primary']=paired(a,b,groups=['astra','bot2'],equal_groups=True)
                pair['astra']=paired(a,b,groups=['astra'])
                pair['bot2']=paired(a,b,groups=['bot2'])
                pair['greedy']=paired(a,b,groups=['bot1'])
            comparisons[baseline+' -> '+candidate]=pair
        result['batches'][batch]={'complete':True,'arms':{k:summarize(v) for k,v in arms.items()},
                                 'comparisons':comparisons,
                                 'full_cli_calls':{k:sum(len(r['decision_times']) for r in v) for k,v in arms.items()}}
    result['budget']={'elapsed_wall_s':time.time()-manifest['created'],
        'full_game_attempts':db.execute('select count(*) from attempts').fetchone()[0],
        'attempt_status':dict(db.execute('select status,count(*) from attempts group by status')),
        'completed_full_games':db.execute("select count(*) from tasks where status='done'").fetchone()[0]}
    output=ROOT/'docs/secret_hunter_turn_plans/final-results.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({batch:{name:[s['all']['wins'],s['all']['n']] for name,s in data['arms'].items()}
                      for batch,data in result['batches'].items()},indent=2))


if __name__=='__main__':main()
