"""Read-only progress, capacity and execution metrics; never expose outcomes."""
import argparse
from collections import Counter
import datetime
import json
import sqlite3
import time
from zoneinfo import ZoneInfo
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_program.common import quantiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    args = parser.parse_args()
    db = sqlite3.connect((RUN / 'ledger.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    meta = {r['key']: json.loads(r['value']) for r in db.execute('select * from meta')}
    batch = db.execute('select * from batches where id=?', (args.batch,)).fetchone()
    assert batch
    progress = [dict(r) for r in db.execute('select candidate,status,count(*) as count from tasks where batch=? group by candidate,status', (args.batch,))]
    attempts = list(db.execute('select a.status,a.started,a.finished from attempts a join tasks t on t.key=a.task where t.batch=?', (args.batch,)))
    finished = [r for r in attempts if r['status'] == 'done']
    elapsed = max(r['finished'] for r in finished) - min(r['started'] for r in attempts) if finished else 0
    rate = len(finished) / elapsed * 60 if elapsed else None
    errors, timings = Counter(), []
    for row in db.execute("select result from tasks where batch=? and status='done'", (args.batch,)):
        result = json.loads(row[0])
        timings.extend(result['decision_times'])
        for key in ('harness_error', 'opponent_errors', 'policy_errors', 'fallbacks', 'over_2s', 'public_input_violations'):
            value = result.get(key, 0)
            errors[key] += len(value) if isinstance(value, list) else int(bool(value))
        for key in ('illegal_counts', 'restarts', 'timeouts'):
            errors[key] += sum(result['result'][key].values())
        errors['non_hero_death_terminal'] += result['result']['reason'] != 'hero_death'
    total = sum(r['count'] for r in progress)
    done = sum(r['count'] for r in progress if r['status'] == 'done')
    now = time.time()
    record = {'at_et': datetime.datetime.fromtimestamp(now, ZoneInfo('America/New_York')).isoformat(),
              'batch': args.batch, 'status': batch['status'], 'progress': progress,
              'done': done, 'total': total, 'attempt_status': dict(Counter(r['status'] for r in attempts)),
              'games_per_minute': rate, 'estimated_remaining_minutes': (total - done) / rate if rate else None,
              'execution_errors': dict(errors), 'full_cli_latency_s': quantiles(timings),
              'budget_full_used': db.execute('select count(*) from attempts').fetchone()[0] + db.execute('select count(*) from auxiliary_games').fetchone()[0],
              'budget_continuations_used': db.execute('select count(*) from cf_attempts').fetchone()[0],
              'deadline_remaining_minutes': (meta['manifest']['deadline'] - now) / 60,
              'selection_and_final_opened': [meta.get('selection_opened', False), meta.get('final_opened', False)],
              'scope': 'Execution and progress only; no wins, action choices or final outcomes inspected.'}
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
