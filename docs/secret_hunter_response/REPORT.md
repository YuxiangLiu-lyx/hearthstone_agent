# Public-response Secret Hunter research report

**Result: no candidate is promoted. Retain frozen Y1 as the research baseline.** The fixed original Krush/Misdirection/Ooze deck is unchanged, byte for byte and in the original order. E1 is a reproducible mechanics research artifact. B3/C3 test the selective endpoint/response/recovery idea, but a better predictive error does not automatically produce better play.

## Fixed boundary and research question

Base commit `8b9a1f30ca16a3587b04f15472d855e14c26a8ce`; independent branch `research/secret-hunter-response-20261111`. Deck SHA-256 `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`; 30 Hunter cards including EX1_543, EX1_533 and EX1_066. Both frozen Y1 and K1 submit exactly that ordered list. The existing H7 champion pointer and old releases remain untouched. Course engine, six core and fourteen guardrail opponents are hash-protected. Local proxies are not real Astra or official hidden Bot2.

Question: does a public-history response model improve complete decisions on own turns 2–4 and independent seed win rates? Learned logistic models and old co-occurrence counts were evaluated offline only, as course rules forbid shipping model weights. Runtime C3 is an independently written, conservative scenario mechanism informed by the calibration study, not a deployed learned classifier. Thus this round tests the legal bounded adaptation, not the exact fitted predictor.

## Prediction and source mechanisms

See [STAGE1.md](STAGE1.md), [SOURCES.md](SOURCES.md) and [calibration.json](calibration.json). The requested ZIP was absent; frozen Y1 generated 480 new development games (397 wins), yielding 2,962 public next-turn responses. Fit/calibration/test split by complete source seed has 1,804/575/583 rows (24/8/8 groups). No seed, game ID, proxy label, hidden hand, future event or outcome is a predictor. Multi-label events can co-occur and do not represent mutually exclusive hidden hands.

| Offline feature set | Test Brier | ECE5 | Own turns 2–4 Brier |
|---|---:|---:|---:|
| Class + mana | 0.13234 | 0.02859 | 0.13491 |
| + board/resources | 0.12706 | 0.03892 | 0.12724 |
| + public history | 0.12833 | 0.03452 | 0.12834 |
| Class/mana + filtered Bigram | 0.13254 | 0.02776 | 0.13567 |
| Board/history + Bigram | 0.12855 | 0.03701 | 0.12867 |

State features reduce Brier by 0.00528, paired seed 95% interval [-0.00831, -0.00215], but worsen calibration and both Bot2 proxy errors. Adding history or the external prior does not improve the richer model. The old Bigram has 352/1,814 IDs in the course pool, then filters class and mana. It is a co-occurrence count, not a hand probability. Leave-one-proxy-out and label-level calibration tables are retained.

PredatorMCTS `getPredictionMap` / `simulateOpponentWithPrediction` motivated shortlisting turn endpoints, sparse public-compatible responses and our continuation. Cardsformer motivated separate verified transition labels and terminal outcome labels; its CUDA/pythonnet/SabberStone environment, tensor schema and changed card stats do not cheaply match this course. The 2020 Sebastian Miller source motivated action-count-dependent depth. Source versions, author attribution, license findings and exact hashes are recorded; no external source code, binary, engine or checkpoint is in the ZIP.

## Complete-turn evidence and autonomous iterations

The improved sampler produced 72 distinct source positions across all six opponents, original wins/losses, both turn orders and turns 2–4. 59 positions include alternatives with a shared first action. Four plans × three selection plus five independent validation futures = 2,304 terminal continuations, zero errors. Selected plans win 263/360 versus Y1 257/360, paired source-seed interval [+0.00, +4.62] pp. These are conditional source-hand diagnostics, not a general strategy effect.

Replay evidence: case 16, seed 960014, seat 1, turn 3, Freezing Trap instead of Hyena wins 4/20 versus 1/20 in fresh extension samples; promising but weak. Case 8, seed 960003, seat 1, turn 4, attacking then ending instead of the full Hounds/development plan wins 11/20 versus Y1 19/20. Case 13 initially loses every validation future under all alternatives; extension produces 2/20 versus 0/20, so it is not proven unwinnable. Case 2 loses its apparent advantage after extension (5/20 each). [STAGE2.md](STAGE2.md), archived engine prefixes and `replay_case.py` reproduce both positive and negative evidence.

