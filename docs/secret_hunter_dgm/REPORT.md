# Original Krush Secret Hunter: performance improvement, no release promotion

**Keep H7 as the release champion. Y1 passes every performance gate but fails the strict reliability gate because a full-CLI stale-observation fault test exceeded 2.5 seconds and its cause remains unresolved.** Eight subsequent correct refresh tests do not erase that failure. No policy changed after final opening; no extra confirmation was added. Y1 is a separately verified research ZIP, not an official course submission.

## Starting point and immutable boundaries

Actual local and remote HEAD was `b160f41`, newer than the requested reference `9ef30c2`. The intervening chance round was reviewed: its C2 uses D1, so none of its win rates are attributed to the original deck. The tree was clean, no applicable AGENTS.md was found, and work continued in an independent worktree/branch. Main and the original worktree remain untouched. Final Y1 was frozen in commit `26e802f` before any final result.

Every candidate uses the original **30-card Hunter deck with King Krush, Misdirection and Ooze**, with the original card order. No Arcane Shot or Snipe. Deck SHA-256: `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`. Each candidate/batch/build checks hash, multiset, size, official class/copy validation and actual program `deck_submission`. K0 is byte-preserved H7; K1 is M1 strategy with only the original deck copied over. K1 inherits no D1 result.

Integrity verifies 3,872 original tracked files, 339 installed engine files, both frozen opponent manifests, all source fingerprints, schedules and summaries. Only the six existing core and fourteen existing guardrail opponents were used; no real Astra, models, self-play or opponent evolution.

Historical scans found 1,399 used/reserved seed values. Development used subsets of 950000–950303; final core was 951000–951079 and guardrail 952000–952019. These are now examined. Conditional PRNG values 954000–959999 are recorded as examined too. `seed-audit.json`, `plan.json`, `budget.json` and `checkpoint.json` preserve boundaries.

## Offline evolution and negative results

This is a Codex-directed program evolution adaptation, not full DGM, AlphaEvolve or GEPA reproduction. The scheduler evaluates and archives; Codex reads trajectories and writes new code. All deployed decisions remain Python/public-information decisions. No fitted weights or external services are bundled. Specific papers/functions and licensing boundaries are in `SOURCES.md`.

| Candidate | Parents | Tested change and outcome |
|---|---|---|
| C0 | historical chance C2 | Same-deck transfer of exact/sampled summon search; pilot and screen did not establish a gain. |
| B1 | K1 | Slot/mana/Taunt-aware in-hand Krush charge clock; no future draw assumed, hero freeze separated from minion charge. Eight conditional checks pass. Same-block win counts unchanged; strategic value not independently established. |
| C1 | C0 | Standalone Companion activation, including all three outcomes; inherited trigger projector matches 96/96 official-engine cases. No standalone overall gain. |
| O1 | K1 | Require a coherent early curve before keeping three-drops against pressure classes. Regressed in both blocks; rejected. |
| C2 | C1 | Reject an unsupported alternative locally while preserving completed comparable roots. Unsupported baseline still prevents overriding the original rule. Conditional Juggler/Hounds case supports this repair. |
| E1 | K1 + historical M2 | Revive opaque enemy draw and enemy-only Wyrm/Apprentice body coverage. Five directed checks; local ability retained and re-evaluated on common blocks. |
| S1 | C2 | Compare three own-turn endpoints after visible responses. Small round2 gain failed to persist; higher latency. |
| T1 | C2 | Exact single-Misdirection targets plus bounded outcome-contingent visible attacks. 24/24 real-engine checks; no overall gain; not in release. Multi-secret and Snake/Juggler responses remain unresolved. |
| X1 | S1 + B1 + E1 | Complementary merge, verified with another 96/96 mechanism set. Gains were re-evaluated, not assumed additive. |
| Y1 | X1 + C2 | Ablate the costly endpoint shortlist while retaining local-root rejection, Companion, Krush clock and M2 effects. Selected before final. |

