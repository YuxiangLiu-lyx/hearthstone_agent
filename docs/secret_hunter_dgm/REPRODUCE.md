# Resume and reproduce the original-deck research

Worktree: `../hearthstone-krush-20261111`; branch `research/secret-hunter-krush-20261111`. Use the existing course Python environment (`.venv/bin/python`, hs-arena 0.2.2). Local `.venv` and course-distribution symlinks are convenience references, excluded from Git and release ZIPs. No environment, installer or model weights are shipped.

## Load the existing checkpoint

```sh
.venv/bin/python -m development.secret_hunter_dgm.resume
```

This loads the full candidate lineage, source hashes, old/used/reserved seeds and cumulative attempt ledger. It does not start again from K0 or invent a strategy. Codex must inspect the checkpoint, diagnostics and negative results and propose the next code change. Do not rerun `setup.py` or snapshot creators on these directories. An existing run name fails closed. Interrupted attempts stay charged; record any retries as new reservations.

The confirmation blocks 951000–951079 and 952000–952019 are permanently examined after this round. The older audit includes reserved blocks, not just rows with completed wins. Conditional continuation PRNG values 954000–959999 are also considered examined. New confirmation requires a new pre-registered round and seed audit. Do not tune on final data and then reuse it for confirmation.

## Recompute from retained results

```sh
.venv/bin/python -m development.secret_hunter_dgm.development_analysis
.venv/bin/python -m development.secret_hunter_dgm.evidence
.venv/bin/python -m development.secret_hunter_dgm.final_analysis
.venv/bin/python -m development.secret_hunter_dgm.integrity
.venv/bin/python -m development.secret_hunter_dgm.archive
```

`final_analysis` recomputes performance gates. `integrity` then reapplies the unresolved full-CLI fault gate and preserves H7. Do not treat the intermediate performance-only file as promotion authorization. Seed bootstrap uses 10,000 whole shared seed resamples, retaining both seats and opponents. Results from different blocks are not sorted by unpaired raw rates.

Large ignored `games/` directories contain local observations used by trajectory and integrity tools. A fresh clone retains complete schedules, aggregate/individual result rows, public diagnostic cases, source hashes and selected trace evidence; regenerate raw games before expecting full local trace audits. This limitation is explicit.

## Verify the actual artifact

```sh
.venv/bin/hs-arena validate development/secret_hunter_dgm/release/secret-hunter-program --no-game
.venv/bin/python -m development.secret_hunter_dgm.deck_guard development/secret_hunter_dgm/release/secret-hunter-program
```

ZIP and extraction hashes are in `dist/secret-hunter-krush-y1.manifest.json`. K0/H7 source and `dist/secret-hunter-program.zip` are preserved byte-for-byte. The new ZIP is a separately labeled research artifact until every promotion gate passes.

The recorded artifact reproduction used **950240–950243**, six existing core opponents, both seats, 48 matches. These are used development seeds, not additional validation. The source/extracted result comparison is `zip-reproduction.json`; one timing-bound action divergence is retained in `trace-divergence.json` rather than rerun until matching.

To independently replay after reserving 48 attempts in a NEW continuation ledger:

```sh
.venv/bin/python -m development.teacher_eval.run \
  --candidate development/secret_hunter_dgm/release/secret-hunter-program \
  --population development/teacher_eval/core.json \
  --out experiments/krush-independent-reproduction \
  --start 950240 --seeds 4 --workers 2 --split confirmation
```

The legacy runner requires that split label for high numeric seeds; this command is **reproduction**, never untouched confirmation. Do not reuse its output path or alter old result rows.

Two no-model local clients used seeds 953000–953001 against the existing official Mage. After a new two-attempt reservation, the same path is:

```sh
.venv/bin/hs-arena play \
  --p1 client:development/secret_hunter_dgm/release/secret-hunter-program \
  --p2 greedy --games 2 --parallel 1 --seed 953000 \
  --out experiments/krush-client-independent-reproduction
```

No actual Luna/Haiku host was run this round. Historical H7 model-host evidence is historical only; current client checks do not measure host model, network or tool latency.

## Next investigation

First instrument cold Python startup, supervisor entry, worker creation and termination under controlled contention to explain the archived >2.5-second stale-observation fault. The independent follow-up refresh checks do not erase it. Keep this instrumentation offline and test baseline/child with identical loads. Any runtime repair after opening confirmation belongs to a new round with newly reserved final seeds.

For strategy work, preserve C2's root-local coverage repair and use the validated Juggler/Hounds case as a fixture. Single-Misdirection response T1 remains an independently validated stepping stone; no whole-game gain or multi-secret correctness is claimed. Prefer measured coverage/continuation questions over another blanket defensive coefficient.
