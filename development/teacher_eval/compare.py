"""Strict paired comparisons with resampling by shared seed (both seats/all opponents)."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from development.secret_hunter_program.common import ROOT, write


def index(rows):
    result={}
    for row in rows:
        key=(row['opponent'],row['seed'],row['seat'])
        if key in result:
            raise ValueError(f'Duplicate pair: {key}')
        if row.get('harness_error'):
            raise ValueError(f'Invalid game: {key}')
        result[key]=row
    return result


def paired(a,b,groups=None,equal_groups=False):
    a,b=index(a),index(b)
    if a.keys()!=b.keys():
        raise ValueError('Paired game sets differ; never silently drop missing games')
    keys=[k for k in sorted(a) if groups is None or a[k]['group'] in groups]
    if not keys:
        raise ValueError('Empty comparison')
    for k in keys:
        if a[k]['group']!=b[k]['group']:
            raise ValueError('Opponent group changed between arms')
    by_seed=defaultdict(list)
    for k in keys:
        by_seed[k[1]].append(k)
    def rate(mapping, selected):
        if equal_groups:
            families=defaultdict(list)
            for k in selected:families[mapping[k]['group']].append(mapping[k]['score'])
            return statistics.mean(statistics.mean(v) for v in families.values())
        return statistics.mean(mapping[k]['score'] for k in selected)
    # Each cluster has exactly the same balanced design. Compute seed deltas once.
    designs={tuple(sorted((k[0],k[2]) for k in ks)) for ks in by_seed.values()}
    if len(designs)!=1:
        raise ValueError('Unbalanced seeds; use a weighted cluster estimator explicitly')
    deltas=[rate(b,ks)-rate(a,ks) for _,ks in sorted(by_seed.items())]
    rng=random.Random(20261111)
    samples=sorted(statistics.mean(rng.choices(deltas,k=len(deltas))) for _ in range(10000))
    return {'n_per_arm':len(keys),'seed_clusters':len(deltas),
            'a_wins':sum(a[k]['score'] for k in keys),'b_wins':sum(b[k]['score'] for k in keys),
            'a_rate':rate(a,keys),'b_rate':rate(b,keys),'gain':rate(b,keys)-rate(a,keys),
            'gain_seed_cluster_95':[samples[250],samples[9749]],
            'a_only_wins':sum(a[k]['score']>b[k]['score'] for k in keys),
            'b_only_wins':sum(b[k]['score']>a[k]['score'] for k in keys),
            'weighting':'equal family macro' if equal_groups else 'equal games',
            'limitation':'Fixed local proxies, not real Astra; few seed clusters and adaptive development selection limit inference.'}


def compare(left,right):
    configs=[json.loads((p/'config.json').read_text()) for p in (left,right)]
    for field in ('population_sha256','opponent_versions','start','seeds','split'):
        if configs[0][field]!=configs[1][field]:raise ValueError(f'Mismatched {field}')
    rows=[[json.loads(line) for line in (p/'results.jsonl').read_text().splitlines()] for p in (left,right)]
    if any(len(r)!=c['planned_games'] for r,c in zip(rows,configs)):
        raise ValueError('Incomplete scheduled run')
    groups=sorted({r['group'] for r in rows[0]})
    out={'baseline':str(left.relative_to(ROOT)),'candidate':str(right.relative_to(ROOT)),
         'all':paired(*rows),'by_group':{g:paired(*rows,groups=[g]) for g in groups}}
    if {'astra','bot2'}<=set(groups):
        out['hard_family_macro']=paired(*rows,groups=['astra','bot2'],equal_groups=True)
        out['teacher_family_macro']=paired(*rows,equal_groups=True)
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('baseline');parser.add_argument('candidate')
    parser.add_argument('--out',required=True);args=parser.parse_args()
    report=compare(ROOT/args.baseline,ROOT/args.candidate)
    write(ROOT/args.out,report)
    print(json.dumps(report,indent=2))
