# Reproduce the frozen C2 release

Run from the repository root with the existing course `.venv`. Authoritative
frozen source: `development/secret_hunter_chance/candidates/C2`; exact ZIP extraction:
`development/secret_hunter_chance/release/secret-hunter-program`. The source was
frozen in commit `92daa80` before final matches. Later changes are research tools,
reports and release copies only. See `final-freeze.json` and the SHA-256 manifest.

## Read-only verification from this workspace

```sh
.venv/bin/hs-arena validate development/secret_hunter_chance/release/secret-hunter-program --no-game
.venv/bin/python -m development.secret_hunter_chance.verify_release
.venv/bin/python -m development.secret_hunter_chance.integrity
```

The latter two commands require the local ignored raw game directories. Git
retains schedules, source hashes, result rows, summaries, public counterfactual
observations and selected audits, but not the large per-player replay folders.
On a fresh clone, re-run games before expecting trace verification to work.
The scripts write their audit summaries; they do not spend additional game budget.

## Recompute estimates without playing games

```sh
.venv/bin/python -m development.secret_hunter_chance.development_analysis
.venv/bin/python -m development.secret_hunter_chance.final_analysis
.venv/bin/python -m development.secret_hunter_chance.report
```

The checked-in JSONL rows suffice for paired estimates. Final analysis keeps the
whole seed cluster intact across seats/opponents, using 10,000 bootstrap draws.
The report also reads the archived integrity/runtime/client summaries. Do not
change thresholds after examining final results.

## Replay the 48-game exact artifact check in a new output directory

This command spends 48 additional full-game attempts. It reuses examined seeds
for reproduction, not new evidence. Record it in a new continuation ledger before
running; the completed round's totals do not include a future user's rerun.
Choose an unused output path, then:

```sh
.venv/bin/python -m development.teacher_eval.run \
  --candidate development/secret_hunter_chance/release/secret-hunter-program \
  --population development/teacher_eval/core.json \
  --out experiments/c2-reproduction-independent \
  --start 941000 --seeds 4 --workers 2 --split confirmation
```

To repeat the entire recorded final schedule, use 40 seeds from 941000 against
`core.json` and 20 from 942000 against `guardrail.json`, both seats, separately
for frozen D1/H7/C2. That costs 3,120 attempts. The stored run configurations
contain exact opponent/deck/source hashes. Do not call these seed blocks unseen.

Local client smoke tests used the existing official Mage, no model host:

```sh
.venv/bin/hs-arena play \
  --p1 client:development/secret_hunter_chance/release/secret-hunter-program \
  --p2 greedy --games 2 --parallel 1 --seed 943000 \
  --out experiments/c2-client-reproduction-independent
```

This spends two additional attempts. It does not submit to the course or measure
Luna/tool/network latency. The release SKILL.md directs the host to execute the
program at every decision and relay the exact current sequence/action.

## Mechanism and runtime evidence

* `mechanisms-v2.json`: 96/96 directed nonterminal cases.
* `development-differential.json`: 160/160 observed development branches.
* `proof-checks-v2.json`: probability, proof separation, metadata/deadline guards.
* `terminal-checks-v2.json`: raw 18/24 matches; six post-game corpse differences.
* `terminal-semantics.json`: nonterminal 17/17 exact; terminal 7/7 same payoff.
* `runtime-C2.json`: 74 cold CLI/fault cases, 60 normal/crowded latency samples.
* `chance-cold.json`: 24 largest development chance trees, exact release.
* `pipeline-checks.json`: 100 warm file-to-action calls, plus stale input during hang.

Initial failed fixture/assertion logs remain archived. They are not production
policy errors and are not silently removed from the ledger. Terminal fixture
attempts are charged as full games; partial/failed reservations stay charged.

## Resuming or starting another round

This round is complete. Do not re-run `setup.py`, snapshot creators, or `build.py`
on its directories. Existing output paths and reservation names intentionally
fail closed. A process interruption does not refund its reservation. Inspect
`budget.json`, its output config and flushed result rows; record any replayed
attempts under a new reservation and reconcile duplicate/missing pairs explicitly.
There is no implicit `--resume` that makes partially viewed validation fresh.

C2 is the new recommendation in `decision.json`; the historical H7 marker and
D1/H7 releases are preserved. Next work should use a new branch/directory/ledger,
scan all historical and reserved blocks again, and freeze new confirmation seeds.
Start by isolating Snake Trap/Juggler cases among the 126 rejected visible
responses. Implement and engine-check their chance response before changing any
weights. Keep C2 as the matched parent, preserve D1/H7 controls and the fixed deck,
and do not infer hidden opponent identities from evaluator filenames.
