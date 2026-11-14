"""Explicit ratio-of-totals cluster bootstrap for conditioned, uneven samples."""
from collections import defaultdict
import json
import random
from development.teacher_eval.compare import index
from development.teacher_eval.run import summarize
from development.secret_hunter_mcgs import train

def weighted_pair(left,right,keys=None):
    a,b=index(left),index(right);assert a.keys()==b.keys()
    keys=set(keys) if keys is not None else set(a);assert keys<=a.keys()
    grouped=defaultdict(list)
    for k in sorted(keys):grouped[k[1]].append(k)
    totals=[(sum(b[k]['score']-a[k]['score'] for k in ks),len(ks)) for ks in grouped.values()]
    rng=random.Random(20261113);draws=[]
    for _ in range(10000):
        sample=rng.choices(totals,k=len(totals));draws.append(sum(x[0] for x in sample)/sum(x[1] for x in sample))
    draws.sort();n=len(keys)
    return {'n_per_arm':n,'seed_clusters':len(totals),'a_wins':sum(a[k]['score'] for k in keys),
            'b_wins':sum(b[k]['score'] for k in keys),'gain':sum(x[0] for x in totals)/n,
            'gain_seed_cluster_95':[draws[250],draws[9749]],
            'a_only_wins':sum(a[k]['score']>b[k]['score'] for k in keys),
            'b_only_wins':sum(a[k]['score']<b[k]['score'] for k in keys),
            'weighting':'equal selected games; ratio of totals within bootstrapped whole source-seed clusters',
            'limitation':'Conditioned opening distribution, never a full-pool win rate.'}

def selected_report(db,run,batch,selection):
    b=db.execute('select * from batches where id=?',(batch,)).fetchone()
    if db.execute("select 1 from tasks where batch=? and status!='done'",(batch,)).fetchone():return
    arms=json.loads(b['arms']);rows={}
    for arm in arms:
        rows[arm]=[json.loads(x[0]) for x in db.execute('select result from tasks where batch=? and candidate=? order by seed,opponent,seat',(batch,arm))]
        path=run/'batches'/batch/arm/'results.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows[arm]))
    report={'batch':batch,'arms':{a:summarize(rs) for a,rs in rows.items()},'comparisons':{}}
    hit_path=selection.with_name(selection.stem+'-sampling.json')
    sampling=json.loads(hit_path.read_text())['records'] if hit_path.exists() else []
    hits={tuple(r['key']) for r in sampling if r['hit']}
    for arm in arms[1:]:
        report['comparisons'][arm]={'all_selected':weighted_pair(rows[arms[0]],rows[arm])}
        if hits:
            report['comparisons'][arm]['hit_only']=weighted_pair(rows[arms[0]],rows[arm],hits)
            report['comparisons'][arm]['hit_by_actual_first']={str(first):weighted_pair(rows[arms[0]],rows[arm],keys)
                for first in (True,False) if (keys:={tuple(r['key']) for r in sampling if r['hit'] and r['first']==first})}
        report['comparisons'][arm]['by_opponent']={name:weighted_pair(rows[arms[0]],rows[arm],
            [k for k in index(rows[arm]) if k[0]==name]) for name in sorted({r['opponent'] for r in rows[arm]})}
    train.atomic(run/'batches'/batch/'report.json',report)
    with db:db.execute("update batches set status='done' where id=?",(batch,))
    print(json.dumps({'batch_complete':batch,'wins':{a:[v['all']['wins'],v['all']['n']] for a,v in report['arms'].items()},'comparisons':report['comparisons']}),flush=True)