Nine substantive modifications plus the C0 transfer were evaluated. K0/K1 are controls, not counted as new hypotheses. `candidates.json` and append-only `archive.jsonl` retain lineage, code/config/deck/tool hashes, seed schedules, opponents, actual first player, costs and retention reasons.

| Shared development block | K0 | K1 | Other relevant arms |
|---|---:|---:|---|
| Pilot, 72/arm | 60 | 60 | C0 60 |
| Screen, 144/arm | 119 | 125 | B1 125; C0 124; C1 123; O1 123 |
| Round2, 192/arm | — | 150 | B1 150; C1 150; O1 149; C2 151; E1 150; S1 152 |
| Round3, 240/arm | 182 | 195 | E1 202; S1 194; T1 192; X1 200 |
| Retention, 384/arm | 272 | 277 | E1 282; X1 284; Y1 284 |
| Old-pool development, 112/arm | 96 | 96 | E1 98; X1 99; Y1 99 |

On retention, Y1 primary was 72.14%, versus X1 72.01%, E1 70.83%, K1 70.57% and K0 69.14%. Y1 was chosen for slightly better primary and lower P99 latency, not because this tiny difference proved superiority. Larger response machinery and stricter openings were not stable improvements. These repeated selection blocks, including inspected counterfactual validation cases, are development data; no row was relabeled independent confirmation.

## Training-tool evolution and conditional evidence

The original-root harness reconstructs source games in the official engine, preserves every original action, validates alternatives with legal public actions, records complete first-turn continuations and terminal outcomes, and splits by whole source seed clusters. Existing hidden hands remain conditioned on the source and are never supplied to a policy. Sample 0 retains source RNG/deck order; later samples resample future order/RNG. Divergent actions consume randomness differently. There is no public-belief reconstruction benchmark in this round and no unknown-hand forced-win claim.

- Initial 60 stratified source games: all six opponents, 20 early/24 mid/16 late; 480 terminal continuations and all 60 original roots. Five originals were outside the fast model but executed legally in the engine.
- The next tool version excludes forced decisions and deduplicates tactical roots while sampling new C1 trajectories. Another 60 games, 25 early/20 mid/15 late, yielded 540 continuations, 180/180 possible root comparisons versus 160/180 initially, and retained 20 unsupported original roots. This is measured feedback yield on different selected distributions, not a controlled population effect.
- Eight important disagreements received 288 additional continuations (12/action). Two training cases were also tested with a stronger legal public-information continuation policy, 72 more games. Total terminal counterfactuals: 1,380, zero errors. No learned model enters the release.

The clearest case is source `fb25edd091cf4420`, seq 7, turn 5, Bot2-face proxy: own Juggler versus enemy Leper/Juggler, with Kill Command, Hounds, Explosive and Misdirection in hand. C1 scored Hounds above Kill Command, then discarded the completed comparison when an unrelated Misdirection response was unsupported. C2/Y1 retain Hounds. Conditional 12-sample continuations: original Kill Command **5/12**, Hounds **11/12**, Explosive **10/12**. `adaptive-action-audit.json` links the exact mechanism and actions. This is evidence for a local decision repair; adaptive sampling and conditioned hands prevent a general win guarantee. It is not certified as the first important error in the source game.

Other small-sample apparent gains shrank: different Juggler-removal attack orders became 8/12 versus 8/12. Reports explicitly label first causal errors unresolved. Larger conditional diagnostics were used to validate the local-root fix and to reject unjustified extra response complexity; they were not converted into arbitrary fitted config weights.

## One untouched three-arm confirmation

80 new shared seeds × six core opponents × both seats × three frozen versions = 2,880 games. Another 20 seeds × fourteen old-pool opponents × both seats × three versions = 1,680. All 4,560 scheduled games completed. The fixed primary is 0.5 × Astra mean + 0.5 × Bot2 mean; Bot1 is separate. Shared seeds are paired experimental clusters, not a promise of identical future hands/RNG after divergence.

