# Reproduce the frozen program

Run from the repository root with the existing Python 3.11 `.venv` and supplied `hs_arena` 0.2.2. No extra package, service or key is required. The original round consumed 5,997/6,000 full games; do not silently append a new large experiment to its ledger. Existing results can be verified read-only. New research requires a new explicitly recorded round, budget and untouched seeds.

## Verify existing results and archive

```sh
.venv/bin/hs-arena validate secret-hunter-program --no-game
.venv/bin/python -m development.secret_hunter_program.verify
.venv/bin/python -m development.secret_hunter_program.compare \
  experiments/program-b1-f2-confirmation experiments/program-f2-confirmation \
  --out docs/secret_hunter_program/f2-paired-recomputed.json
.venv/bin/python -m development.secret_hunter_program.relay_audit \
  experiments/program-final-relay-smoke \
  --out docs/secret_hunter_program/f1-relay-audit-recomputed.json
```

The release source is `secret-hunter-program/`; exact extracted F2 is `development/secret_hunter_program/release-F2/secret-hunter-program/`. The same-deck baseline is `development/secret_hunter_program/candidates/B1/`. All P0–P3, T1–T6, validation ablations, F1 and F2 snapshots remain in `candidates/`. The original F1 ZIP is `dist/secret-hunter-program-f1.zip` and its original extraction remains in `release/`.

Build again only from the unchanged frozen source, using a new extraction path:

```sh
.venv/bin/python -m development.secret_hunter_program.build \
  --freeze-dir /tmp/secret-hunter-program-rebuilt
```

This deterministic build writes `dist/secret-hunter-program.zip`, validates the actual extracted skill and verifies source/extraction hashes. It intentionally refuses to overwrite an existing extraction directory. Compare the new ZIP hash with `dist/secret-hunter-program.manifest.json` and `SECRET_HUNTER_CHAMPION.json`.

## Direct public-state API

The pure entry is a function, shared by training and the supervised skill worker:

```python
import json
import sys
sys.path.insert(0, "secret-hunter-program/scripts")
from program_policy import decide
from state_features import with_public_history

config = json.load(open("secret-hunter-program/config.json"))
state = json.load(open("public-state.json"))
public_events = []  # Current game's public events only; reset between games.
state = with_public_history(state, public_events)
action, diagnostics = decide(state, config)
print(json.dumps({"seq": state["seq"], "action": action}))
```

The host-facing command is `python scripts/decide.py` inside the skill folder. It reads `game/state.json` and public `game/history.jsonl`, logs diagnostics under `scratch/`, supervises a killable worker and prints only the final envelope. `python scripts/fallback.py` is the independent program-only fallback. At `game_over`, the CLI emits `game_over: true` and the relay stops. No runtime model selection command exists.

## Exact commands used for final confirmation

These have already completed. `--resume` verifies the candidate and opponent hashes and returns without replaying completed games:

```sh
.venv/bin/python -m development.secret_hunter_program.run \
  --candidate development/secret_hunter_program/candidates/B1 \
  --out experiments/program-b1-f2-confirmation \
  --start 174000 --seeds 10 --workers 2 --split confirmation --resume \
  --hypothesis 'Fresh B1 baseline block paired against F2 after the inactive Companion identity correction.'

.venv/bin/python -m development.secret_hunter_program.run \
  --candidate development/secret_hunter_program/candidates/F2 \
  --out experiments/program-f2-confirmation \
  --start 174000 --seeds 10 --workers 2 --split confirmation --resume \
  --hypothesis 'F2 separate fresh confirmation after fixing unused chance-helper identities; fixed T1 weights, no new tuning.'
```

For a separately budgeted new run, omit `--resume` and choose a new output directory. The runner checks the fixed deck/pool, reserves games before starting, uses opaque game IDs and never passes seed/opponent identifiers into the policy. It refuses to exceed the current round budget or wall deadline.

`train.py` implements the actual two-generation, three-offspring local search (`random.Random(4611)`); `validate.py` runs the seven matched validation/ablation versions. They deliberately refuse existing candidate/output directories. Exact original arguments and candidate hashes are retained in `training.json`, `validation.json` and experiment configs; the snapshots can be evaluated directly without regenerating candidates.

## Mechanisms and time budgets

```sh
.venv/bin/python -m development.secret_hunter_program.checks \
  --candidate development/secret_hunter_program/release-F2/secret-hunter-program \
  --out docs/secret_hunter_program/f2-mechanics-recomputed.json
.venv/bin/python -m development.secret_hunter_program.chance_checks
.venv/bin/python -m development.secret_hunter_program.defence_checks
.venv/bin/python -m development.secret_hunter_program.runtime_checks \
  --candidate development/secret_hunter_program/release-F2/secret-hunter-program \
  --out docs/secret_hunter_program/f2-runtime-recomputed.json
```

These are short cases, never full-game win-rate samples, and each invocation charges the short-case ledger. `differential.py` reconstructs permitted development games for one-step official-engine comparison. `diagnose.py` records earliest divergence and legal current-turn counterfactuals. Engine reconstruction inputs remain outside the policy. `relay_equivalence.py` compares F1/F2 files and recomputes the 77 F1 host actions from public observations.

## Official client and relay

The exact F2 ZIP completed this no-model command:

```sh
.venv/bin/hs-arena play \
  --p1 client:development/secret_hunter_program/release-F2/secret-hunter-program \
  --p2 greedy --games 1 --seed 273001 --parallel 1 \
  --out experiments/program-f2-client-smoke/games
```

The actual run reserved its game before launching the official CLI. Do not rerun into the existing directory. The two official model-host games were F1, using `--mode skill`, seeds 273000–273001, one worker, seat 1 and only `official-mage`. They used the existing course login and a process-local PATH pointing to the working bundled Codex binary; no credentials were added. **The two-game cap is exhausted. Do not run additional model-host smoke games for this round.** F2's exact ZIP has not been model-host tested; it has client, static, fault and public-action-equivalence verification.

No command here sends Slack, publishes a submission or pushes Git. The local champion marker is not a course submission.
