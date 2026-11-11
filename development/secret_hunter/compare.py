"""Matched opponent/seed/seat outcomes with a seed-cluster bootstrap."""
import argparse
import json
from pathlib import Path
import random
from development.secret_hunter.audit import readlines
from development.secret_hunter.bootstrap import write


def compare(left,right):
    a={(r['opponent'],r['seed'],r['seat']):r for r in readlines(Path(left)/'results.jsonl')}
    b={(r['opponent'],r['seed'],r['seat']):r for r in readlines(Path(right)/'results.jsonl')}
    assert set(a)==set(b),'Unmatched comparison schedule'
    def group(keys):
        if not keys:return None
        seeds=sorted({k[1] for k in keys});delta={s:sum(b[k]['score']-a[k]['score'] for k in keys if k[1]==s)/sum(k[1]==s for k in keys) for s in seeds}
        rng=random.Random(910);boot=sorted(sum(delta[rng.choice(seeds)] for _ in seeds)/len(seeds) for _ in range(5000))
        return {'n_per_arm':len(keys),'a_wins':sum(a[k]['score'] for k in keys),'b_wins':sum(b[k]['score'] for k in keys),
                'gain':sum(b[k]['score']-a[k]['score'] for k in keys)/len(keys),
                'seed_clusters':len(seeds),'gain_seed_cluster_95':[boot[125],boot[4874]] if len(seeds)>=2 else None,
                'a_only_wins':sum(a[k]['score']>b[k]['score'] for k in keys),
                'b_only_wins':sum(b[k]['score']>a[k]['score'] for k in keys),
                'limitation':'Fixed opponents; fewer than 20 seed clusters give unstable intervals.'}
    return {'baseline':str(left),'candidate':str(right),'all':group(list(a)),
            'primary':group([k for k in a if k[0]!='official-mage']),
            'base':group([k for k in a if k[0]=='official-mage']),
            'by_opponent':{o:group([k for k in a if k[0]==o]) for o in sorted({k[0] for k in a})}}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('candidate');p.add_argument('--out',required=True);a=p.parse_args()
    r=compare(a.baseline,a.candidate);write(a.out,r);print(json.dumps({k:v for k,v in r.items() if k!='by_opponent'}))
