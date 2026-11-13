# Original Krush Secret Hunter: completed turn-plan iteration

Do not promote E2-finish-minions. Keep engine-trap-v2 as the next research parent and Y1 as the cumulative-gain control.

Every win rate in this report is against the existing frozen **local proxy opponents**. The main result is the independent frozen-code comparison below. Historical reproduction, adaptive development, selected conditional continuations, and post-freeze diagnostics are kept separate. A positive point estimate whose interval crosses zero is not described as a confirmed population gain.

## Independent final comparison

Final core seeds 31100000–31100039 and guard seeds 31200000–31200007 were reserved before development. After selecting E2, exact fingerprints were frozen before opening these seeds. All three arms use the same seeds, both seats, and unchanged opponent versions. Each arm completes 480 core plus 224 guard games; all 2,112 games use the complete Python CLI for every in-game atomic decision. Deck submission is separately checked through the actual CLI and course deck validator.

| Version | Astra | Bot2 | Greedy | Core total | Astra + Bot2 equal-family score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Y1 | 184/240 (76.67%) | 142/160 (88.75%) | 72/80 (90.00%) | 398/480 (82.92%) | 82.71% |
| engine-trap-v2 | 190/240 (79.17%) | 147/160 (91.88%) | 71/80 (88.75%) | 408/480 (85.00%) | 85.52% |
| E2-finish-minions | 189/240 (78.75%) | 147/160 (91.88%) | 71/80 (88.75%) | 407/480 (84.79%) | 85.31% |

Strict pairing uses `(opponent, seed, seat)`. The primary interval resamples all opponents and both seats together within each of 40 complete seed groups (10,000 bootstrap samples). Greedy is excluded from the primary score.

| Comparison | Primary gain, 95% seed-group interval | Astra gain, interval | Core gain, interval | Core flips / regressions |
| --- | ---: | ---: | ---: | ---: |
| Y1 -> engine-trap-v2 | +2.81 pp [-0.42, +6.67] | +2.50 pp [-1.67, +7.08] | +2.08 pp [-1.04, +5.62] | 26 / 16 |
| Y1 -> E2-finish-minions | +2.60 pp [-0.62, +6.46] | +2.08 pp [-2.08, +6.67] | +1.87 pp [-1.25, +5.42] | 26 / 17 |
| engine-trap-v2 -> E2-finish-minions | -0.21 pp [-0.62, +0.00] | -0.42 pp [-1.25, +0.00] | -0.21 pp [-0.63, +0.00] | 0 / 1 |

A zero-width bootstrap interval from identical observed outcomes does not establish policy equivalence, especially when the new action almost never triggers. Source selection and these fixed proxies limit generalization. No final outcome was used to change the candidate.

| Core opponent | Y1 | engine-trap-v2 | E2-finish-minions |
| --- | ---: | ---: | ---: |
| astra-board-proxy | 58/80 (72.50%) | 61/80 (76.25%) | 61/80 (76.25%) |
| astra-sticky-proxy | 56/80 (70.00%) | 59/80 (73.75%) | 58/80 (72.50%) |
| astra-tempo-proxy | 70/80 (87.50%) | 70/80 (87.50%) | 70/80 (87.50%) |
| bot1-mage-proxy | 72/80 (90.00%) | 71/80 (88.75%) | 71/80 (88.75%) |
| bot2-face-proxy | 73/80 (91.25%) | 74/80 (92.50%) | 74/80 (92.50%) |
| bot2-trade-proxy | 69/80 (86.25%) | 73/80 (91.25%) | 73/80 (91.25%) |

| Actual move order | Y1 | engine-trap-v2 | E2-finish-minions |
| --- | ---: | ---: | ---: |
| First | 207/240 (86.25%) | 212/240 (88.33%) | 211/240 (87.92%) |
| Second | 191/240 (79.58%) | 196/240 (81.67%) | 196/240 (81.67%) |

## Guardrail regression

