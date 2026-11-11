# Reproduction and entry points

Run from the repository root using `.venv/bin/python` / `.venv/bin/hs-arena`.
No runtime installation, network, model inference, or opponent private data is
needed for program training. The base commit is
`6a7fc2475a17190268594ef2f5940b5b3a62f8f0`; frozen source hashes identify the
uncommitted research files, so the commit alone is not the release identifier.

## Artifacts

- Retained champion: `secret-hunter-program/`, `dist/secret-hunter-program.zip`.
- Exact F2 baseline: `development/secret_hunter_es/candidates/B0/`.
- Rejected research finalist: `development/secret_hunter_es/candidates/C2/`.
- Exact research ZIP: `dist/secret-hunter-es.zip`.
- Extracted research ZIP: `development/secret_hunter_es/release/secret-hunter-program/`.
- Instruction-only revision: `dist/secret-hunter-es-relay-fix.zip`; client verified, official host unconfirmed.
- Evolved candidates and their inherited sigmas: `candidates/E*`, `evolution.json`.

The research ZIP is a valid skill package, **not the recommended champion**.
The existing champion marker and ZIP were not replaced.

## Policy and interface

The pure entry point is `scripts/program_policy.py:decide(public_state, config)`.
The supervised CLI is `scripts/decide.py`; it reads `game/state.json`, maintains
only within-game public history and prints one `seq/action` JSON envelope.
`client.py` and the Luna relay skill call that same supervised program.

```sh
.venv/bin/hs-arena validate development/secret_hunter_es/release/secret-hunter-program --no-game
.venv/bin/python -m development.secret_hunter_es.runtime_checks --candidate development/secret_hunter_es/release/secret-hunter-program --out docs/secret_hunter_es/runtime-checks-repeat.json
.venv/bin/python -m development.secret_hunter_es.verify
```

The runtime check records short-case budget and deliberately kills hung workers;
it does not start a model-host match. A direct CLI call requires an actual public
observation in the skill's own `game/state.json`.

## Executed experiment commands

```sh
.venv/bin/python -m development.secret_hunter_es.setup
.venv/bin/python -m development.secret_hunter_es.checks
.venv/bin/python -m development.secret_hunter_es.differential
.venv/bin/python -m development.secret_hunter_es.screen
.venv/bin/python -m development.secret_hunter_es.evolve
.venv/bin/python -m development.secret_hunter_es.validate
.venv/bin/python -m development.secret_hunter_es.build
.venv/bin/python -m development.secret_hunter_es.confirm
.venv/bin/python -m development.secret_hunter_es.run --candidate development/secret_hunter_es/release/secret-hunter-program --out experiments/es-zip-reproduction-confirmation --start 281000 --seeds 2 --split confirmation --hypothesis 'Previously used seeds; reproduction only'
.venv/bin/python -m development.secret_hunter_es.summarize
.venv/bin/python -m development.secret_hunter_es.report
```

The initial baseline and extra D1 screen were separate `run` invocations, with
`--start 78100 --seeds 4` and the exact paths and hypotheses recorded in each
experiment's `config.json`. `screen.py` creates C1/C2/C3 from the preserved
`working/` implementation; `evolve.py` clones immutable parents before mutations.
`validate.py` freezes before the final 40-seed confirmation; `confirm.py` evaluates
the actual ZIP extraction. All full-game evaluations use 14 frozen opponents,
both seats, four Python workers, and the unchanged official engine.

Scripts deliberately refuse to overwrite frozen outputs. `run --resume` with
the same original arguments verifies completed run hashes without replaying
games. New research reruns require new output names and a separately authorized,
fresh dated budget; do not delete the ledger or silently extend this round.
The current completed round is near its 6,000-game limit.

The two official client and two Luna-medium smoke games are interface checks
only. They are excluded from the primary final estimate. Do not repeat model-host
smokes within this round, which has already used its two-game allowance.

The final host audit found one skipped script call (61/62 exact). The original
research ZIP remains frozen. `relay-fix.json` documents a separate instruction-only
revision and its 73/73 client action reproduction. To reproduce its static build:

```sh
.venv/bin/python -m development.secret_hunter_es.build --source development/secret_hunter_es/relay-fix/secret-hunter-program --artifact secret-hunter-es-relay-fix --freeze-dir development/secret_hunter_es/release-relay-fix
```

That command also refuses to overwrite the archived release. It does not imply
that the revised instructions passed an official model-host test.
