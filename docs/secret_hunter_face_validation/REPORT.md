# Frozen F2 validation

**Reject F2 as a replacement; retain Y1.** F2 loses 21 net core games and 10 net old-pool games on untouched paired seeds. Reliability passes, but the preregistered performance gates fail. This is evidence against this implementation of the requested face-oriented style, not evidence that every favorable trade should be taken.

Parent commit: `dd25aa61002272c4312f5352949749fbadc2e10c`. Preregistration commit: `5b4b40c`. Branch: `research/secret-hunter-face-validation-20261112`.

## Design and frozen boundaries

The user's new request to validate F2 authorizes this bounded validation run. A separate ledger caps this work at 1,600 full executions, 2,000 short reservations and 3,600 accumulated experiment seconds. The exhausted original 16,000-attempt ledger is byte-for-byte unchanged. No strategy parameter or policy was changed after opening these seeds.

Y1 and F2 each play 40 new source seeds (985000–985039), all six existing core proxies and both physical seats: 480 games per arm. The old pool uses 10 new source seeds (986000–986009), its 14 existing opponents and both seats: 280 per arm. Actual first/second is audited independently of physical seat. All pairs are complete. Both arms use the same original course engine, max-turn setting, opponent versions and six-worker execution harness, in separate sequential process pools.

The primary endpoint is 0.5 times the Astra-family mean plus 0.5 times the Bot2-family mean. Its denominator is 400 games per arm; the separate Mage proxy contributes only to the 480-game total. Intervals use 10,000 bootstrap draws of complete source-seed groups, retaining all opponents and both seats. Individual opponent and seat intervals are descriptive, without a multiple-comparison claim. Ten old-pool seed groups give relatively coarse guardrail estimates. These are local proxies, not an evaluation of the real Astra service.

The ordered original 30-card deck is unchanged, including King Krush `EX1_543`, Misdirection `EX1_533` and Acidic Swamp Ooze `EX1_066`. Deck SHA-256: `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`.

F2 is tested directly from the extracted research ZIP. Source hash: `f055c456c8f315ab4c6134bc1f194cc6fc45f5e4ac2f0837fba2b963792a99f4`. Y1 source hash: `47ea1ba9392507e7eaa28cd4384056cb2acee11c57d7253db95099f3ef924735`.

## Paired outcomes

Differences and intervals are percentage points, F2 minus Y1.

| Population | Y1 | F2 | Difference | Seed-group 95% interval |
|---|---:|---:|---:|---:|
| Core total | 405/480 (84.38%) | 384/480 (80.00%) | -4.37 | [-6.46, -2.29] |
| Primary: equal Astra/Bot2 families | 83.85% | 79.90% | -3.96 | [-6.35, -1.56] |
| Astra family | 188/240 (78.33%) | 169/240 (70.42%) | -7.92 | [-11.67, -4.58] |
| Bot2 family | 143/160 (89.38%) | 143/160 (89.38%) | +0.00 | [-3.75, +3.75] |
| Mage proxy | 74/80 (92.50%) | 72/80 (90.00%) | -2.50 | [-7.50, +2.50] |
| Core actual first | 208/240 (86.67%) | 198/240 (82.50%) | -4.17 | [-7.08, -1.25] |
| Core actual second | 197/240 (82.08%) | 186/240 (77.50%) | -4.58 | [-7.92, -1.25] |
| Old pool total | 251/280 (89.64%) | 241/280 (86.07%) | -3.57 | [-6.79, -0.71] |

Among core pairs, F2 turns 10 Y1 losses into wins but turns 31 Y1 wins into losses. In the old pool, the corresponding counts are 6 and 16. No draw, missing pair, harness error or forfeited game is hidden in these totals.

