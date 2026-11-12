"""Real matches with a fresh supervised CLI invocation for every atomic decision."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from hs_arena.agents.base import Decision
from development.secret_hunter_tactics.run import ScriptPlayer


class CLIPlayer(ScriptPlayer):
    def __init__(self, candidate):
        super().__init__(candidate)
        self.temp = tempfile.TemporaryDirectory(prefix='krush-cli-')
        self.root = Path(self.temp.name) / 'skill'
        shutil.copytree(candidate, self.root, ignore=shutil.ignore_patterns('__pycache__', 'game', 'scratch'))
        (self.root / 'game').mkdir()

    def decide(self, state):
        from state_features import with_public_history
        from action_validator import legal
        self.history.extend(state.get('events', []))
        public = with_public_history(state, self.history)
        (self.root / 'game/state.json').write_text(json.dumps(state))
        (self.root / 'game/history.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.history))
        start = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, 'scripts/decide.py'], cwd=self.root,
                                  capture_output=True, text=True, timeout=2.1, check=True)
            answer = json.loads(proc.stdout)
            action = answer['action']
            elapsed = time.monotonic()-start
            assert answer['seq'] == state['seq'] and legal(state, action), answer
            record = json.loads((self.root/'scratch/decisions.jsonl').read_text().splitlines()[-1])
            info = dict(record['info'])
            if record.get('worker_error'):
                info['error'] = record['worker_error']
            self.log.write(json.dumps({'state':public,'action':action,'info':info,
                                       'elapsed_s':elapsed,'execution':'full_cli'})+'\n')
            if elapsed > 2:
                return Decision('timeout', message='Full CLI exceeded the internal 2-second ceiling')
            return Decision('action', action)
        except subprocess.TimeoutExpired:
            self.log.write(json.dumps({'state':public,'action':None,'info':{'error':'cli_timeout'},
                                       'elapsed_s':time.monotonic()-start})+'\n')
            return Decision('timeout')

    def stop(self):
        super().stop()
        self.temp.cleanup()


def worker(task):
    # One arm per fresh process pool; no frozen harness source is modified.
    import development.secret_hunter_tactics.run as harness
    from development.teacher_eval.run import worker as play
    previous = harness.ScriptPlayer
    harness.ScriptPlayer = CLIPlayer
    try:
        row = play(task)
        row['execution'] = 'full_cli'
        return row
    finally:
        harness.ScriptPlayer = previous
