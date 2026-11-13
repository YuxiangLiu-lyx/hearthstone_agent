# Reproducing the original Krush turn-plan study

All reported opponents are frozen local proxies. No real Astra service or external model participates in these experiments. Read `REPORT.md` for the completed result and recommendation; a ZIP being present does not imply that its policy was promoted.

## Environment and provenance

- Research branch: `research/secret-hunter-turn-plans-20261112`.
- Starting repository commit: `c2bc11f0a88f2e20dcd951a056042bcb40426041`.
- Recovered historical commit: `0066a304931ae89415e6eff2a6735c2d6026b7d0`.
- Python 3.11.15; installed course package `hs-arena` 0.2.2 and its bundled dependencies.
- The course distribution is available locally as `hs-arena-0.2.2`; it is not included in a submission ZIP.
- Exact engine tree, candidate fingerprints, ordered deck audit, and final seed reservation are recorded in the adjacent JSON files.
- The only changed old research adapter is `development/secret_hunter_mcgs/mcgs_world.py`: restore an unused zero-attack hero's swing using the already-public `hero_attack_available` feature. The installed course engine is unchanged.

Commands below run from the research worktree. Its `.venv` is a local convenience link, excluded from Git and all packages. Substitute another Python environment with the same course package when necessary.

```sh
cd /Users/liuyuxiang/.codex/worktrees/hearthstone-turn-plans-20261112
.venv/bin/python -m development.secret_hunter_turn_plans.study status
```

The ledger is SQLite/WAL. Status is read-only and works while a batch holds the writer lock. The supervisor uses three concurrent game processes with fresh complete CLI invocations for every atomic decision. No in-process timing estimate is substituted for CLI timing.

## Read and independently aggregate completed games

The research data archive restores `runs/turn-plans-20261112/` under the repository. The compact committed results can also be read without rerunning games. Strict pair keys are `(opponent, seed, seat)`; duplicate, missing, or invalid pairs fail instead of being silently dropped.

```sh
.venv/bin/python -m development.secret_hunter_turn_plans.finalize
.venv/bin/python -m development.secret_hunter_turn_plans.audit --batch final-core --baseline engine-trap-v2
.venv/bin/python -m development.secret_hunter_turn_plans.audit --batch final-guard --baseline engine-trap-v2
.venv/bin/python -m development.secret_hunter_turn_plans.analyze_offline --input continuations-v4
.venv/bin/python -m development.secret_hunter_turn_plans.analyze_offline --input strict-coil-v2
.venv/bin/python -m development.secret_hunter_turn_plans.evidence
```

`finalize` requires all three arms to have 480 core and 224 guard games. Its 95% intervals resample whole seed clusters 10,000 times, keeping both seats and all opponents together. The primary score is `(Astra family rate + Bot2 family rate) / 2`; Greedy is reported separately. These intervals describe the fixed local proxy pool, not generalization to an unknown competitive ladder.

## Run the frozen comparison again

The existing run retains its initial four-hour deadline. Use a new run directory for a fresh reproduction budget. The published final seeds are now known reproduction seeds; they must never again be called unseen validation data for a modified policy.

```sh
export KRUSH_TURN_RUN="$PWD/runs/turn-plans-reproduction"
.venv/bin/python -m development.secret_hunter_turn_plans.study init
cp docs/secret_hunter_turn_plans/final-freeze.json "$KRUSH_TURN_RUN/final-freeze.json"
nice -n 10 .venv/bin/python -u -m development.secret_hunter_turn_plans.study run \
  --batch final-core --arms Y1 engine-trap-v2 E2-finish-minions \
  --start 31100000 --seeds 40 --workers 3 --final
nice -n 10 .venv/bin/python -u -m development.secret_hunter_turn_plans.study run \
  --batch final-guard --arms Y1 engine-trap-v2 E2-finish-minions \
  --start 31200000 --seeds 8 --pool guardrail --workers 3 --final
.venv/bin/python -m development.secret_hunter_turn_plans.finalize
```