| Core opponent | Y1 | F2 | Difference | Seed-group 95% interval |
|---|---:|---:|---:|---:|
| astra-board-proxy | 59/80 (73.75%) | 53/80 (66.25%) | -7.50 | [-13.75, -1.25] |
| astra-sticky-proxy | 58/80 (72.50%) | 50/80 (62.50%) | -10.00 | [-17.50, -3.75] |
| astra-tempo-proxy | 71/80 (88.75%) | 66/80 (82.50%) | -6.25 | [-12.50, +0.00] |
| bot1-mage-proxy | 74/80 (92.50%) | 72/80 (90.00%) | -2.50 | [-7.50, +2.50] |
| bot2-face-proxy | 74/80 (92.50%) | 73/80 (91.25%) | -1.25 | [-6.25, +2.50] |
| bot2-trade-proxy | 69/80 (86.25%) | 70/80 (87.50%) | +1.25 | [-5.00, +7.50] |

| Old-pool opponent | Y1 | F2 | Difference | Seed-group 95% interval |
|---|---:|---:|---:|---:|
| adversarial-priest-v1 | 16/20 (80.00%) | 16/20 (80.00%) | +0.00 | [-20.00, +20.00] |
| adversarial-zoo | 18/20 (90.00%) | 15/20 (75.00%) | -15.00 | [-30.00, +0.00] |
| aggressive-hunter | 19/20 (95.00%) | 17/20 (85.00%) | -10.00 | [-25.00, +0.00] |
| aggressive-paladin | 19/20 (95.00%) | 18/20 (90.00%) | -5.00 | [-15.00, +0.00] |
| control-mage | 17/20 (85.00%) | 18/20 (90.00%) | +5.00 | [+0.00, +15.00] |
| control-priest | 19/20 (95.00%) | 19/20 (95.00%) | +0.00 | [+0.00, +0.00] |
| historical-mage | 17/20 (85.00%) | 15/20 (75.00%) | -10.00 | [-25.00, +0.00] |
| official-mage | 16/20 (80.00%) | 16/20 (80.00%) | +0.00 | [-15.00, +15.00] |
| search-paladin | 17/20 (85.00%) | 16/20 (80.00%) | -5.00 | [-15.00, +0.00] |
| search-shaman | 18/20 (90.00%) | 18/20 (90.00%) | +0.00 | [-15.00, +15.00] |
| tempo-paladin | 18/20 (90.00%) | 17/20 (85.00%) | -5.00 | [-20.00, +10.00] |
| tempo-warlock | 19/20 (95.00%) | 18/20 (90.00%) | -5.00 | [-15.00, +0.00] |
| value-priest | 18/20 (90.00%) | 18/20 (90.00%) | +0.00 | [+0.00, +0.00] |
| value-warlock | 20/20 (100.00%) | 20/20 (100.00%) | +0.00 | [+0.00, +0.00] |

`official-mage` is the existing Greedy guardrail. Actual first in the old pool is 126/140 for Y1 versus 121/140 for F2; actual second is 125/140 versus 120/140.

Promotion required at least +1 percentage point on the primary endpoint, a strictly positive paired lower bound, no family drop worse than 5 points, no old-pool overall drop worse than 3 points, no old opponent drop worse than 10 points, and reliability success. F2 fails all five performance gates, including a 15-point drop against adversarial-zoo. It passes the reliability gate. The performance conclusion does not depend on the small client smoke sample.

## What the preference actually changed

The 480 core games contain 4,640 Y1 attacks, of which 3,088 target face (66.55%). F2 makes 4,543 attacks, of which 2,984 target face (65.68%). Two-mana Hero Power uses increase from 48 to 66. Therefore the selected historical trade-to-face audit did not generalize to a higher full-game face-attack share.

There are 396 first own-action differences, each reached at the same public state in both arms. The first difference is trade-to-face in 57 games (2 F2-only wins, 2 Y1-only wins), face-to-trade in 47 (0 and 4), and minion-to-Hero-Power in 19 (2 and 3). These are post-hoc diagnostic categories, not isolated causal treatment estimates. Changes to development, action ordering and later state distributions matter; a face bonus can change search ranking and pruning as well as the final attack target.

