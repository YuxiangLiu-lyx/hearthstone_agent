# Reproducing and continuing the MCGS iteration

All commands below are executed from the repository root. Use the stable checkout outside cloud-managed Documents:

```sh
cd /Users/liuyuxiang/.codex/worktrees/hearthstone-mcgs-20261112
.venv/bin/python -m development.secret_hunter_mcgs.train status --run runs/krush-mcgs
```

`runs/krush-mcgs/launch.json` holds the current PID, exact launch command, working directory and log path. `training.log` contains actual per-game results; `checkpoint.json` is a convenience snapshot, and SQLite is authoritative. A local `caffeinate -i -w PID -t 28800` process prevents idle sleep while training is active. A reboot, logout or manual termination can still stop the process; resume is explicit.

## Environment and sources

The starting commit is `5afec0f074e56145723f544e23aba062f4be14e3`; the research branch is `research/secret-hunter-mcgs-20261112`. Python 3.11 and the existing course distribution `hs_arena` 0.2.2 are required. No external model or paid API is needed. On another machine, create a venv and install the authorized course wheel with its supplied dependency wheels, following the course README. The research code does not modify that distribution.

The new local checkout was cloned from the existing face-validation branch after cloud placeholders broke Git/file reads in Documents. Its course wheel was extracted into the copied local venv to restore missing bytes, then checked against all 339 pre-existing course file hashes. That repair did not change engine semantics. Optional packages such as the broken copied pip installation are not needed by the running trainer; for a fresh installation use a newly created venv and the course's installation instructions.

Read `SOURCES.md` and `source-fetch.json` for primary URLs, sections, exact source hashes and license findings. Actual source downloads used curl after an initial urllib certificate failure. For example:

```sh
curl -L https://hearthstoneai.github.io/files/bots/UserCreatedDeckPlaying2019/2019_UCDP_MCGS.zip -o /tmp/choe.zip
shasum -a 256 /tmp/choe.zip
curl -L https://ieee-cog.org/2019/papers/paper_257.pdf -o /tmp/choe.pdf
```

The champion ZIP must hash to `f00a54f310a8f868deb59964c17e71357d67ecfcedba01c0245053dcc5aa920a`. The course Markdown and evolution/DGM HTML hashes are also recorded. No downloaded champion code is in the skill ZIP.

## Checks actually executed

```sh
.venv/bin/python -m development.secret_hunter_mcgs.audit
.venv/bin/python -m development.secret_hunter_mcgs.checks
.venv/bin/python -m development.secret_hunter_mcgs.response_transfer
.venv/bin/python -m development.secret_hunter_mcgs.replays
.venv/bin/python -m development.secret_hunter_mcgs.evidence
.venv/bin/python -m development.secret_hunter_mcgs.ablate
.venv/bin/python -m development.secret_hunter_mcgs.runtime
.venv/bin/python -m development.secret_hunter_mcgs.runtime --candidate development/secret_hunter_mcgs/candidates/M5-dpw --out docs/secret_hunter_mcgs/runtime-M5-isolated.json
.venv/bin/python -m development.secret_hunter_mcgs.runtime --candidate development/secret_hunter_mcgs/candidates/M5-uct --out docs/secret_hunter_mcgs/runtime-M5-uct-isolated.json
.venv/bin/python -m development.secret_hunter_mcgs.analyze
.venv/bin/python -m compileall -q development/secret_hunter_mcgs
```

The replay/evidence/analysis commands use the restored run's public C2 extraction. Their default path is `runs/krush-mcgs`. `replays` creates 240 terminal attempts and four pairs of fast/reference searches; rerunning it is an explicit new offline computation and should be charged in a new research ledger if used for optimization. The actual study charged the initial exploratory continuations, failed translation attempts, corrected continuations, illustrative full traces and diagnostic continuations. The manual accounting reserve is 600 (598 identified plus a two-attempt conservative cushion); subsequent runner-generated continuations are charged individually before execution.

`continuations-guided-proxy.json` is the **earlier exploratory** result whose anchor used a cheap rank policy. Its original Y1 label was incorrect. `continuations.json` and `continuations-v2` are the corrected full-Y1-plan experiment. Do not combine them as independent samples. The unchanged source seeds and all derived states are development data.

The full-CLI match adapter is `cli_match.py`. It launches the unmodified candidate supervisor afresh for each atomic action, writes only the legal state and public history, verifies the returned seq/action, and records outer elapsed time. Warm Python full games remain explicitly labeled. The frozen course evaluator and opponent implementation were reused without source edits.

## Training commands and durable budget

These are the supported entrypoints, all exercised during this work:

```sh
.venv/bin/python -m development.secret_hunter_mcgs.train pilot --run runs/krush-mcgs
.venv/bin/python -m development.secret_hunter_mcgs.train run --run runs/krush-mcgs --hours 8 --max-full-games 12000 --max-continuations 60000 --workers 4
.venv/bin/python -m development.secret_hunter_mcgs.train status --run runs/krush-mcgs
.venv/bin/python -m development.secret_hunter_mcgs.train resume --run runs/krush-mcgs --workers 4
```

Do not launch a second writer while the detached process is running. The lock rejects it. `status` does not claim the writer lock or change candidate selection. `resume` uses the persisted mode, limits, charged attempts and pending tasks; it does not grant another eight hours. New `pilot` initialization runs the source/deck/engine checks, a small representative paired terminal replay, four M5/Y1 arms, and a second batch automatically. Historical pilot amendments and their original M0/M3 results are retained in the current run; the fresh entrypoint no longer begins with the known-bad M0 adapter.

The exact detached launcher was Python `subprocess.Popen(command, cwd=root, stdout=training_log, stderr=STDOUT, start_new_session=True)` followed by `caffeinate`. The initial detached PID 3235 encountered the cloud failure. PID 4949 resumed in the stable checkout, completed cli-103 and automatically began gen-001. It was drained to load the explicit analysis-time accounting and corrected fresh-pilot entrypoint. The subsequent launch and current PID are in `launch.json`; do not rely on historical PIDs to send signals.

To stop and resume deliberately, read and verify the PID/command before sending SIGTERM. The runner stops dispatching and allows five seconds for inflight games to finish. It then terminates their isolated process groups, including CLI descendants, and returns unfinished tasks to pending. The default whole-game limits are 120 seconds for in-process policy games and 180 seconds for full-CLI games. A timed-out execution stays charged and gets one retry per invocation; a second failure leaves the batch incomplete, with no fabricated strategy loss or promotion. These limits do not replace the unchanged per-decision CLI deadline. The historical pool-based interruption tests preserved completed keys, but a later two-hour stuck game exposed an unbounded drain; the new process supervision fixes that failure mode. An injected second writer produced `Another writer owns this run.` Abrupt machine loss was not separately exercised.

The runner reserves whole seed blocks before dispatch, charges every full-game attempt before launching, atomically writes worker results before acknowledgment and uses WAL SQLite plus one writer lock. A completed atomic result can be reconciled after a parent interruption. A missing result leaves the attempt charged and permits a new attempt for that task; this is a recorded retry, not a free replay. Candidate fingerprints are checked before and after each arm. Previously completed tasks are not replayed by a normal drain/resume.

## Actual seed blocks and amendments

| Block | Purpose |
| --- | --- |
| 10000000–10000001 | Initial Y1/M0 diagnostic; remaining M1/M2 tasks cancelled unlaunched |
| 10000100–10000101 | Initial second batch cancelled before launch after semantic failure |
| 10000200–10000201 | Corrected four-arm M3 pilot |
| 10000300–10000301 | Automatically started M3 DPW second batch |
| 10000400–10000403 | Y1 / M3 DPW / M5 DPW structural comparison |
| 10000600 | Four-arm full-CLI pilot |
| 10000700–10000703 | Y1 / M5 UCT / M6 confidence experiment |
| 10001000–10001003 | Aborted cloud-storage batch, 96 charged attempts, excluded from selection |
| 10001100 onward | Fresh automatic generations; each reserves four seeds and advances by 100 |
| 10050000 onward | Selection, full CLI |
| 10100000–10100079 | Frozen final core, full CLI, 1,920 games |
| 10200000–10200019 | Frozen final guard, full CLI, 1,120 games |

The caps include pilot and failures. The original dataset's seed values and prior face-validation seeds remain known/development. The ledger is the authority if the automatic run has progressed beyond this table. No final result is a training feature; `finalize.py` writes a result only after both frozen final reports exist and the runtime gate is checked.

## Failures, corrections and coverage

`lineage.json`, `structural-lineage.json`, `particle-lineage.json`, `identity-lineage.json` and `confidence-lineage.json` contain immutable parents/settings/hashes. `automatic-lineage.json` and the live ledger describe preimplemented automatic configurations. Actual source revisions repaired read-only immunity handling, aura double counting, weapon durability, hidden-particle collapse and entity-ID collisions. The own-turn-only ablation and unused paper-rounding option were corrected and retested. M5 match defaults did not use either corrected option.