The first 24-case pilot was biased toward two Astra proxies because of lexicographic sampling. It remains archived; the corrected sampler was actually used for the 72-case study. Shared public-state gates ensure a plan replans after a random result rather than blindly following a cached sequence. Three selection futures remain noisy; terminal continuations use Y1 and may undervalue plans needing a stronger future policy.

| Child | Parents | Evidence-driven change | Decision |
|---|---|---|---|
| B1 / C1 | Y1 | Full endpoint / visible reply / known-hand recovery; C adds sparse response scenarios | Rejected after 76/75 wins vs Y1 81/96 |
| B2 / C2 | B1 / C1 | Bound recovery influence; prevent advancing the future hand clock twice | 79/80 wins; retained for diagnosis |
| B3 / C3 | B2 / C2 | Preserve baseline root attribution; inherit Coin/random-followup coverage guard | 81/81 pilot wins, later retention regression |
| E1 | Y1 | Only add opposing public end-turn effects to existing response valuation | Selected before final; tied Y1 development primary |

The C2-only pilot loss exposed a concrete generation defect: Coin/end-turn was compared against a full competing plan while Coin/Companion was omitted. After fixing that defect, remaining B3/C3 retention regressions fall into evaluation/continuation unresolved (6 and 7 Y1-only wins, respectively), not certified simulator errors. The first source-mechanism check caught an incorrect Mortal Coil damage assumption; it was fixed before matches. Full diagnostics distinguish first divergence from a causally proven first mistake.

## Paired development and final results

| Arm | Pilot wins / 96 | Screen wins / 288 | Retain wins / 384 | Combined development primary |
|---|---:|---:|---:|---:|
| Y1 | 81 | 258 | 321 | 85.09% |
| B3 | 81 | 260 | 317 | 84.70% |
| C3 | 81 | 259 | 316 | 84.44% |
| E1 | 81 | 259 | 320 | 85.09% |

Final core: 80 new source seeds (961000–961079), both seats and six opponents, 960 games per arm. E1 is the sole promotion-eligible challenger. B3/C3 were frozen before opening as additional core diagnostic ablations; no post-final selection occurs. Old-pool confirmation uses 20 other new seeds (962000–962019), 560 games each for Y1/K1/E1. Main metric weights Astra and Bot2 families equally; Greedy Mage is reported separately. Bootstrap resamples whole paired seed clusters.

| Arm | Core wins / 960 | Overall | Primary | Primary seed 95% | Actual first / 480 | Actual second / 480 |
|---|---:|---:|---:|---|---:|---:|
| Y1 | 787 | 81.98% | 81.56% | 78.18%–84.84% | 418 | 369 |
| K1 | 775 | 80.73% | 80.62% | 77.14%–84.01% | 407 | 368 |
| E1 | 786 | 81.88% | 81.46% | 78.12%–84.69% | 419 | 367 |
| B3 | 785 | 81.77% | 81.30% | 77.76%–84.64% | 417 | 368 |
| C3 | 786 | 81.88% | 81.35% | 77.81%–84.69% | 417 | 369 |

| Paired contrast | Primary gain | Seed-cluster 95% | Left-only / right-only primary wins |
|---|---:|---|---:|
| K1 minus Y1 | -0.94 pp | [-2.55, +0.68] pp | 25 / 17 |
| E1 minus Y1 | -0.10 pp | [-0.73, +0.52] pp | 4 / 3 |
| B3 minus Y1 | -0.26 pp | [-0.99, +0.47] pp | 6 / 3 |
| C3 minus Y1 | -0.21 pp | [-1.04, +0.57] pp | 6 / 4 |
| C3 minus B3 | +0.05 pp | [-0.47, +0.52] pp | 2 / 3 |
| E1 minus K1 | +0.83 pp | [-0.83, +2.50] pp | 19 / 26 |

| Core opponent (160 each) | Y1 | K1 | E1 | B3 | C3 |
|---|---:|---:|---:|---:|---:|
| astra-board-proxy | 115 | 113 | 114 | 113 | 114 |
| astra-sticky-proxy | 112 | 111 | 113 | 111 | 113 |
| astra-tempo-proxy | 139 | 136 | 138 | 138 | 137 |
| bot1-mage-proxy | 143 | 139 | 143 | 144 | 144 |
| bot2-face-proxy | 140 | 140 | 140 | 140 | 140 |
| bot2-trade-proxy | 138 | 136 | 138 | 139 | 138 |

