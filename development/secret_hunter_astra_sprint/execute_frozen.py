"""Run both frozen CLI pools in order; never choose or modify a candidate."""
import json
import subprocess
import sys
import time

from development.secret_hunter_astra_sprint.study import ROOT, RUN
from development.secret_hunter_astra_sprint import ledger as train
from development.secret_hunter_program.common import sha


def main():
    freeze_path = RUN / 'final-freeze.json'
    freeze = json.loads(freeze_path.read_text())
    selection = json.loads((RUN / 'selection-plan.json').read_text())
    commands = []
    for pool, key, batch in [('core', 'final_core', 'final-core'), ('guardrail', 'final_guard', 'final-guard')]:
        lo, hi = freeze['seeds'][key]
        commands.append(['development.secret_hunter_astra_sprint.study', 'run', '--batch', batch,
                         '--arms', *freeze['arms'], '--start', str(lo), '--seeds', str(hi - lo + 1),
                         '--pool', pool, '--workers', str(selection['workers']), '--final'])
    path = RUN / 'final-execution-plan.json'
    plan = {'freeze_sha256': sha(freeze_path), 'commands': commands}
    if path.exists():
        saved = json.loads(path.read_text())
        assert all(saved[k] == v for k, v in plan.items())
    else:
        train.atomic(path, {'created': time.time(), **plan})
    digest = sha(path)
    db = train.connect(RUN)
    for command in commands:
        assert sha(path) == digest and sha(freeze_path) == plan['freeze_sha256']
        print(json.dumps({'frozen_command': command}), flush=True)
        with (RUN / (command[command.index('--batch') + 1] + '.closed.log')).open('a') as log:
            subprocess.run([sys.executable, '-m', *command], cwd=ROOT, check=True, stdout=log, stderr=subprocess.STDOUT)
        batch = command[command.index('--batch') + 1]
        row = db.execute('select status from batches where id=?', (batch,)).fetchone()
        assert row and row['status'] == 'done', ('Incomplete frozen pool; resume the same plan', batch)
    print(json.dumps({'frozen_plan_complete': str(path)}), flush=True)


if __name__ == '__main__':
    main()
