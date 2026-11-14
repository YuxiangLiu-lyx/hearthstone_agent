"""Exploratory aggregation of disjoint completed development seed cohorts."""
import argparse
import json
from development.secret_hunter_long.study import RUN
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import paired,index
from development.secret_hunter_long.comparisons import clustered

def main():
    p=argparse.ArgumentParser();p.add_argument('left');p.add_argument('right');p.add_argument('--batches',nargs='+',required=True);a=p.parse_args()
    db=train.connect(RUN);values={arm:[] for arm in (a.left,a.right)};seen=set()
    for batch in a.batches:
        b=db.execute('select * from batches where id=?',(batch,)).fetchone()
        assert b and b['status']=='done' and b['phase'] in ('development','cli_development')
        assert b['start']<51500000,'No selection/final data in exploratory development aggregate'
        local={}
        for arm in values:
            local[arm]=[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done'",(batch,arm))]
            assert len(local[arm])==b['seeds']*12 and all(not r.get('harness_error') for r in local[arm])
        keys=set(index(local[a.left]));assert keys==set(index(local[a.right])) and not seen&keys
        assert not ({k[1] for k in seen}&{k[1] for k in keys}),'Source seed groups must be disjoint across batches'
        seen|=keys
        for arm in values:values[arm]+=local[arm]
    left,right=values[a.left],values[a.right]
    result={'left':a.left,'right':a.right,'batches':a.batches,'all':paired(left,right),
       'primary':paired(left,right,groups=['astra','bot2'],equal_groups=True),
       'by_family':{g:paired(left,right,groups=[g]) for g in ('astra','bot2','bot1')},
       'by_actual_first':{str(first):clustered(*[[r for r in rows if (r['first_player']==r['seat'])==first] for rows in (left,right)]) for first in (True,False)},
       'scope':'Adaptive development evidence only, not an independent promotion test. Every cohort repeats both parents; all source seeds are distinct.'}
    path=RUN/'analysis'/('combined-'+a.left+'-'+a.right+'.json');train.atomic(path,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('by_family','by_actual_first')}))

if __name__=='__main__':main()
