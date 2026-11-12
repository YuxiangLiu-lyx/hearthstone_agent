"""Offline fault injection for bounded execution and durable retry accounting."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from development.benchmarks.run import fingerprint
from development.secret_hunter_mcgs import train
from development.secret_hunter_mcgs.supervision import GameProcess


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name)
        self.candidate = self.run / 'candidate'
        self.candidate.mkdir()
        (self.candidate / 'config.json').write_text('{}')
        self.db = train.connect(self.run)
        train.setmeta(self.db, 'candidates', {'test': {
            'path': str(self.candidate), 'sha256': fingerprint(self.candidate)}})
        train.setmeta(self.db, 'manifest', {
            'limits': {'seconds': 30, 'full_games': 10, 'continuations': 10},
            'reserved_final_games': 0})
        self.db.execute('INSERT INTO batches VALUES (?,?,?,?,?,?)',
                        ('test', 'development', '["test"]', 1, 1, 'pending'))
        self.db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,NULL)',
                        ('task', 'test', 'test', 'development', '{"name":"fake"}', 1, 1, 'pending'))
        self.db.commit()
        self.args = argparse.Namespace(workers=1, game_timeout_seconds=.4,
                                       cli_game_timeout_seconds=.4, stop_grace_seconds=.2)
        self.processes = []
        train.STOP = False

    def tearDown(self):
        for p in self.processes:
            if p.process.poll() is None:
                p.close()
        train.STOP = False
        self.db.close()
        self.temp.cleanup()

    def launch(self, script):
        def factory(command, cwd, log_path):
            p = GameProcess([sys.executable, '-c', script, command[-1]], cwd, log_path)
            self.processes.append(p)
            return p
        return patch.object(train, 'GameProcess', factory)

    def run_arm(self):
        train.run_arm(self.db, self.run, 'test', 'test', self.args)

    def test_timeout_is_charged_and_retried_without_strategy_loss(self):
        start = time.monotonic()
        with self.launch('import time; time.sleep(60)'):
            self.run_arm()
        self.assertLess(time.monotonic() - start, 3)
        self.assertEqual([r[0] for r in self.db.execute('SELECT status FROM attempts')], ['timeout', 'timeout'])
        row = self.db.execute('SELECT status,result FROM tasks').fetchone()
        self.assertEqual(tuple(row), ('pending', None))
        self.assertFalse(train.analyze(self.db, self.run, 'test'))
        script = ('import json,sys; from pathlib import Path; '
                  'r=json.loads(Path(sys.argv[1]).read_text()); '
                  'Path(r["result_path"]).write_text(json.dumps('
                  '{"score":1,"seed":1,"seat":1,"opponent":"fake"}))')
        with self.launch(script):
            self.run_arm()
            self.run_arm()
        self.assertEqual(self.db.execute('SELECT count(*) FROM attempts').fetchone()[0], 3)
        self.assertEqual(json.loads(self.db.execute('SELECT result FROM tasks').fetchone()[0])['score'], 1)
        self.assertTrue(all(p.process.poll() is not None for p in self.processes))

    def test_stop_bounds_drain_and_preserves_pending_work(self):
        self.args.game_timeout_seconds = 60
        timer = threading.Timer(.2, lambda: setattr(train, 'STOP', True))
        start = time.monotonic()
        timer.start()
        try:
            with self.launch('import time; time.sleep(60)'):
                self.run_arm()
        finally:
            timer.join()
        self.assertLess(time.monotonic() - start, 2)
        self.assertEqual(self.db.execute('SELECT status FROM attempts').fetchone()[0], 'interrupted')
        self.assertEqual(self.db.execute('SELECT status FROM tasks').fetchone()[0], 'pending')

    def test_budget_expiry_terminates_inflight_game(self):
        manifest = train.meta(self.db, 'manifest')
        manifest['limits']['seconds'] = .3
        train.setmeta(self.db, 'manifest', manifest)
        self.args.game_timeout_seconds = 60
        with self.launch('import time; time.sleep(60)'):
            self.run_arm()
        self.assertEqual(self.db.execute('SELECT status FROM attempts').fetchone()[0], 'budget_expired')
        self.assertIsNone(self.db.execute('SELECT result FROM tasks').fetchone()[0])

    def test_close_kills_cli_descendants(self):
        pid_path = self.run / 'grandchild.pid'
        script = ('import subprocess,sys,time; from pathlib import Path; '
                  'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
                  'Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)')
        p = GameProcess([sys.executable, '-c', script, str(pid_path)], self.run, self.run/'child.log')
        self.processes.append(p)
        deadline = time.monotonic() + 3
        while not pid_path.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(pid_path.exists())
        descendant = int(pid_path.read_text())
        p.close()
        state = subprocess.run(['ps', '-p', str(descendant), '-o', 'stat='],
                               capture_output=True, text=True).stdout.strip()
        self.assertTrue(not state or state.startswith('Z'), state)
        self.assertIsNotNone(p.process.returncode)


if __name__ == '__main__':
    unittest.main()
