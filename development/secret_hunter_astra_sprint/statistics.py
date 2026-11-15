"""Strict DARCL2 pairs, source-seed intervals, and the Astra sprint estimand."""
from collections import defaultdict
import json
import random

from development.teacher_eval.compare import index
from development.secret_hunter_astra_sprint import ledger as train


def paired(left, right):
    a, b = index(left), index(right)
    assert a.keys() == b.keys() and a
    clusters = defaultdict(list)
    for key in sorted(a):
        assert a[key]['first_player'] == b[key]['first_player']
        assert a[key]['group'] == b[key]['group']
        clusters[key[1]].append(key)
    values = [(sum(b[k]['score'] - a[k]['score'] for k in keys), len(keys))
              for keys in clusters.values()]
    rng = random.Random(20261115)
    samples = []
    for _ in range(10000):
        selected = rng.choices(values, k=len(values))
        samples.append(sum(v[0] for v in selected) / sum(v[1] for v in selected))
    samples.sort()
    n = len(a)
    aw, bw = sum(r['score'] for r in a.values()), sum(r['score'] for r in b.values())
    return {'n_per_arm': n, 'seed_clusters': len(values), 'a_wins': aw, 'b_wins': bw,
            'a_rate': aw / n, 'b_rate': bw / n, 'gain': (bw - aw) / n,
            'gain_seed_cluster_95': [samples[250], samples[9749]],
            'gain_one_sided_90_lower': samples[1000],
            'a_only_wins': sum(a[k]['score'] > b[k]['score'] for k in a),
            'b_only_wins': sum(a[k]['score'] < b[k]['score'] for k in a),
            'weighting': 'equal games; balanced three-Astra design equals equal proxy macro',
            'bootstrap': '10000 resamples of complete source seeds; ratio for unequal strata; fixed RNG 20261115',
            'scope': 'Local fixed proxies only; intervals from adaptive development are descriptive.'}


def compare(left, right):
    result = {'all': paired(left, right)}
    groups = sorted({r['group'] for r in left})
    result['by_group'] = {g: paired([r for r in left if r['group'] == g],
                                     [r for r in right if r['group'] == g]) for g in groups}
    opponents = sorted({r['opponent'] for r in left})
    result['by_opponent'] = {o: paired([r for r in left if r['opponent'] == o],
                                        [r for r in right if r['opponent'] == o]) for o in opponents}
    result['by_actual_first'] = {str(v): paired([r for r in left if (r['first_player'] == r['seat']) == v],
                                                [r for r in right if (r['first_player'] == r['seat']) == v])
                                 for v in (True, False)}
    result['by_seat'] = {str(v): paired([r for r in left if r['seat'] == v],
                                        [r for r in right if r['seat'] == v]) for v in (1, 2)}
    result['primary'] = result['by_group'].get('astra')
    if result['primary']:
        counts = {o: sum(r['opponent'] == o for r in left) for o in opponents if o.startswith('astra-')}
        assert len(counts) == 3 and len(set(counts.values())) == 1
        al=[r for r in left if r['group']=='astra'];bl=[r for r in right if r['group']=='astra']
        result['primary_by_seat']={str(v):paired([r for r in al if r['seat']==v],[r for r in bl if r['seat']==v]) for v in (1,2)}
        result['primary_by_actual_first']={str(v):paired([r for r in al if (r['first_player']==r['seat'])==v],
            [r for r in bl if (r['first_player']==r['seat'])==v]) for v in (True,False)}
    aa, bb = index(left), index(right)
    result['flips'] = [{'opponent': k[0], 'seed': k[1], 'seat': k[2],
                        'a_win': aa[k]['score'], 'b_win': bb[k]['score'],
                        'a_game': aa[k]['game'], 'b_game': bb[k]['game']}
                       for k in sorted(aa) if aa[k]['score'] != bb[k]['score']]
    return result


def analyze(db, run, batch):
    from development.secret_hunter_astra_sprint.provenance import archive_code
    from development.secret_hunter_astra_sprint.study import ROOT
    from development.secret_hunter_program.common import sha
    item = db.execute('select * from batches where id=?', (batch,)).fetchone()
    assert item
    if db.execute("select count(*) from tasks where batch=? and status!='done'", (batch,)).fetchone()[0]:
        return False
    if item['phase'].startswith('final'):
        freeze=json.loads((run/'final-freeze.json').read_text())
        assert all(sha(ROOT/path)==digest for path,digest in freeze['analysis_sources'].items())
        for pool in ('final-core', 'final-guard'):
            record = db.execute('select status from batches where id=?', (pool,)).fetchone()
            assert record and record['status'] == 'done', 'Do not open outcomes until both final pools finish'
    arms = json.loads(item['arms'])
    rows = {a: [json.loads(r[0]) for r in db.execute('select result from tasks where batch=? and candidate=? order by seed,opponent,seat', (batch, a))]
            for a in arms}
    report = {'batch': batch, 'phase': item['phase'], 'start': item['start'], 'seed_groups': item['seeds'],
              'baseline': arms[0], 'arms': {}, 'comparisons': {}, 'primary': 'three Astra proxies equally weighted'}
    report['analysis_source_archive']=archive_code(run,['development/secret_hunter_astra_sprint/statistics.py'])
    assert arms[0] == 'DARCL2'
    for arm, games in rows.items():
        report['arms'][arm] = train.summarize(games)
        folder = run / 'batches' / batch / arm
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'results.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in games))
    if not any(r.get('harness_error') for games in rows.values() for r in games):
        for arm in arms[1:]:
            report['comparisons'][arm] = compare(rows[arms[0]], rows[arm])
    train.atomic(run / 'batches' / batch / 'report.json', report)
    with db:
        db.execute("update batches set status='done' where id=?", (batch,))
    print(json.dumps({'batch_complete': batch, 'wins': {a: report['arms'][a]['all']['wins'] for a in arms}}), flush=True)
    return True
