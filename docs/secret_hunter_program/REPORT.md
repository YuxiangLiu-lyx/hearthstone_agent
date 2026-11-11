# Secret Hunter program research — final report

F2 is the local program champion. On its separately frozen fresh block, the primary 13-opponent macro improved from **79.62% to 86.15%**, a paired **+6.54 percentage points**, seed-cluster 95% interval **+1.54 to +11.54**. There are only **10 seed clusters** in this correction confirmation; percentile bootstrap intervals are unstable at that size. No evidence establishes a >90% primary win rate.

All strategy is Python. The official skill host still uses Luna medium solely as a relay. No runtime model strategy comparison, extra model, new opponent, self-play, deck change, formal submission or remote push was performed. Existing champions and research assets remain preserved.

## Results and provenance

The exact requested deck and existing 14-opponent pool were frozen before comparison. The official Greedy Mage is reported separately from 13 equally weighted validation opponents, not counted twice. Both seats are matched for each opponent and seed. Same seed does **not** guarantee identical later draws or random effects after policies diverge. These opponents do not estimate Mystery Bot, Astra or classmates.

| Cohort | Baseline W/N (rate; descriptive Wilson 95%) | F2 W/N (rate; descriptive Wilson 95%) | Paired gain pp (seed-cluster 95%) |
|---|---|---|---|
| Primary macro | 207/260 (79.62%; 74.30–84.06) | 224/260 (86.15%; 81.43–89.83) | +6.54 (+1.54, +11.54) |
| Official Greedy Mage | 18/20 (90.00%; 69.90–97.21) | 18/20 (90.00%; 69.90–97.21) | +0.00 (-15.00, +15.00) |
| All 14 equally weighted | 225/280 (80.36%; 75.31–84.59) | 242/280 (86.43%; 81.92–89.95) | +6.07 (+1.43, +10.71) |

F2 primary single-version seed-cluster 95% interval: **80.00–91.92%**. Wilson intervals above are descriptive and do not account for seed clustering. All F2/B1 final draws and voids were zero. F2 won 123/140 when first and 119/140 when second.

| Opponent | B1 W–L–D | B1 rate (Wilson 95%) | F2 W–L–D | F2 rate (Wilson 95%) | Paired gain pp (95%) |
|---|---|---|---|---|---|
| adversarial-priest-v1 | 12–8–0 | 60.00% (38.66–78.12) | 16–4–0 | 80.00% (58.40–91.93) | +20.0 (+5.0, +35.0) |
| adversarial-zoo | 14–6–0 | 70.00% (48.10–85.45) | 14–6–0 | 70.00% (48.10–85.45) | +0.0 (-25.0, +30.0) |
| aggressive-hunter | 16–4–0 | 80.00% (58.40–91.93) | 17–3–0 | 85.00% (63.96–94.76) | +5.0 (+0.0, +15.0) |
| aggressive-paladin | 17–3–0 | 85.00% (63.96–94.76) | 20–0–0 | 100.00% (83.89–100.00) | +15.0 (+0.0, +40.0) |
| control-mage | 17–3–0 | 85.00% (63.96–94.76) | 16–4–0 | 80.00% (58.40–91.93) | -5.0 (-35.0, +20.0) |
| control-priest | 15–5–0 | 75.00% (53.13–88.81) | 17–3–0 | 85.00% (63.96–94.76) | +10.0 (+0.0, +25.0) |
| historical-mage | 16–4–0 | 80.00% (58.40–91.93) | 16–4–0 | 80.00% (58.40–91.93) | +0.0 (-15.0, +15.0) |
| official-mage | 18–2–0 | 90.00% (69.90–97.21) | 18–2–0 | 90.00% (69.90–97.21) | +0.0 (-15.0, +15.0) |
| search-paladin | 11–9–0 | 55.00% (34.21–74.18) | 15–5–0 | 75.00% (53.13–88.81) | +20.0 (+5.0, +35.0) |
| search-shaman | 18–2–0 | 90.00% (69.90–97.21) | 17–3–0 | 85.00% (63.96–94.76) | -5.0 (-15.0, +0.0) |
| tempo-paladin | 17–3–0 | 85.00% (63.96–94.76) | 17–3–0 | 85.00% (63.96–94.76) | +0.0 (-20.0, +20.0) |
| tempo-warlock | 19–1–0 | 95.00% (76.39–99.11) | 19–1–0 | 95.00% (76.39–99.11) | +0.0 (-15.0, +15.0) |
| value-priest | 16–4–0 | 80.00% (58.40–91.93) | 20–0–0 | 100.00% (83.89–100.00) | +20.0 (+5.0, +35.0) |
| value-warlock | 19–1–0 | 95.00% (76.39–99.11) | 20–0–0 | 100.00% (83.89–100.00) | +5.0 (+0.0, +15.0) |

