# Reproduction and continuation

Run from the `hearthstone-response-20261111` worktree with `.venv/bin/python`. It uses the existing hs-arena 0.2.2 course environment; no new dependencies or model checkpoint is required. The `.venv` and `hs-arena-0.2.2` symlinks are local conveniences, excluded from Git and all skill ZIPs. Install/use the course distribution separately on another machine. This branch does not install or vendor an external simulator.

Load the existing archive and reservations without resetting them:

```sh
.venv/bin/python -m development.secret_hunter_response.resume
```

The scheduler does not invent policies. A later Codex session must read `REPORT.md`, `checkpoint.json`, `failure-diagnostics.json`, `calibration.json` and the candidate archive, propose a justified child, and reserve genuinely unused final seeds in a new research ledger. Current final seeds are permanently consumed; looking at them again does not create independent confirmation.

## Recorded experiments

The original commands were:

```sh
.venv/bin/python -m development.secret_hunter_response.run --candidate development/secret_hunter_response/candidates/Y1 --name y1-response-data --start 960000 --seeds 40 --workers 6
.venv/bin/python -m development.secret_hunter_response.data
.venv/bin/python -m development.secret_hunter_response.calibrate
.venv/bin/python -m development.secret_hunter_response.predictive_analysis
.venv/bin/python -m development.secret_hunter_response.counterfactual --n 24 --selection 3 --validation 5 --name counterfactual-pilot
.venv/bin/python -m development.secret_hunter_response.counterfactual --n 72 --selection 3 --validation 5 --name counterfactual-balanced
.venv/bin/python -m development.secret_hunter_response.extend_evidence
```

These names already exist in the budget ledger; rerunning a reserved name intentionally refuses to overwrite the experiment. Public response JSONL, model coefficients, source hashes, all counterfactual outcomes, and replay prefixes are committed. Full ignored source logs can be recreated from the recorded game schedules, but strict counterfactual reconstruction uses the archived prefixes and does not require them. Calibration coefficients can be deterministically regenerated with the recorded feature functions, seed-group split and SGD seed; they are offline research artifacts, not runtime dependencies.

The development schedule is 960100–960107 (pilot), 960140–960163 (screen), 960200–960231 (retention), always both seats and the unchanged six core opponents. Each arm uses its own interpreter pool to prevent module-name cross-contamination. See every experiment's `config.json`, `results.jsonl`, `summary.json`, and candidate lineage for actual versions. A replay on an already used development block may be scheduled under a new unique name, subject to the remaining budget:

```sh
.venv/bin/python -m development.secret_hunter_response.run --candidate development/secret_hunter_response/candidates/E1 --name e1-local-replay-1 --start 960200 --seeds 4 --workers 6
```

Final commands, already executed once, were:

```sh
.venv/bin/python -m development.secret_hunter_response.batch --arms Y1,K1,E1,B3,C3 --label final-core --start 961000 --seeds 80 --final
.venv/bin/python -m development.secret_hunter_response.batch --arms Y1,K1,E1 --label final-guard --start 962000 --seeds 20 --population guardrail --final
.venv/bin/python -m development.secret_hunter_response.final_analysis
```

The extra B3/C3 core arms were preregistered before opening final seeds as diagnostic ablations, not additional promotion-eligible challengers. E1 was selected before final results. All final arms remain frozen. No extra samples are appended until significance appears.

## Replay the two evidence cases

These commands re-execute one recorded future, verify the first-turn action trace, next-turn state and final outcome, and charge one full attempt each. Use fresh output names when repeating them:

```sh
.venv/bin/python -m development.secret_hunter_response.replay_case --case 16 --plan plan-2 --out docs/secret_hunter_response/replay-positive-local-1.json
.venv/bin/python -m development.secret_hunter_response.replay_case --case 8 --plan plan-3 --out docs/secret_hunter_response/replay-negative-local-1.json
```

`replay-positive.json` and `replay-negative.json` contain the already completed checks. The positive lead remains weak (4/20 versus 1/20 on extended futures); the harmful alternative is clearer (11/20 versus 19/20). Neither is an unconditional unknown-hand guarantee.

## Run the packaged strategy

`dist/secret-hunter-krush-response-e1.zip` is a research artifact unless `decision.json` records promotion. Its manifest contains all file hashes. The ZIP is extracted at `development/secret_hunter_response/release/secret-hunter-program` and uses only the Python standard library and course dependencies.

```sh
.venv/bin/hs-arena validate development/secret_hunter_response/release/secret-hunter-program --no-game
.venv/bin/hs-arena play --p1 client:development/secret_hunter_response/release/secret-hunter-program --p2 greedy --games 2 --parallel 1 --seed 963000 --out /tmp/hunter-response-client-replay
```

The client command replays already used seeds and is not additional independent evidence. Existing results are in `client-audit.json`. These were no-model local client games; no Luna/Haiku host, real Astra, official Bot2 or course submission was run. To decide against a current public observation, place it at the extracted skill's `game/state.json`, optional public history at `game/history.jsonl`, then run its `scripts/decide.py` from the skill folder. Relay only its matching-sequence action; honor `refresh_required`.

Cold/fault checks are in `runtime-y1.json`, `runtime-e1.json`, `y1-isolated-stale.json`, `e1-isolated-stale.json`, and `chance-cold.json`. Full extracted-game reproduction is in `zip-reproduction.json` and `reproduction-differences.json`. The preserved historical Y1 timeout is not erased by successful new isolated checks.