The fourteen existing guard opponents use eight new complete seed groups, both seats. These seeds were also reserved before development. Small subgroup estimates are descriptive.

| Version | Guard total |
| --- | ---: |
| Y1 | 192/224 (85.71%) |
| engine-trap-v2 | 190/224 (84.82%) |
| E2-finish-minions | 190/224 (84.82%) |

- Y1 -> engine-trap-v2: -0.89 pp [-2.23, +0.00]; 2 flips, 4 regressions.

- Y1 -> E2-finish-minions: -0.89 pp [-2.23, +0.00]; 2 flips, 4 regressions.

- engine-trap-v2 -> E2-finish-minions: +0.00 pp [+0.00, +0.00]; 0 flips, 0 regressions.

| Guard opponent | Y1 | engine-trap-v2 | E2-finish-minions |
| --- | ---: | ---: | ---: |
| adversarial-priest-v1 | 14/16 (87.50%) | 14/16 (87.50%) | 14/16 (87.50%) |
| adversarial-zoo | 12/16 (75.00%) | 10/16 (62.50%) | 10/16 (62.50%) |
| aggressive-hunter | 13/16 (81.25%) | 12/16 (75.00%) | 12/16 (75.00%) |
| aggressive-paladin | 15/16 (93.75%) | 15/16 (93.75%) | 15/16 (93.75%) |
| control-mage | 11/16 (68.75%) | 12/16 (75.00%) | 12/16 (75.00%) |
| control-priest | 15/16 (93.75%) | 15/16 (93.75%) | 15/16 (93.75%) |
| historical-mage | 13/16 (81.25%) | 14/16 (87.50%) | 14/16 (87.50%) |
| official-mage | 12/16 (75.00%) | 12/16 (75.00%) | 12/16 (75.00%) |
| search-paladin | 14/16 (87.50%) | 14/16 (87.50%) | 14/16 (87.50%) |
| search-shaman | 14/16 (87.50%) | 14/16 (87.50%) | 14/16 (87.50%) |
| tempo-paladin | 13/16 (81.25%) | 13/16 (81.25%) | 13/16 (81.25%) |
| tempo-warlock | 15/16 (93.75%) | 15/16 (93.75%) | 15/16 (93.75%) |
| value-priest | 16/16 (100.00%) | 15/16 (93.75%) | 15/16 (93.75%) |
| value-warlock | 15/16 (93.75%) | 15/16 (93.75%) | 15/16 (93.75%) |

## Action coverage and incremental effect

| E2 game-level stage | Core / 480 | Guard / 224 |
| --- | ---: | ---: |
| One of the three public contexts observed | 327 | 72 |
| A deterministic continuation saved | 480 | 222 |
| A next action passed the state/legal checks | 479 | 221 |
| A different legal continuation existed | 384 | 177 |
| An action actually changed after the fresh-plan guard | 3 | 0 |

Context counts and continuation counts describe different entry conditions, so the context row is not a strict denominator for all cached plans. A different valid continuation can be rejected by E2 in favor of fresh replanning. Exact paired flips/regressions are reported above; cache hits by themselves are not improvements.

## Historical reproduction and development decisions

The supplied `hearthstone_astra_0066a30.zip` restored commit `0066a304931ae89415e6eff2a6735c2d6026b7d0`; every embedded checksum passed. Rebuilding engine-trap-v2 reproduces fingerprint `ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`. Reaggregation gives the reported Astra 176/240 versus 188/240, 19 flips and seven regressions; complete core 389/480 versus 406/480. A 24-game old-seed full-CLI audit matches every archived outcome. Three original public turns were replayed through the full CLI for restored and new versions.

| Completed development screen | Y1 | engine-trap-v2 | E2 | E3 broad continuation | E4 narrow trap continuation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eight seed groups, 96 games/arm | 93 | 91 | 91 | 87 | Not run |
| Six new seed groups, 72 games/arm | 47 | 52 | 52 | Rejected | 52 |

