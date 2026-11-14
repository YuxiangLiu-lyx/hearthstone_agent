"""Additional opponent/first-player pair reports and source-cluster intervals."""
import argparse
from collections import defaultdict
import json
import random
import statistics
from development.secret_hunter_long.study import RUN
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import paired,index

def clustered(a,b):
    aa,bb=index(a),index(b);assert aa.keys()==bb.keys()
    groups=defaultdict(list)
    for k in aa:groups[k[1]].append(k)
    # Ratio estimator handles unequal public-conditioned subset sizes and actual
    # first-player strata. Always resample entire source seeds, never games.
    cluster=[(sum(bb[k]['score']-aa[k]['score'] for k in ks),len(ks)) for ks in groups.values()]
    rng=random.Random(20261114);samples=[]
    for _ in range(10000):
        chosen=rng.choices(cluster,k=len(cluster));samples.append(sum(x[0] for x in chosen)/sum(x[1] for x in chosen))
    samples.sort();n=len(aa)
    return {'n_per_arm':n,'source_seed_groups':len(groups),'a_wins':sum(r['score'] for r in a),'b_wins':sum(r['score'] for r in b),
       'gain':sum(x[0] for x in cluster)/n,'gain_seed_cluster_95':[samples[250],samples[9749]],
       'rescued':sum(aa[k]['score']<bb[k]['score'] for k in aa),'lost_old_wins':sum(aa[k]['score']>bb[k]['score'] for k in aa),
       'estimator':'ratio of total paired differences to total games; whole-source-seed bootstrap'}

def run(batch,left,right):
    db=train.connect(RUN)
    rows=[[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done'",(batch,arm))] for arm in (left,right)]
    aa,bb=[index(r) for r in rows];assert aa.keys()==bb.keys()
    for k in aa:assert aa[k]['first_player']==bb[k]['first_player']
    result={'batch':batch,'left':left,'right':right,'all':paired(*rows),
       'primary':paired(*rows,groups=['astra','bot2'],equal_groups=True) if {'astra','bot2'}<={r['group'] for r in rows[0]} else None,
       'by_opponent':{name:clustered(*[[r for r in rs if r['opponent']==name] for rs in rows]) for name in sorted({r['opponent'] for r in rows[0]})},
       'by_actual_first':{str(first):clustered(*[[r for r in rs if (r['first_player']==r['seat'])==first] for rs in rows]) for first in (True,False)},
       'flips':[{'opponent':k[0],'seed':k[1],'seat':k[2],'a_win':aa[k]['score'],'b_win':bb[k]['score'],'a_game':aa[k]['game'],'b_game':bb[k]['game']} for k in sorted(aa) if aa[k]['score']!=bb[k]['score']]}
    train.atomic(RUN/'analysis'/f'{batch}-{left}-{right}-paired.json',result)
    print(json.dumps({'left':left,'right':right,'all':result['all'],'primary':result['primary']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('left');p.add_argument('right');a=p.parse_args();run(a.batch,a.left,a.right)