Keep the environment variable set for the same run. `Ctrl-C` or `SIGTERM` stops scheduling, allows a short grace period, closes child process groups, and returns interrupted tasks to pending. Rerun the exact batch command to resume within its recorded budget; completed tasks are skipped. Execution failures are charged as attempts and are not fabricated strategy losses. Do not start two writers for one run. To preserve and resume after an intentionally long pause beyond the deadline, explicitly create a new budget/run and label it as such rather than silently resetting the old ledger.

## Reproduce a complete counterfactual replay

Use the original archived run, or set `KRUSH_TURN_RUN` to its extracted location. Each selected result has a neighboring `.request.json`, its public source case, the sampled hidden-card hypothesis, initial RNG seed, actual tested-turn actions, and a complete trace to the terminal winner. The replay command checks every stored public state and every action against the original course engine.

```sh
unset KRUSH_TURN_RUN
.venv/bin/python -m development.secret_hunter_turn_plans.replay \
  runs/turn-plans-20261112/recovered-golem-continuations/trap-replay-0-natural-0-replan.json
.venv/bin/python -m development.secret_hunter_turn_plans.replay \
  runs/turn-plans-20261112/recovered-golem-continuations/trap-replay-0-natural-0-committed.json
.venv/bin/python -m development.secret_hunter_turn_plans.replay \
  runs/turn-plans-20261112/continuations-v4/amani-031-natural-0-replan.json
.venv/bin/python -m development.secret_hunter_turn_plans.replay \
  runs/turn-plans-20261112/continuations-v4/amani-031-natural-0-bow_amani.json
```

The first pair changes only the tested turn's Secretkeeper completion. The second pair demonstrates a legal alternate turn that turns a win into a loss. Route names denote search objectives; consult the actual sequence before describing an action as Bow removal, Taunt, or Highmane development. Source grouping prevents the same source seed, opposite seat, or adjacent state from crossing training and validation. Conditional futures within one source game are not independent source groups.

For regenerated continuation jobs, copy the archived `mined-v4` source directory into a newly initialized run and use:

```sh
.venv/bin/python -m development.secret_hunter_turn_plans.offline \
  --sources mined-v4 --output continuations-v4 --candidate E3-verified-plans --samples 4 --workers 3
.venv/bin/python -m development.secret_hunter_turn_plans.offline \
  --sources mined-v4 --output strict-coil-v2 --candidate E3-verified-plans --samples 4 --workers 3 \
  --only-scenario forced_coil --strict-coil --force-next-draw
```

The stress sampler conditions on Coil in hand, or the next draw when the hand is empty, while preserving card counts. It excludes already-damaged source Amani and does not deliberately self-kill Amani with Coil after a defensive trade. Forced-Coil outcomes are diagnostic labels only. Natural samples alone fit the small rules; none of those new rules generalized well enough to enter the final candidate.

## Rebuild and validate submission artifacts

The candidate directories are immutable source snapshots. Their internal modules preserve the implementation at each build, even when the later research helper changes. Rebuilding the authentic historical parent uses the recovered source:

```sh
.venv/bin/python -m development.secret_hunter_astra_plans.build \
  --out /tmp/krush-engine-trap-rebuild engine trap
.venv/bin/python -m development.secret_hunter_turn_plans.package
.venv/bin/hs-arena validate --no-game development/secret_hunter_turn_plans/candidates/engine-trap-v2
.venv/bin/hs-arena validate --no-game development/secret_hunter_turn_plans/candidates/E2-finish-minions
.venv/bin/python -m development.secret_hunter_turn_plans.runtime --candidate E2-finish-minions
.venv/bin/python -m development.secret_hunter_turn_plans.runtime --candidate E2-finish-minions --isolated-stale
```

Packaging verifies that unpacked source fingerprints equal the frozen tested candidates. Each submission ZIP contains one skill folder, Python sources, JSON configuration/deck, and its existing playbook; no environment, binary, checkpoint, private game state, or research dataset. `--no-game` is intentional: static course validation is separate from the completed local full-CLI matches. No completed live Luna relay match or real Astra win rate is claimed by this study.