The F2 endpoint bonus depends on damage already dealt and a state-dependent safety/engine guard. Its discontinuity can change preferences for removing an engine or reaching a different endpoint. This is a code-based hypothesis, not a validated explanation of every lost game. The observed early Hero Power substitutions give a more concrete next target: preserve profitable development and measure aggression among otherwise comparable attack allocations, while valuing pressure that can actually survive and attack next turn. No such revised candidate was tuned on these validation seeds.

## Three replayable examples

The complete original action traces for both arms are in `recorded-games.json.gz`, with per-step course-engine public-state hashes. They are reproduced twice: once while building the archive and once from the archive alone. All six terminal outcomes match. These replays are charged separately and are not additional independent wins. They compare the complete recorded policies and realized random outcomes, not a single-action intervention with an identical continuation policy.

1. **Useful face damage:** bot2-face-proxy, seed 985018, seat 1, our four-mana turn. Both arms have 20 health against 22 and the same friendly board. Y1 swings Bow at Leper Gnome, ends at 17 health with the opponent still at 22, and later loses. F2 swings face, ends at 20 against 19, and later wins with 2 health remaining. It saves the immediate contact and deathrattle damage and advances its clock; the enemy minion remains a cost.
2. **High-value removal was worth taking:** astra-tempo-proxy, seed 985010, seat 1, our three-mana turn. Our two 1/1 Hounds face a 3/2 Flame Imp and a 1/1 Leper Gnome, with both heroes at 27. Y1 spends both Hounds killing Imp and eventually wins. F2 sends both Hounds face for two damage. At our next turn its Hounds are gone and enemy board attack is 8, versus 5 in Y1's branch. F2 dies on global turn 12 with the opponent still at 19; Y1 wins on global turn 15 with 3 health left.
3. **Early damage displaced development:** bot2-face-proxy, seed 985013, seat 2, our two-mana turn. Y1 plays Hyena and trades Leper Gnome into Timber Wolf. F2 first uses Hero Power and ultimately also trades away its Gnome. F2 buys two extra face damage that turn but ends with no minion; Y1 keeps Hyena. Y1 subsequently develops Companion/Houndmaster pressure and wins on global turn 11 at 18 health. F2 loses on global turn 15, three damage short. This illustrates why a generic damage bonus is broader than the intended attack-target preference.

Detailed first actions, public observations, turn endpoints and terminal states are in `first-differences.jsonl.gz`, `cases.json` and `cases-repeated.json`. All chosen case seeds now count as inspected validation data. Using them to design a follow-up would make them development data; a new candidate needs a new untouched confirmation set.

## Runtime, faults and artifact integrity

All 1,520 paired games complete through the original engine: 43,101 own decisions, zero illegal actions on either player, zero timeouts, policy/opponent errors, normal fallbacks or decisions over two seconds. This fast harness calls the Python policy directly, so those times are not full CLI latency.

The exact extracted F2 artifact separately passes 74 full CLI cold/fault cases. Its 60 cold calls have P95 0.252 seconds, P99/max 0.354 seconds. Across the full suite, including injected hung workers, maximum time is 1.825 seconds; no illegal output or call over two seconds occurs. Existing twelve mechanism fixtures and the guaranteed Krush lethal check remain applicable because the F2 source hash is unchanged; they were not counted as new validation games.

Isolated stale-observation/hung-worker tests pass 8/8 for Y1 and 8/8 for F2, each with maximum below 1.844 seconds. No worker pool ran during these checks. All request a fresh observation and none returns a stale action. This rerun retains the historical concurrent-load failure; measured success is not a hard real-time guarantee.

Two official local no-model client games on seeds 987000–987001 produce 97 decisions with zero relay deviations, worker errors, fallbacks, illegal actions or timeouts. They split 1–1 against Greedy; this is only a transport smoke test. Maximum publication-to-action time is 0.382 seconds. The package also passes `hs-arena validate --no-game`.