| Core opponent / metric | K0 | K1 | Y1 |
|---|---:|---:|---:|
| astra-board-proxy | 108/160 (67.50%) | 114/160 (71.25%) | 110/160 (68.75%) |
| astra-tempo-proxy | 131/160 (81.88%) | 127/160 (79.38%) | 131/160 (81.88%) |
| astra-sticky-proxy | 106/160 (66.25%) | 116/160 (72.50%) | 116/160 (72.50%) |
| bot2-face-proxy | 130/160 (81.25%) | 134/160 (83.75%) | 140/160 (87.50%) |
| bot2-trade-proxy | 132/160 (82.50%) | 132/160 (82.50%) | 136/160 (85.00%) |
| bot1-mage-proxy | 140/160 (87.50%) | 140/160 (87.50%) | 140/160 (87.50%) |
| All six | 747/960 (77.81%) | 763/960 (79.48%) | 773/960 (80.52%) |
| Primary | 76.88% | 78.75% | 80.31% |
| Primary seed-cluster 95% | [73.12, 80.73] | [74.90, 82.50] | [76.56, 83.91] |

| Paired primary comparison | Gain, percentage points | 95% seed interval | Baseline-only / Y1-only wins |
|---|---:|---:|---:|
| Y1 minus K0 | +3.44 | [0.94, 5.94] | 29 / 55 |
| Y1 minus K1 | +1.56 | [-0.05, 3.28] | 13 / 23 |

Intervals use 10,000 resamples of entire shared seed clusters, keeping both seats and all opponents. Y1 has evidence of higher primary performance than K0 on this fixed population; superiority over K1 is not established. The performance bundle cannot be causally allocated to every component. No result supports a 90% population win rate.

Y1 weakest core matchup is Astra-board, **110/160 (68.75%)**, versus K0 108 and K1 114. Astra-sticky is **116/160 (72.50%)**, versus K0 106 and K1 116. Astra totals: K0 345/480, K1 357/480, Y1 357/480. Bot2: 262/320, 266/320, 276/320. The advantage over K1 is concentrated in Bot2; board still needs work.

| Actual turn order, all six | K0 | K1 | Y1 |
|---|---:|---:|---:|
| First | 386/480 (80.42%) | 398/480 (82.92%) | 404/480 (84.17%) |
| Second | 361/480 (75.21%) | 365/480 (76.04%) | 369/480 (76.88%) |

Old pool: K0 **499/560 (89.11%)**, K1 **499/560 (89.11%)**, Y1 **503/560 (89.82%)**. Y1−K0 = **+0.71 pp [−0.89, +2.32]**, with 10 K0-only and 14 Y1-only wins. Worst per-opponent point decline is control-Mage, −5 pp. Practical old-pool and family screens pass; this is not statistical noninferiority.

## Runtime and release gate

All regular game attempts had zero observed illegal actions, policy exceptions, timeouts, unexpected fallbacks or opponent errors. This does not erase injected-fault failures.

| Measurement | P50 ms | P95 ms | P99 ms | Max ms |
|---|---:|---:|---:|---:|
| K0 pure policy, final core | 0.63 | 35.92 | 97.29 | 323.59 |
| K1 pure policy, final core | 1.75 | 61.71 | 147.36 | 377.69 |
| Y1 pure policy, final core | 2.99 | 82.55 | 227.64 | 768.96 |
| K0 complete cold CLI, 60 normal states | 68.17 | 308.57 | 318.84 | 318.84 |
| K1 complete cold CLI, 60 normal states | 145.50 | 331.05 | 338.95 | 338.95 |
| Y1 complete cold CLI, 60 normal states | 145.34 | 327.68 | 492.72 | 492.72 |
| Extracted Y1, 24 largest chance trees | 549.68 | 855.76 | 920.04 | 920.04 |

