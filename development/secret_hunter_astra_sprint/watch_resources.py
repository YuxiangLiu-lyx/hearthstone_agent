"""Run only preregistered fixed-state resource checks until recovery or cutoff."""
import datetime
import json
import os
import subprocess
import sys
import time
from development.secret_hunter_astra_sprint.study import ROOT, RUN
from development.secret_hunter_astra_sprint import ledger


def main():
    plan = json.loads((RUN / 'resource-recovery-plan.json').read_text())
    cutoff = datetime.datetime.fromisoformat(plan['watch_until_utc']).timestamp()
    samples = [json.loads(p.read_text()) for p in RUN.glob('resource-probe-health-*.json')]
    due = max(s['created'] for s in samples) + plan['health_interval_seconds']
    record = {'pid': os.getpid(), 'started': time.time(), 'cutoff': cutoff, 'events': [], 'status': 'watching'}
    output = RUN / 'resource-watch.json'
    ledger.atomic(output, record)
    while time.time() < cutoff:
        if time.time() < due:
            time.sleep(min(15, due - time.time(), max(.01, cutoff - time.time())))
            continue
        label = 'health-' + datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')
        command = [sys.executable, '-m', 'development.secret_hunter_astra_sprint.resource_probe',
                   '--label', label, '--workers', '3', '--include-complex']
        with (RUN / (label + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        assert result.returncode == 0, label
        health = json.loads((RUN / ('resource-probe-' + label + '.json')).read_text())
        summary = health['summaries'][0]
        recovered = (summary['calls'] == summary['matches_original_action'] == 16
                     and not any(summary[k] for k in ('invalid', 'fallbacks', 'over_2s')))
        event = {'file': 'resource-probe-' + label + '.json', 'created': health['created'],
                 'summary': summary, 'health_gate_passed': recovered}
        record['events'].append(event)
        ledger.atomic(output, record)
        print(json.dumps(event), flush=True)
        if recovered:
            record['status'] = 'health_gate_passed_requires_capacity_pilot'
            break
        due = health['created'] + plan['health_interval_seconds']
    else:
        record['status'] = 'watch_window_expired'
    record['finished'] = time.time()
    ledger.atomic(output, record)
    print(json.dumps({'status': record['status']}), flush=True)


if __name__ == '__main__':
    main()
