"""Paired 2x2 terminal interaction; source-seed clusters remain intact."""
import argparse
from collections import defaultdict
import json
import random
import statistics

from development.secret_hunter_long.study import RUN
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import index


def run(batch, arms):
    db = train.connect(RUN)
    status = db.execute('select status from batches where id=?', (batch,)).fetchone()
    assert status and status['status'] == 'done'
    rows = [index([json.loads(r[0]) for r in db.execute(
        "select result from tasks where batch=? and candidate=? and status='done'", (batch, arm))]) for arm in arms]
    keys = set(rows[0])
    assert all(set(r) == keys for r in rows) and keys
    assert all(not r[k].get('harness_error') for r in rows for k in keys)
    outcomes = {}
    for label, groups in [('all', None), ('primary', ('astra', 'bot2'))]:
        by_seed = defaultdict(lambda: defaultdict(list))
        for key in keys:
            family = rows[0][key]['group']
            if groups and family not in groups:
                continue
            scores = [r[key]['score'] for r in rows]
            interaction = scores[3] - scores[1] - scores[2] + scores[0]
            by_seed[key[1]][family if groups else 'all'].append(interaction)
        values = [statistics.mean(statistics.mean(xs) for xs in families.values()) for families in by_seed.values()]
        rng = random.Random(20261114)
        samples = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(10000))
        outcomes[label] = {'source_seed_groups': len(values), 'interaction_gain': statistics.mean(values),
                           'interaction_seed_cluster_95': [samples[250], samples[9749]]}
    result = {'batch': batch, 'arms_in_order_base_M_T_MT': arms,
              'formula': 'win(M+T) - win(M) - win(T) + win(base)', 'outcomes': outcomes,
              'scope': 'Descriptive paired factorial interaction on development seeds; not a promotion test.'}
    path = RUN / 'analysis' / (batch + '-' + '-'.join(arms) + '-factorial.json')
    train.atomic(path, result)
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('batch')
    parser.add_argument('arms', nargs=4)
    args = parser.parse_args()
    run(args.batch, args.arms)
