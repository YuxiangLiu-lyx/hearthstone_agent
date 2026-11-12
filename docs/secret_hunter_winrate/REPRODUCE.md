# Reproduce the win-rate follow-up

Run from the repository root with the existing Python 3.11 environment and course `hs-arena==0.2.2`. Do not modify the installed engine, ordered deck or opponent pools. Local symlinks to the original workspace environment and course distribution are not part of the ZIP.

## Audit existing evidence

```sh
.venv/bin/python -m development.secret_hunter_winrate.verify
.venv/bin/python -m development.secret_hunter_winrate.analyze
.venv/bin/hs-arena validate development/secret_hunter_winrate/release/secret-hunter-winrate-w3 --no-game
```

The first two commands regenerate audit/analysis JSON from retained local logs. Normal-game observations and official-client workspaces are ignored by Git; raw per-game results, public first-divergence evidence, public replay witnesses, the earlier source-prefix archive, candidate code and the ZIP are committed. On a fresh clone, the stored audit/report can be inspected and the course source-prefix witness can be replayed without those ignored match logs. `analyze.py` and the client portion of `verify.py` require the original local game logs; this limitation is explicit.

Fresh-clone analysis of the committed result rows, without ignored match logs:

```sh
.venv/bin/python -m development.secret_hunter_winrate.analyze --metrics-only --out /tmp/winrate-metrics.json
shasum -a 256 dist/secret-hunter-krush-winrate-w3.zip
```

## Replay the course-engine witness

```sh
.venv/bin/python -m development.secret_hunter_winrate.witness \
  --candidate development/secret_hunter_winrate/candidates/W3 \
  --case 33 --name winrate-reproduce-w3-case33 \
  --out /tmp/winrate-reproduce-w3-case33.json
```

This reconstructs the public source prefix from `docs/secret_hunter_response/replay-prefixes.jsonl.gz`, validates the original public-state hash, and runs the frozen candidate for one legal turn. It spends a new short reservation, not a terminal game. Use a new unique ledger name for each attempt. Replace the candidate with `development/secret_hunter_response/candidates/Y1` and the name/output to reproduce the original Juggler line. Case 57 with candidate W2 reproduces buff-before-attack. These source cases are development evidence.

A direct cold CLI replay requires no engine transition:

```sh
.venv/bin/python - <<'PY'
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
source = Path('development/secret_hunter_winrate/release/secret-hunter-winrate-w3')
state = json.loads(Path('docs/secret_hunter_winrate/witness-w3.json').read_text())['initial_public_state']
with tempfile.TemporaryDirectory() as directory:
    skill = Path(directory)/'skill'
    shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__', 'game', 'scratch'))
    (skill/'game').mkdir()
    (skill/'game/state.json').write_text(json.dumps(state))
    subprocess.run([sys.executable, 'scripts/decide.py'], cwd=skill, check=True)
PY
```

Only a current legal first action is emitted. Subsequent actions require fresh observations. Time-limited searches may choose different legal traces across hardware or scheduling; hashes and observed outcome comparisons are retained rather than promising bitwise action determinism.

## Recorded experiment commands

These are the commands used, not permission to reset an exhausted ledger. The shared ledger is now at the authorized 16,000 full-attempt cap. A fresh full rerun requires an explicitly authorized additional budget and a separate attempt name/output; never reset the historical ledger or treat the opened final seeds as unseen validation.

```sh
.venv/bin/python -m development.secret_hunter_response.run --candidate development/secret_hunter_winrate/candidates/W1 --name winrate-w1-dev --start 960100 --seeds 8 --workers 6
.venv/bin/python -m development.secret_hunter_response.run --candidate development/secret_hunter_winrate/candidates/W2 --name winrate-w2-dev --start 960100 --seeds 8 --workers 6
.venv/bin/python -m development.secret_hunter_response.run --candidate development/secret_hunter_winrate/candidates/W3 --name winrate-w3-dev --start 960100 --seeds 8 --workers 6
.venv/bin/python -m development.secret_hunter_winrate.run --candidate development/secret_hunter_response/candidates/Y1 --name y1-final-core --start 981000 --seeds 40 --workers 6 --final
.venv/bin/python -m development.secret_hunter_winrate.run --candidate development/secret_hunter_winrate/candidates/W3 --name w3-final-core --start 981000 --seeds 40 --workers 6 --final
.venv/bin/python -m development.secret_hunter_winrate.run --candidate development/secret_hunter_response/candidates/Y1 --name y1-final-guard --population guardrail --start 982000 --seeds 2 --workers 6 --final
.venv/bin/python -m development.secret_hunter_winrate.run --candidate development/secret_hunter_winrate/candidates/W3 --name w3-final-guard --population guardrail --start 982000 --seeds 2 --workers 6 --final
.venv/bin/python -m development.secret_hunter_winrate.continuation_check
```

The runner validates frozen source hashes, opponent hashes, exact schedules, both seats, deck submission and row completeness. It precharges the shared atomic ledger before launching at most six workers. The original frozen Y1 96-game baseline was reused; no baseline rows were dropped.

## Artifact and reliability reproduction

`build.py` deterministically produces the saved ZIP from the frozen source; it deliberately refuses to overwrite an existing artifact. The manifest lists every member SHA-256. The ZIP can be independently extracted and validated without rebuilding it.

Recorded reliability commands:

```sh
.venv/bin/python -m development.secret_hunter_response.regression --candidate development/secret_hunter_winrate/candidates/W3 --out docs/secret_hunter_winrate/regression-w3.json
.venv/bin/python -m development.secret_hunter_response.runtime_checks --candidate development/secret_hunter_winrate/release/secret-hunter-winrate-w3 --out docs/secret_hunter_winrate/runtime-release.json
.venv/bin/python -m development.secret_hunter_response.fault_check --candidate development/secret_hunter_winrate/release/secret-hunter-winrate-w3 --name winrate-release-isolated-stale
.venv/bin/python -m development.secret_hunter_winrate.client_test
```

All old reservations and output paths are protected against reuse. The client smoke test runs two existing Greedy games through the official no-model client, not a model host. Client seed block: 984000–984001. Conditional Bow seeds: 983000–983011. Both blocks are separately recorded in the new checkpoint and are unavailable for future unseen validation.