The previous frozen F1 block had 30 seed clusters: baseline 654/780 (83.85%) versus F1 684/780 (87.69%), paired +3.85 pp [1.41, 6.28]; Greedy 47/60 versus 50/60. Its all-opponent result was 701/840 versus 734/840. Those results remain valid for F1 but are **not pooled into F2’s fresh confirmation**. The inactive Companion helper later failed an ID-specific audit (Misha/Huffer swapped). F2 corrects two token-table entries, keeps all score/search parameters fixed, and uses new seeds 174000–174009. F1 remains archived with its original hash.

F2 changes only two unused chance-projection constants and version metadata; decision and relay functions are unchanged. All 77 prior official relay decisions were recomputed from their public history using F2 and matched exactly. The correction was still given a separate fresh block; no favorable seeds were selected after seeing results.

## Actual iterations, training and ablation

P0 reused C5’s default Python ranking and covered lethal search. Three hypotheses were implemented and screened: P1 survival/resource scores, P2 finite turn search, P3 conditional Secrets/combo ordering. Two generations of three seeded Gaussian/categorical mutations optimized board, face, hand, risk, width, depth and node limits with elitist retention. T1 was retained; later mutations did not beat it. No paper weights or rarity features were transplanted. Development selection has substantial selection bias.

| Development arm | All W/N | Primary macro | Greedy W/N | Decision |
|---|---|---|---|---|
| P0 | 125/168 | 75.00% | 8/12 | baseline |
| P1 | 124/168 | 74.36% | 8/12 | no gain |
| P2 | 136/168 | 81.41% | 9/12 | retain search direction |
| P3 | 125/168 | 75.64% | 7/12 | no total-win gain |
| T1 | 139/168 | 82.69% | 10/12 | retained parent |
| T2 | 135/168 | 80.77% | 9/12 | not retained |
| T3 | 133/168 | 79.49% | 9/12 | not retained |
| T4 | 136/168 | 80.77% | 10/12 | not retained |
| T5 | 136/168 | 81.41% | 9/12 | not retained |
| T6 | 132/168 | 78.85% | 9/12 | not retained |

| Frozen validation / ablation | All W/N | Primary macro | Greedy W/N | Interpretation |
|---|---|---|---|---|
| B0 | 233/280 | 83.46% | 16/20 | same-deck baseline |
| V1-score | 233/280 | 83.46% | 16/20 | score-only: no stable gain |
| V2-search | 241/280 | 85.77% | 18/20 | search adds 8 wins |
| V3-trained | 242/280 | 86.15% | 18/20 | trained search: selected |
| V4-no-search | 233/280 | 83.46% | 16/20 | remove search: back to baseline |
| V5-combined | 240/280 | 85.77% | 17/20 | all added rules: not retained |
| V6-cache | 240/280 | 85.38% | 18/20 | continuation reuse: disabled |

The strongest evidence is for turn search over the same-deck baseline. Parameter training added only one validation win beyond untuned search; an independent benefit from that tuning is **not established**. Extra survival/Secret rules and planned-continuation reuse were tried and withdrawn. Exact-observation caching remains enabled. Full per-arm intervals, matched ablation differences, code/config/deck/opponent hashes, hypotheses and commands are in `experiments.json`, `training.json`, `validation.json` and each experiment’s `config.json`.

## Reliability, latency and simulation boundaries

Across **195,511 pure-policy decisions**: 0 policy exceptions, 0 emergency fallbacks, 0 internal >2-second decisions. All completed round matches had zero own illegal actions, course timeouts or forfeits. The ordinary conservative ranking path on unsupported effects is a designed policy path, not an emergency fallback.

| Measurement | P50 ms | P95 ms | P99 ms | Max ms |
|---|---:|---:|---:|---:|
| B1 pure, F2 block | 0.089 | 13.050 | 96.212 | 197.200 |
| F2 pure | 0.275 | 22.526 | 119.713 | 275.454 |
| F2 cold supervised CLI | 78.695 | 125.107 | 129.681 | 130.352 |
| F2 CLI including injected faults | 77.692 | 130.352 | 1820.815 | 1821.431 |

