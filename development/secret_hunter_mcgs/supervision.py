"""Bounded offline game processes, including their CLI descendants."""
import os
from pathlib import Path
import signal
import subprocess
import time


class GameProcess:
    def __init__(self, command, cwd, log_path):
        self.log = Path(log_path).open('ab')
        self.started = time.monotonic()
        try:
            self.process = subprocess.Popen(
                command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=self.log,
                stderr=subprocess.STDOUT, start_new_session=True)
        except BaseException:
            self.log.close()
            raise

    def close(self):
        # Each game owns a new session. This also removes a CLI grandchild that
        # outlived its immediate parent; it never signals the trainer's group.
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=3)
        finally:
            self.log.close()