E3 changed actions in 72/96 games and lost four parent wins without gaining any. E2 changed one game in the first screen and zero in the second; its outcomes matched its parent throughout both. E4 had one cache-hit game and zero action changes in its 72-game screen. E2 was selected as a narrow research challenger, not predeclared a winner.

Before the authentic archive arrived, independent R-series reconstructions were tested separately: one-seed pilot 10/12 each for Y1/R0/R1; four-seed screen Y1 43/48, R0 42/48, R1/R4 41/48. R2/R3 were built but not fully screened; R5/R6 screening was interrupted on recovery of the actual parent. These are not engine-trap-v2 results. All parent snapshots and rejected variants remain in `development/secret_hunter_turn_plans/lineage.json`.

## Complete-turn labels and learned rules

The corrected grouped sample contains 63 public source cases from original-deck proxy wins and losses. Source seed determines the split across arms, opponents, both seats, and related states. Four paired future samples per source compare the current turn with alternate full turns; validation uses disjoint source groups and future indices. Subsequent own turns use frozen Y1, and the opponent remains frozen. Legal reactive replanning follows observed random outcomes.

- Corrected main continuation batch: 1,960 terminal trajectories; 60 initial-hand-only forced-Coil hypotheses excluded. A later strict stress batch fixes empty-hand next-draw conditioning and excludes already-enraged Amani: 400 terminal trajectories, 60 explicitly inapplicable jobs.
- Natural labels alone fit constants or one public-feature threshold, with a one-win complexity penalty and a minimum two-win training improvement. Keeper improved 27/44 to 29/44 on training groups but fell from 37/40 to 36/40 on held-out groups. It was rejected. Knife/Wolf and Amani fitting selected unchanged replanning.
- The recovered Golem case adds 192 terminal continuations: verified Secretkeeper completion improves 28/48 to 34/48, with nine flips and three regressions. It is one source game, not 48 independent examples.
- An explicitly post-freeze Amani diagnostic adds 720 terminal continuations. A cheap one-Hound trade preserves Highmane and gives 91/96 natural wins versus 90/96 (two flips, one regression), and 24/24 forced-Coil wins versus 12/24. The natural improvement is only one win in one known source game; it was not used to alter the final strategy. Bow gives 88/96 naturally despite strong forced defense.

A further 120 strict no-Coil response controls (including additional draws) preserve 22/24 wins for replan and cheap trading, versus 21/24 for Bow/Companion. The five corrected/diagnostic sets therefore contain 3,392 terminal trajectories. Preliminary runs and interrupted jobs remain separately named in the full archive and are excluded from these corrected totals. Eight complete stored-action replays reproduce every public state and terminal winner, including a positive Golem completion, a natural win harmed by a legal Bow route, and cheap prevention of the forced Amani lethal. Ten selected natural cases lost every tested route. See [CASE_STUDIES.md](CASE_STUDIES.md) for executed sequences, all three problem-specific tables, sampling caveats, and coverage gaps.

The observed bottleneck is primarily when to trust a generated full turn: legal deterministic commitment can override a better fresh decision. The famous missing follow-up is real but rare. The archived 96-game trap audit has only two targeted-deathrattle opportunities, both rejected by the old gate. The separate historical 144-game screen lacks per-decision logs in the supplied archive, so its zero-trigger claim is distinguished from the independently recounted 96-game funnel.

In the final core regression `(astra-sticky-proxy, 31100027, seat 1)`, E2 completes a Leper Gnome play after fresh replanning prefers end turn. The opponent uses Amani to kill it, enabling a 5/2 Amani. The existing public model predicts this visible trade exactly. The earlier search keeps only one endpoint per first action: its pre-response score prefers Gnome (-20.36 versus -22.56), but the response-adjusted score prefers stopping (-22.90 versus -24.04). Both plans begin with the same Wolf trade. This identifies loss of a useful endpoint before response evaluation, followed by harmful commitment, rather than a missing Enrage rule. No final seed was used to modify the candidate; see `final-core-action-changes.json`.