Complete CLI includes interpreter/import/worker startup, reads, history/features, search and output. Warm full file-to-action P50/P95/P99/max: 42.02/256.13/265.35/424.70 ms, with initialized imports. The unified soft deadline remains ≤1.5 s from Python entry and supervisor termination around 1.8 s; OS scheduling/startup means this is not hard real time. Host model/network/tool latency is unmeasured.

**Unresolved Y1 fault:** the stale-observation/hung-worker test exceeded its 2.5-second outer wait while other experiments ran, then the harness tried to remove a directory while the subprocess was still active. Original failure log and all 200 reserved short cases remain charged. The improved harness records each result before cleanup and isolates/kills only its own test process group. Eight follow-ups all returned refresh, no stale action, maximum 1.826 s. Scheduling/startup delay is a hypothesis, not a proven explanation. Therefore reliability fails and no champion pointer is updated.

**Frozen K0 fault:** malformed injected history raises JSONDecodeError in the old supervisor. It was not repaired or excluded from reporting. K1/Y1 pass that case. K0 normal cold timing was separately recovered after the interrupted test. This is a known robustness limitation of the retained historical champion, not a normal-match loss or authorization to silently substitute an unconfirmed artifact.

Y1 standard 74-case check passed, including long history, malformed input, worker crash/hang, saved fallback and sequence changes; its expected-fault maximum was 1.822 s. The separate >2.5 s test above still blocks release. `trace-divergence.json` shows the one ZIP reproduction action difference: identical decision state apart from game/deadline metadata, chance search hit a wall deadline in one run and retained its legal baseline. Both outcomes matched.

## Budget, artifact and continuation

Charged **12,421/16,000** full attempts: 12,334 completed full games, including 1,380 conditional continuations and two clients, plus 87 conservatively retained reservations. Short branches: **33,190/80,000**. Cumulative experiment wall time, summing overlap conservatively: **21.93/360 minutes**. Final games/reproduction/client used 4,610 of the 5,000-game reserve. Production search nodes are separately recorded in final telemetry. Across 313,452 scheduled policy decisions, normal-match defects were zero.

No new paid API/model call was made. Current Codex-session billing/token cost is not exposed and is not estimated. Development/orchestration timing is recorded separately in `time-accounting.json`; experiment time is not mislabeled as the entire task duration.

Research ZIP: `dist/secret-hunter-krush-y1.zip`, **42,070 bytes** compressed / 110,972 unpacked. SHA-256: `e1427f2acdf25da33b97bb6ea6ea9d57b9c56d13722224213149f621c40f9084`. Extracted source SHA-256: `47ea1ba9392507e7eaa28cd4384056cb2acee11c57d7253db95099f3ef924735`. One skill folder; Python and JSON/Markdown only, no logs, hidden state, weights, environment, installer or external service. Actual extracted ZIP passes course format/deck validation, reproduces **48/48 outcomes and 47/48 complete traces**, and passes two no-model official clients with **64/64 exact current-sequence actions**. No new model-host test was performed; historical H7 host evidence is separate.

Recommended release remains `dist/secret-hunter-program.zip`, SHA-256 `1e417ecdb29773b57a15eedf2bd70f617c7260ecdfa28614bc2ad7e21b877a4d`, and the historical champion pointer remains byte-identical. Y1 is valuable research evidence and a future parent, not a promoted release.

Next highest-value hypothesis: instrument full cold-start/supervisor/worker timing under controlled contention, determine why the observed timeout escaped the local target, and validate a narrow runtime fix on a new pre-registered round. Strategy continuation should preserve the verified root-local Juggler/Hounds repair and address the weak Astra-board matchup with public observations, rather than infer hidden cards or add a larger generic defensive penalty.

Resume with `.venv/bin/python -m development.secret_hunter_dgm.resume`. It restores lineage, hashes, seed reservations and budget without resetting K0. Codex must still read the checkpoint and propose code. See `REPRODUCE.md` for exact replay commands and fresh-clone limitations. No main merge or course submission occurred.