F2 searched at most 1950 nodes per decision (1,600 lethal + 350 turn nodes); node P95/P99 were 293/1271. The lethal projector rejected 1325/8587 main observations due to coverage. A bounded-out search is not an absence-of-lethal proof.

Fresh worker component profiling measured P95 parsing 0.141 ms, imports 16.3 ms, decision computation 47.2 ms and serialization 0.020 ms; process startup/exit overhead was 19.4 ms. These component microbenchmarks are separate from the full parent/worker CLI timing. Runtime faults exercise an actual noncooperative sleep, crash, tiny/zero search budgets and saving a better action before a forced kill. The corrected fault harness asserts that a hang really times out. No hard real-time or model-host deadline guarantee is claimed.

The engine checks cover all 19 card IDs, Tracking’s removal/choice/discard, own-only Secretkeeper behavior, Explosive/Freezing ordering and Bow renewal, shields, avoided Secret triggers, Snake capacity, Juggler randomness, Hyena deaths, Ooze, Houndmaster, Highmane, Krush, and compound armor/taunt/weapon lethals. There were 732/732 matching supported one-step projections. That finite check missed an inactive chance-label bug, subsequently fixed by branch-identity tests. Random summons, unknown Secrets and unsupported effects remain outside deterministic proofs. See `DIAGNOSTICS.md` for the complete failure taxonomy and early legal counterfactuals.

## Submission interface and artifacts

The final ZIP is **29,114 bytes compressed / 74,859 bytes uncompressed**, one skill root, standard library plus course package only. SHA-256: `31d62e755cf2d0a51a291b6c23a329d97af8d93f448d56084e91f555775bd173`. Source, ZIP and extracted tree hashes agree. F2’s 56-game extraction reproduction matched all **56 outcomes and 56 complete action traces**; reproduction games are not new holdout samples.

The actual F2 ZIP completed an official no-model client game with 40/40 exact script-to-act transfers. Two earlier F1 official Luna-medium games both completed normally, 77/77 actions exact, with no worker error or fallback. Their total durations were 176.623 and 197.559 seconds; maximum publication-to-act latency was 13.808 seconds. These host timings are separate from the internal Python target. The **exact F2 ZIP was not model-host tested**, because the two-game cap was already reached. Its decision and relay functions are unchanged from F1, and all 77 public decisions match on replay; this is interface-equivalence evidence, not a third smoke test.

Protected-file audit: 455 prior assets and 339 installed runtime files unchanged; all 14 opponents and their dependencies unchanged. 8923 F2 inputs were checked for absence of hidden opponent hand/deck, seed, RNG and opponent identity. Source base commit: `6a7fc2475a17190268594ef2f5940b5b3a62f8f0`; local branch `research/secret-hunter-program-20261111`. New work is identified by frozen content hashes and remains local; no remote publication occurred.

## Budget and course-score scope

Completed **5,997/6,000 full games**: 5,992 pure Python, three official client games and two official relay smoke games. Experimental short continuations, mechanism fixtures and runtime/replay probes are conservatively charged separately: **1,410/20,000 cases**. Internal search nodes are reported independently, not counted as full matches. Initial final reservation was 1,680 games (28%); the final paired blocks and extraction reproductions used 2,352 games (39.2% of the cap). All scheduled matches finished. Research began 05:54:40 UTC; ledger wall time at archival was 51.1 minutes, within four hours.

Current course grading gives five completion points if all six Bot-1 games finish, plus a 0–3 win bonus. Using F2’s Greedy point estimate 90.00% in a simple six-game binomial approximation gives **2.88/3** expected win-bonus points, or **7.88/8** for the known Bot-1 portion conditional on no forfeits. This is a noisy plug-in estimate from 20 games, ignores seat-specific dependence and is not an earned grade. Mystery Bot points, Astra and ladder bonuses are **unknown**. A 90% Greedy point estimate is not statistical evidence of >90% performance.

See [reproduction commands](REPRODUCE.md), [strategy](STRATEGY.md), [sources and license decisions](SOURCES.md), [diagnostics](DIAGNOSTICS.md), `budget.json`, `verification.json` and the repository-level `SECRET_HUNTER_CHAMPION.json`.
