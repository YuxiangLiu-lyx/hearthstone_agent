"""Collect final statistics without replaying games or changing selection."""
import json
from pathlib import Path

from development.secret_hunter_long.study import ROOT, RUN
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import quantiles, sha


def read(path):
    return json.loads(path.read_text())


def main():
    db = train.connect(RUN)
    recommendation = read(ROOT / 'docs/secret_hunter_long/recommendation.json')
    acceptance = read(RUN / 'final-acceptance.json')
    assert acceptance['passed']
    freeze = read(RUN / 'final-freeze.json')
    pools = {}
    for batch in ('final-core', 'final-guard'):
        assert db.execute('select status from batches where id=?', (batch,)).fetchone()[0] == 'done'
        path = RUN / 'batches' / batch / 'report.json'
        paired_path = RUN / 'analysis' / f'{batch}-B-{recommendation["challenger"]}-paired.json'
        actions = read(RUN / 'analysis' / f'{batch}-B-{recommendation["challenger"]}-actions.json')
        pools[batch] = {'report_sha256': sha(path), 'report': read(path),
                        'paired_sha256': sha(paired_path), 'paired': read(paired_path),
                        'actions': {k: v for k, v in actions.items() if k != 'examples'}}
    cli = {}
    for arm in freeze['arms']:
        rows = [json.loads(r[0]) for r in db.execute(
            "select result from tasks where phase in ('final_core','final_guard') and candidate=? and status='done'", (arm,))]
        runtime = read(ROOT / f'docs/secret_hunter_long/runtime-{arm}.json')
        cli[arm] = {'merged_final_pools': train.summarize(rows),
                    'cold_start': quantiles([r['elapsed_s'] for r in runtime['records'] if r['tag'] == 'cold']),
                    'runtime_ordinary': runtime['ordinary_latency_s'],
                    'runtime_including_injected_faults': runtime['all_including_fault_latency_s']}
    relay = {}
    for mode in ('luna', 'client'):
        records = [r for r in acceptance['records'] if r['mode'] == mode]
        internal, publication, outside = [], [], []
        for record in records:
            player = Path(record['game_path']) / f'p{record["seat"]}'
            decisions = [json.loads(line) for line in (player / 'seat/scratch/decisions.jsonl').read_text().splitlines()]
            normal = {d['seq']: d for d in decisions if d['phase'] != 'deck_submission'}
            internal.extend(d['elapsed_s'] for d in normal.values())
            calls = [json.loads(line) for line in (player / 'seat/mcp_calls.jsonl').read_text().splitlines()]
            for call in calls:
                if call['tool'] != 'act' or call['arguments']['seq'] not in normal:
                    continue
                seq = call['arguments']['seq']
                elapsed = call['time'] - (player / f'decisions/{seq:05d}.state.json').stat().st_mtime
                publication.append(elapsed)
                outside.append(elapsed - normal[seq]['elapsed_s'])
        relay[mode] = {'games': len(records), 'act_calls': sum(r['act_calls'] for r in records),
                       'actual_first': sum(r['result']['first_player'] == r['seat'] for r in records),
                       'internal_program_latency_s': quantiles(internal),
                       'publication_to_act_latency_s': quantiles(publication),
                       'outside_internal_program_latency_s': quantiles(outside)}
    result = {'recommended': recommendation['recommended'], 'freeze': freeze,
              'recommendation': recommendation, 'pools': pools, 'full_cli': cli, 'relay': relay,
              'latency_method': 'Recompute quantiles from pooled raw decision samples; never average per-game quantiles.',
              'timing_scope': 'Full CLI includes process startup; relay internal excludes it. Publication-to-act includes model/shell/startup/transport and is not pure network time.'}
    train.atomic(RUN / 'final-validation.json', result)
    train.atomic(ROOT / 'docs/secret_hunter_long/final-validation.json', result)
    print(json.dumps({'recommended': result['recommended'], 'full_cli': {k: v['merged_final_pools']['latency_s'] for k, v in cli.items()}, 'relay': relay}))


if __name__ == '__main__':
    main()