| Old pool | Wins / 560 | Overall |
|---|---:|---:|
| Y1 | 519 | 92.68% |
| K1 | 504 | 90.00% |
| E1 | 519 | 92.68% |

E1 old-pool difference versus Y1: +0.00 pp, paired interval [+0.00, +0.00] pp. All fourteen per-opponent comparisons, both-seat summaries, family results and error counts are in `final-results.json`.

No superiority or 90% population win-rate claim is supported. The response experiment fails to establish the intended gain; fitted prediction quality, shallow counterfactual success and match strength remain distinct measurements. Final seeds have not been reused for policy edits.

## Runtime, reliability and packaging

- runtime-y1: 60 cold CLI states, P95 0.251s, P99/max 0.344s; 74 total normal/fault cases, max 1.821s; illegal 0, over 2s 0.
- runtime-e1: 60 cold CLI states, P95 0.264s, P99/max 0.360s; 74 total normal/fault cases, max 1.834s; illegal 0, over 2s 0.
- runtime-release: 60 cold CLI states, P95 0.270s, P99/max 0.363s; 74 total normal/fault cases, max 1.832s; illegal 0, over 2s 0.
- Extracted ZIP: 24 complex chance states, P95 0.639s, P99/max 0.699s; no fallback/error/illegal action.
- y1-isolated-stale: 8/8 correct refreshes with hung worker and changed observation, max 1.847s; no stale action. Four cases include Python-entry instrumentation.
- e1-isolated-stale: 8/8 correct refreshes with hung worker and changed observation, max 1.844s; no stale action. Four cases include Python-entry instrumentation.
- release-isolated-stale: 8/8 correct refreshes with hung worker and changed observation, max 1.847s; no stale action. Four cases include Python-entry instrumentation.
- All normal recorded match runs: 11136 games, 315900 own decisions; illegal actions (both players) 0, timeouts 0, fallbacks 0, pure-policy over-2s 0.
- Extracted E1 replay: 48/48 outcomes match, 47/48 both-player traces match. The one difference is an inherited time-capped turn search (same public state; one search stopped at depth 3, the other reached depth 6); both actions were legal and the outcome matched. This is recorded, not erased.
- Two official no-model client games: 55/55 actions relayed exactly. No real Luna/Haiku host test, network/model call during play, official submission or real Astra run.
- The earlier historical Y1 concurrent timeout remains an unresolved historical incident. Successful independent reruns establish this round’s observed reliability, not a hard real-time guarantee.

Verified mechanisms include Misdirection retarget samples, Explosive/Freezing order and Bow durability, Juggler/Hounds (96/96 differential outcomes), random-result fallback, the 9-mana Krush route after two public Taunts are cleared, temporary buffs and Imp Master end effects. Unsupported Misdirection response trees and Imp Master/Juggler end triggers remain explicit conservative exclusions; they are not modeled as fixed mitigation. The sampled chance planner is never a guaranteed-lethal proof.

Research ZIP: `dist/secret-hunter-krush-response-e1.zip` (42114 bytes), SHA-256 `42892b6e917fdfc7cfac97c93335a61df528a3f20b2638d2547e7b81b670340b`. Extracted source hash `9ea5a43260c928000531c2422a55353f7e876624b3013b89296703da976e7b8a`. One skill folder, Python only, no weights/Bigram table/environment/logs; course-format validation passed. It is not recommended to replace Y1.

## Budget and continuation

Charged 14599/16,000 full attempts and 39906/80,000 short branches; cumulative experiment wall time 35.37 minutes (sum across scheduled runs), elapsed research wall time 44.26 minutes at audit. Failed/unused reservations remain charged. The macOS spawn guard failure reserved 160 continuations but ran none; corrected under a fresh ledger entry. The initial two Mortal Coil mismatch cases also remain recorded. No external paid model/service cost was incurred; Codex session token/currency usage is unavailable.

The strongest next hypothesis is a continuation-consistent value comparison over equally represented complete plans and public-compatible multi-card responses. Do not simply deepen the current evaluator: it already reverses strong Y1 decisions without reliable terminal benefit. First verify candidate completeness and separate transition mismatch from evaluation error on the archived positions. Keep learned models offline unless course rules change.

See [REPRODUCE.md](REPRODUCE.md). Resume with `.venv/bin/python -m development.secret_hunter_response.resume`; this loads the existing lineage, protected hashes and consumed/reserved seeds. A future Codex round must propose changes; the scheduler is not an autonomous policy generator.
