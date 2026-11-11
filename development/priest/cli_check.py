"""Measure fresh CLI invocations on evenly spaced recorded states, checking legality."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from development.face_hunter.report import observations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run"); p.add_argument("--out", required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root/"control_priest/scripts"))
    from actions import legal
    run = Path(args.run); pool = []
    for game in json.loads((run/"metrics.json").read_text())["results"]:
        pool.extend(r["state"] for r in observations(run/"games"/game["game_id"], game["candidate_seat"]))
    sample = [pool[i*(len(pool)-1)//99] for i in range(100)]
    elapsed, failures = [], []
    with tempfile.TemporaryDirectory() as td:
        state_path = Path(td)/"state.json"
        for state in sample:
            state_path.write_text(json.dumps(state))
            start = time.perf_counter()
            result = subprocess.run([sys.executable, str(root/"control_priest/scripts/decide.py"), str(state_path)],
                                    capture_output=True, text=True, timeout=8)
            elapsed.append(time.perf_counter()-start)
            try:
                response = json.loads(result.stdout)
                ok = result.returncode == 0 and not result.stderr and response["seq"] == state["seq"] and legal(state, response["action"])
            except (ValueError, KeyError):
                ok = False
            if not ok:
                failures.append({"seq": state["seq"], "stdout": result.stdout, "stderr": result.stderr})
    output = {"states": len(sample), "mean_s": statistics.mean(elapsed), "p99_s": sorted(elapsed)[98],
              "max_s": max(elapsed), "failures": failures,
              "scope": "Fresh watchdog CLI on recorded public states, including recorded temporary-control annotation; exact bounded-search action identity is not required."}
    Path(args.out).write_text(json.dumps(output, indent=2)+"\n")
    print(json.dumps(output, indent=2))
    assert not failures


if __name__ == "__main__":
    main()