## Reliability and course compliance

| Version | Final games | Full CLI calls | P95 | P99 | Maximum | Illegal / timeout / fallback / over 2 s |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Y1 | 704 | 20377 | 0.151 s | 0.270 s | 0.808 s | 0 / 0 / 0 / 0 |
| engine-trap-v2 | 704 | 20453 | 0.155 s | 0.287 s | 0.780 s | 0 / 0 / 0 / 0 |
| E2-finish-minions | 704 | 20451 | 0.156 s | 0.285 s | 0.787 s | 0 / 0 / 0 / 0 |

The E2 cold/concurrent/fault suite has 41 calls, 0 invalid outputs, and 0 calls over two seconds. Ordinary P99/max is 0.700 s; all fault-injected calls peak at 1.823 s. There are 0 ordinary fallbacks and 2 expected injected-failure fallbacks. A worker that publishes and then hangs returns its checked checkpoint. Eight stale-observation tests return refresh requests without submitting an old action.

After all heavy game workers stopped, the isolated stale-observation rerun completed 8 calls with 0 invalid outputs and 0 calls above two seconds (maximum 1.841 s). Six additional Juggler/Hounds CLI calls all choose legal Hounds plays, with no fallbacks and maximum 0.215 s.

The deck is the exact ordered Y1 list, SHA-256 `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`, including Krush `EX1_543`, Misdirection `EX1_533`, and Ooze `EX1_066`. Six actual CLI deck submissions pass the course validator. Their intentional prepared-deck startup fallback flags are separate from in-game failure fallbacks. All 329 installed course Python files and all protected opponent/pool fingerprints remain unchanged.

Five inherited mechanism tests pass: Wolf aura removal, Coil activating Amani, Krush attacking after a nine-mana Taunt clearance, secret order/Bow/Misdirection, and Juggler plus Hounds. Four Explosive Trap differential cases also match the original engine. Both frozen ZIPs pass course static validation after extraction and preserve the exact tested source fingerprints. They contain one skill folder, Python code and small text configuration only. No environment, binary, external model, hidden-information sampler, or research dataset is shipped. A live Luna relay match was not completed or counted; validation uses the complete Python CLI with local proxies.

## Recommendation and next experiment

Do not promote E2-finish-minions. Keep engine-trap-v2 as the next research parent and Y1 as the cumulative-gain control.

Preserve face pressure as the default. First test retaining a few resource-distinct full-turn endpoints per first action, rather than discarding all but the highest pre-response score; keep the total response budget comparable. The next tactical hypothesis is a cheap exchange that removes just enough opposing attack to survive a possible Amani self-ping while retaining Highmane or burn. Count the next draw even when the opponent currently has zero cards. Collect more independent original-deck source games before fitting that condition; forced stress success alone is insufficient. For Knife/Wolf, collect genuinely resource-limited held-out cases and examples where removing Wolf unlocks profitable attacks. Broader forced commitment should remain rejected.

Code, twelve immutable candidate snapshots, final freeze, exact deck audit, development lineage, aggregate data, raw local evidence archive, replay commands, latency/fault tests, and ZIP fingerprints are provided. See [REPRODUCE.md](REPRODUCE.md), [data-manifest.json](data-manifest.json), [final-results.json](final-results.json), and `dist/secret-hunter-turn-plans/manifest.json`. The research branch began at `c2bc11f0a88f2e20dcd951a056042bcb40426041`; implementation checkpoint `110c406` preserves the tested candidates. No submission or remote publication was performed.

The study completes 3,124 full games across historical rechecks, development, partial superseded screens, and independent validation. There are 5,759 charged offline continuation attempts including rejected/superseded runs, under the recorded 6,000-attempt cap. Final core throughput is 27.7 games/minute and guard throughput 27.3 games/minute at three workers. Final aggregation occurs 2.42 hours after the four-hour-budget study began. No training worker is intentionally left running after delivery.