The integrity audit verifies 4,480 inherited protected files, 339 installed engine files, both frozen policies and original decks, and every ZIP file hash against its extracted counterpart. The audit initially assumed ZIP paths had no top-level directory; that assertion was corrected to match the actual `secret-hunter-face-f2/` prefix. No game, policy or package changed for this read-only verifier fix.

## Artifacts, cost and reproduction

F2 remains an archived rejected research artifact, not the recommended release. Its ZIP is unchanged: `dist/secret-hunter-krush-face-f2.zip`, SHA-256 `62b3bc975407224fe52ad0b853ad35588e2c3fc3b5ae5c033b83584b4d20eb0f`. Keep `dist/secret-hunter-krush-y1.zip` as the validated baseline; no champion pointer or published package was replaced.

This validation charges 1,534/1,600 full executions (1,520 paired games, two client games, twelve recorded-game replay executions), 144/2,000 short reservations, and 232.517/3,600 accumulated experiment seconds. Every reservation is closed. No paid API or external model was used; Codex session cost is unavailable.

Committed evidence includes raw result JSONL, exact schedules/configs and summaries for all four arms; grouped comparisons; public first differences; complete replay actions; runtime/client audits; frozen hashes; lineage and seed checkpoint. Original full per-game observation directories remain ignored. Statistical reproduction and the selected game replays do not require them. Rebuilding the exhaustive behavioral inventory does require those ignored logs or a rerun.

In the existing Python 3.11 / hs-arena 0.2.2 course environment:

```sh
.venv/bin/python -m development.secret_hunter_face_validation.analyze
.venv/bin/python -m development.secret_hunter_face_validation.verify
.venv/bin/python -m development.secret_hunter_face_validation.cases --name local-replay-1 --out /tmp/f2-recorded-replay.json
```

Use a unique replay name; it conservatively charges six full executions to the separate validation ledger. It replays recorded actions and checks the original engine's legal transitions and state hashes, rather than rerunning time-bounded policy search.

The four executed match commands were:

```sh
.venv/bin/python -m development.secret_hunter_face_validation.run --arm Y1 --population core
.venv/bin/python -m development.secret_hunter_face_validation.run --arm F2 --population core
.venv/bin/python -m development.secret_hunter_face_validation.run --arm Y1 --population guardrail
.venv/bin/python -m development.secret_hunter_face_validation.run --arm F2 --population guardrail
```

They intentionally refuse to overwrite completed experiments. To regenerate full matches, create a separate clean worktree at preregistration commit `5b4b40c`, attach the same course environment as `.venv`, and execute those commands there; that commit has the empty dedicated ledger and no validation results. Keep this evidence checkout intact. Shared seed values match starting conditions, but diverging actions can consume randomness differently. Time-bounded policy traces may vary with machine scheduling, so archived-action replay is the exact reproducibility check.

Additional commands used here:

```sh
.venv/bin/python -m development.secret_hunter_face_validation.behavior
.venv/bin/python -m development.secret_hunter_face_validation.cases --build --name build-recorded-cases
.venv/bin/python -m development.secret_hunter_face_validation.runtime_checks --candidate development/secret_hunter_face/release/secret-hunter-face-f2 --out docs/secret_hunter_face_validation/runtime-f2.json
.venv/bin/python -m development.secret_hunter_face_validation.fault_check --candidate development/secret_hunter_face/release/secret-hunter-face-f2 --name f2-isolated-stale
.venv/bin/python -m development.secret_hunter_face_validation.fault_check --candidate development/secret_hunter_response/candidates/Y1 --name y1-isolated-stale
.venv/bin/python -m development.secret_hunter_face_validation.client
.venv/bin/hs-arena validate development/secret_hunter_face/release/secret-hunter-face-f2 --no-game
```

Existing reservation names and the completed archive cannot be reused. These commands document the executed checks; normal metric and integrity regeneration uses the first two commands above without consuming additional games.
