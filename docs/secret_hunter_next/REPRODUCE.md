# Reproduce and continue

Run from the repository root with the existing Python 3.11 `.venv` and unmodified
course `hs_arena 0.2.2`. The course distribution is deliberately not vendored in
Git; use the supplied official wheel if creating a fresh environment. No new
package, model call, network inference, or formal upload is needed.

## Verify the delivered local evidence

```sh
.venv/bin/hs-arena validate development/secret_hunter_next/release/secret-hunter-program --no-game
.venv/bin/python -m development.secret_hunter_next.final_analysis
.venv/bin/python -m development.secret_hunter_next.verify_release
.venv/bin/python -m development.secret_hunter_next.integrity
.venv/bin/python -m development.secret_hunter_next.report
shasum -a 256 dist/secret-hunter-next-m1.zip
```

Expected ZIP SHA-256:
`98a1854949caca7f277eeb5a914b36daa49887f25c0a6619bb36264408489990`.
Expected source fingerprint:
`51cb2cb2454dcff6dea5df3be5ce7dd6c9c99edcff42417b663e8490c70f5b75`.
The repository's fingerprint hashes relative paths plus `.py/.json/.md` bytes;
it is not the Git commit ID. The ZIP manifest lists every packaged file hash.

The compact results, configs, reports and counterfactual observations are tracked.
Large per-game raw folders are preserved locally under `experiments/` and ignored
by Git, consistent with the existing repository. A clean clone can recompute the
final statistics from tracked rows, but must rerun the engine to regenerate raw
observations before calling raw-trace verification or integrity checks.

## Repeat the exact extracted program on used seeds

The following command is an actual 48-game engine rerun. Its output name must be
new. It reserves 48 attempts in the current ledger; it never resets the budget or
claims those used seeds are independent validation.

```sh
.venv/bin/python -m development.secret_hunter_next.run \
  --candidate development/secret_hunter_next/release/secret-hunter-program \
  --name manual-zip-check --start 931000 --seeds 4 --workers 4 --final
```

The archived exact ZIP run is `experiments/secret-hunter-next-zip-reproduction`.
It matched 48/48 winners and all 48 action traces against the original frozen M1
confirmation. Wall-clock cutoffs may alter decisions on a different machine/load;
report differences instead of rerunning until they disappear.

To reconstruct the complete three-arm schedule, use the same runner with candidate
`M1`, `D1`, or `H7` under `development/secret_hunter_next/candidates/`:

- Core: `--start 931000 --seeds 40 --final` (480 games per arm).
- Guardrail: `--population guardrail --start 932000 --seeds 20 --final` (560 per arm).

A complete six-run repeat exceeds the remaining budget of this closed round. It
requires a separately declared reproduction budget/ledger in a new directory;
do not change or reset the archived ledger. All these seeds remain used data.

The official local transport invocation, already run for two games, was:

```sh
.venv/bin/hs-arena play \
  --p1 client:development/secret_hunter_next/release/secret-hunter-program \
  --p2 greedy --games 2 --parallel 1 --seed 933000 \
  --out experiments/secret-hunter-next-client
```

Do not overwrite that destination. It is the existing official Mage opponent,
not an added opponent, a model-host test, or Astra. Future invocations require
separate attempt charges before launch. The course host must run the script and
relay the current `seq/action` exactly as stated in the packaged SKILL.md.

## Recover an interruption safely

`budget.json` reserves all scheduled attempts before execution and uses a lock.
Each completed row is flushed immediately to `results.jsonl`; `config.json`
records the exact schedule, hashes and already-exposed seed block. Started or
failed work is never automatically refunded. Output directories cannot overwrite
one another. This round has no unfinished reservations.

Before continuing an interrupted future run, compare the expected
`(opponent, seed, seat)` keys in its config against recorded rows and actual game
folders. Reconcile any completed-but-unrecorded or partial game first; keep the
partial artifacts and charge any restarted attempt in addition to the original
reservation. Do not blindly rerun the whole schedule, change a frozen candidate,
reset `setup.py`, or treat a reserved/exposed final block as fresh. The runner
intentionally refuses automatic overwrite rather than guessing about orphaned
game folders.

## Next development cycle

Start with the hypothesis in REPORT.md: bounded stochastic continuation for
Juggler plus summons/Hounds, so a useful random root does not disable comparison
of the rest of the turn. Preserve M1 as the mechanism reference and D1/H7 as
frozen controls. Use a new independent work directory and scan this round's
configs as well as `seed-audit.json`; 931000/932000 are now development-only if
revisited. Compare parent and child on a shared new block, then freeze one child
before assigning another untouched final block. Do not copy the whole historical
repository into a new candidate.

Use `candidates.json`, the 24 counterfactual cases, grouped final telemetry and
recorded negative directions to choose cases. Six conditional samples per action
are not enough to certify a repaired loss. For stronger causal checks, increase
samples on the *specific early trade/removal decision* and vary plausible hidden
hands consistently with public evidence; policies must still receive only legal
public observations. Keep full terminal continuations in the full-game budget.