`storage-amendment.json` records the excluded cloud failure. `storage-recovery.json` lists original unavailable files and expected sizes. Candidate bytes were reconstructed from identical frozen copies and all original fingerprints match. Missing historical raw observations were not synthesized. The SQLite task result records, existing reports, current CLI full trajectories and full positive/negative examples remain available. Source manifest and mechanism results were recreated from retained downloaded bytes and rerun checks. The original cloud worktree was not deleted.

The offline proposal CLI could not start: `/opt/homebrew/bin/codex --version`, `exec --help`, and `login status` all failed ENOENT for its vendor binary. No automatic code-agent invocation is claimed. Configuration evolution continues in Python; the checkpoint names the next structural hypothesis for a future agent session.

## Packages and restoration

```sh
.venv/bin/python -m development.secret_hunter_mcgs.archive --skill-only
.venv/bin/python -m development.secret_hunter_mcgs.archive --run runs/krush-mcgs
```

The first builds `dist/secret-hunter-krush-m5-uct-research.zip`, one course-loadable skill directory under 10 MB. It has been extracted, loaded, fingerprinted and checked for exact deck submission. `package.json` records its hash and research-only status. The second also makes `dist/secret-hunter-mcgs-research-data.zip`, which is an **offline data/checkpoint archive**, not a submission and not subject to the skill's size limit. It contains a consistent SQLite backup, completed-at-snapshot attempt/game files, available original traces, full continuation examples and automatic candidate snapshots. Unavailable old cloud files remain listed separately. Inflight attempts in the snapshot remain charged and are retried/reconciled on restoration.

To restore into a **new**, nonexistent run directory:

```sh
.venv/bin/python -m development.secret_hunter_mcgs.archive --restore dist/secret-hunter-mcgs-research-data.zip --run runs/restored-krush-mcgs
.venv/bin/python -m development.secret_hunter_mcgs.train status --run runs/restored-krush-mcgs
.venv/bin/python -m development.secret_hunter_mcgs.train resume --run runs/restored-krush-mcgs --workers 4
```

Restore rewrites attempt result paths, clears the copied PID and verifies any existing automatic candidate bytes before reuse. Do not run an original and restored ledger simultaneously as if they were independent research: they share seeds and history. The archive is a point-in-time snapshot; the live run will contain later results.

The confidence batch completed 144 further games (Y1 45/48, M5 UCT 44/48, M6 45/48). These are included in the final data snapshot. New workflow files pass `git diff --check`; the eleven immutable candidate snapshots retain one pre-existing whitespace-only line from Y1 `improvements.py` so their experimental fingerprints remain unchanged.

## Resuming after the November 12 user pause

The paused ledger preserved 4,607 completed tasks and 4,608 charged attempts, including interrupted attempt 4594 (G024, bot2-face-proxy, seed 10003802, seat 2). Its missing result was not scored as a loss. The original eight-hour budget had 3,713.51 seconds remaining; resuming does not reset it. The largest recorded completed warm-policy game was 42.92 seconds (4,127 rows), compared with the stuck execution lasting over two hours.

The supervised runner uses a fresh process per game while leaving policy, deck, opponent, seed and engine bytes unchanged. Each attempt has a request JSON and worker log; a delayed stack dump precedes its whole-game deadline. The resume uses two workers and Unix niceness 10 to reduce foreground interference. All new outputs stay in the checkout outside iCloud-managed Documents.

```sh
.venv/bin/python -m unittest development.secret_hunter_mcgs.test_supervision -v
nice -n 10 .venv/bin/python -m development.secret_hunter_mcgs.train resume --run runs/krush-mcgs --workers 2
```

Four fault-injection tests passed: timeout/retry accounting followed by successful recovery without duplicate completed work; bounded stop with a pending unscored task; budget expiry during an active game; and removal of a CLI descendant. The original checkpoint and pause evidence remain under `runs/krush-mcgs/pause-events/`.

The first live resume reproduced the stuck source game: at turn 5, a choice offer and the submitted choice stayed unchanged across thousands of increasing sequence numbers. Attempt 4609 hit the 120-second deadline; its retry 4610 was interrupted by a verified SIGTERM and the trainer plus its keep-awake process exited. Both attempts remain charged, without win/loss labels. The public reproducer is `pause-events/repeated-choice-004609.json`. The root cause is not yet isolated between live-engine choice handling and research adapter state interaction.

`pause-events/quarantine-gen-028.json` records the exclusion of the entire incomplete development batch from selection, preserving its 95 completed results and all pending tasks. Its status is `execution_failed`; normal resume does not silently retry it. Selection proceeds from the unchanged archive of completed batches, using the already reserved selection seed block. No candidate, opponent, engine, final seed or budget was changed to work around this failure.
