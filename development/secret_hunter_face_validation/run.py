"""Run one preregistered frozen arm with isolated workers and a separate ledger."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json

from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check
from development.secret_hunter_program.common import ROOT, sha, write
from development.teacher_eval.run import worker, summarize, snapshot
from .accounting import reserve, finish, fail

D = ROOT / 'docs/secret_hunter_face_validation'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['Y1', 'F2'], required=True)
    parser.add_argument('--population', choices=['core', 'guardrail'], required=True)
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    assert 1 <= args.workers <= 6
    plan = json.loads((D / 'plan.json').read_text())
    frozen = json.loads((D / 'freeze.json').read_text())
    assert sha(D / 'plan.json') == frozen['plan_sha256']
    assert sha(ROOT / frozen['old_budget_path']) == frozen['old_budget_sha256']
    source = ROOT / plan['arms'][args.arm]
    check(source)
    assert fingerprint(source) == frozen['source_hashes'][args.arm]
    popfile = ROOT / f'development/teacher_eval/{args.population}.json'
    population = json.loads(popfile.read_text())
    popfreeze = frozen['populations'][args.population]
    assert sha(popfile) == popfreeze['sha256']
    assert snapshot(population) == popfreeze['opponents']
    schedule = plan['schedules'][args.population]
    name = f'{args.arm.lower()}-{args.population}'
    destination = ROOT / 'experiments' / f'secret-hunter-face-validation-{name}'
    assert not destination.exists(), 'Never overwrite or silently rerun confirmation games'
    n = schedule['games_per_arm']
    assert n == len(population) * 2 * schedule['seeds']
    reserve(name, full=n, final=True, seconds=600)
    try:
        destination.mkdir()
        manifest = {**vars(args), **schedule, 'candidate': plan['arms'][args.arm],
                    'candidate_sha256': fingerprint(source), 'population_sha256': sha(popfile),
                    'opponent_versions': snapshot(population), 'population': population,
                    'planned_games': n, 'split': 'confirmation', 'freeze_sha256': sha(D / 'freeze.json')}
        write(destination / 'config.json', manifest)
        tasks = [(str(source), opponent, seed, seat, str(destination), 'python')
                 for opponent in population
                 for seed in range(schedule['start'], schedule['start'] + schedule['seeds'])
                 for seat in (1, 2)]
        rows = []
        with ProcessPoolExecutor(max_workers=args.workers) as pool, (destination / 'results.jsonl').open('w') as out:
            futures = [pool.submit(worker, task) for task in tasks]
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                out.write(json.dumps(row) + '\n')
                out.flush()
                if len(rows) % 48 == 0:
                    print(name, len(rows), n, flush=True)
        assert len({(r['opponent'], r['seed'], r['seat']) for r in rows}) == n
        assert fingerprint(source) == manifest['candidate_sha256']
        assert snapshot(population) == popfreeze['opponents']
        report = summarize(rows)
        groups = report['by_group']
        report['primary'] = (.5 * groups['astra']['win_rate'] + .5 * groups['bot2']['win_rate']
                             if 'astra' in groups else None)
        report['both_sides_illegal'] = sum(sum(r['result']['illegal_counts'].values()) for r in rows)
        report['both_sides_timeouts'] = sum(sum(r['result']['timeouts'].values()) for r in rows)
        write(destination / 'summary.json', report)
        check(source)
        finish(name, completed=len(rows), wins=report['all']['wins'])
        print(json.dumps({'name': name, 'all': report['all'], 'primary': report['primary'],
                          'latency': report['latency_s']}), flush=True)
    except BaseException as exc:
        fail(name, repr(exc))
        raise


if __name__ == '__main__':
    main()
