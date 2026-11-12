# Win-rate follow-up: deterministic coverage and complete endpoint retention

**No new release is promoted. Keep Y1.** This follow-up ran 1,360 additional normal matches, 24 paired terminal continuations, and two official no-model client games. W3 ties Y1 at 395/480 on fresh core seeds and 51/56 in the old pool. The original ordered deck, engine and opponent pools remain unchanged.

This work answers the request to run win rates and optimize after the previous response-model iteration failed. The previous round did run win-rate comparisons: Y1 won 787/960, C3 786/960, and E1 786/960. Its prediction improvements did not become policy improvements. This follow-up uses concrete generation failures to make three smaller candidates, screens their actual wins, and evaluates the frozen survivor on new seeds. It also fails to establish a win-rate gain.

## Frozen boundary and experiment design

Parent: `af7f231d50f6298800a14561e159e8481c77c1e8`, clean before creating `research/secret-hunter-winrate-20261111`. The earlier reference remains `8b9a1f30ca16a3587b04f15472d855e14c26a8ce`. No merge or course submission was performed.

The deck SHA-256 is `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`, including EX1_543, EX1_533 and EX1_066 in the original order. Actual deck submission, all 30 cards, limits, and class are checked. Integrity auditing verifies 4,480 inherited files and 339 installed engine files. All previous frozen candidate hashes and both opponent pools are preserved.

The [plan](plan.json) reserves core seeds 981000–981039 and guardrail seeds 982000–982001 before implementation. These are disjoint from the prior checkpoint. Development reuses the existing Y1 96-game baseline at seeds 960100–960107, with both seats and all six core opponents. Two initial candidates were planned; a logged amendment adds a third 96-game screen after the first two regress, before opening any new final seeds. All candidate attempts remain in the ledger. [final-freeze.json](final-freeze.json) freezes W3 before its 480-game final. No final data changed its code or parameters.

The primary metric is the equal average of the Astra family mean and Bot2 family mean. Mage is reported separately. These are fixed local proxies, not real Astra or the official hidden evaluation. Learned predictors, seeds, opponent identities and future information do not enter online decisions.

## Failures, changes and development wins

| Candidate | Parent | Change | Wins / 96 | Primary | Decision |
|---|---|---|---:|---:|---|
| Y1 | Frozen baseline | Existing search | 81 | 84.896% | Retain |
| W1 | Y1 | Admit deterministic Knife Juggler deployment into existing response-mode turn search | 78 | 80.208% | Reject broad change |
| W2 | W1 | Keep two distinct endpoints per root before the existing six-endpoint reply shortlist; unchanged budgets | 79 | 82.292% | Reject broad change |
| W3 | Y1 | Admit a standalone Juggler-versus-affordable-Bow comparison on turns 2–4, excluding Coin and immediately affordable random summon followups | 81 | 84.896% | Freeze for independent confirmation |

W1 exposes a real coverage omission. `tactical_model.options` and `transition` exclude every Juggler in response mode, even when its deployment triggers no random effect. If Juggler ranks first, `turn_search.plan` exits without comparing a Bow removal plan. Fifteen official-engine transition cases validate deterministic deployment; eleven assertions preserve rejection of subsequent random summons or a second Juggler.

However, globally widening coverage makes other comparisons incomplete. The W1 development results contain four Y1-only wins and one W1-only win. One first divergence plays Secretkeeper before Juggler at five mana, losing a random summon opportunity; two other losses change an Explosive Trap decision into Juggler development. These first divergences identify unresolved evaluation or continuation issues; they do not prove that one action alone caused each terminal loss. The full public states and diagnostics are retained in [w1-failures.json](w1-failures.json).

W2 addresses a different concrete omission: a root can have a good pre-reply endpoint and a different endpoint that is better after the visible reply. Keeping only the highest pre-reply endpoint discards the second plan. In archived balanced case 57, Y1 attacks with Hyena and then buffs it with Houndmaster. W2 buffs first and then attacks, delivering two more face damage. It is a legal, replayed improvement to that sequence, but W2 still loses two more full development games than Y1. A local improvement is insufficient to promote a policy.

W3 narrows the coverage change and preserves the other Y1 paths. It still checks guaranteed lethal first, returns only a legal current root action, and replans after observation. It adds no hidden-hand reconstruction, fitted weights or extra runtime dependency. All 14 inherited mechanism tests pass, including the existing Secret, random-combo and lethal boundaries.

## Replayed Bow example and fresh conditional futures

Balanced case 33 comes from development seed 960028, seat 1, own turn 3, originally a loss against the Mage proxy. The public board contains an enemy 3/2 Sorcerer's Apprentice and no friendly minion. The hand contains Bow, Houndmaster, Juggler, Snake Trap and Explosive Trap.

The course-engine prefix is reconstructed from the earlier archived actions. Y1 plays Juggler and ends. W3 equips Bow, attacks Apprentice with the hero, then ends. Both traces are legal and saved with the initial public observation and per-action public hashes in [witness-y1.json](witness-y1.json) and [witness-w3.json](witness-w3.json).

The prior small conditional sample favored the fixed Bow plan 5/5 against Y1 3/5. After W3 was frozen, twelve new paired future samples, seeds 983000–983011, give Y1 10/12 and the fixed Bow plan 11/12: one Y1-only win, two Bow-only wins. This is one conditional source position, with source hidden hands retained inside the offline course engine and future deck order/RNG resampled. It does not establish a general win-rate gain. The same public Y1 continuation policy follows both initial plans; public-state gates abandon stored prefixes when an observed result differs. No plan is selected using these new futures. Raw data: [continuation-bow.json](continuation-bow.json).

## Independent final results

| Core opponent | Y1 wins / 80 | W3 wins / 80 |
|---|---:|---:|
| Astra board proxy | 55 | 55 |
| Astra sticky proxy | 56 | 56 |
| Astra tempo proxy | 74 | 74 |
| Bot2 face proxy | 71 | 71 |
| Bot2 trade proxy | 65 | 65 |
| Mage proxy | 74 | 74 |
| **Total** | **395/480 = 82.292%** | **395/480 = 82.292%** |
| **Primary: Astra/Bot2 equal family means** | **81.042%** | **81.042%** |

Actual first player: both 207/240 (86.25%). Actual second player: both 188/240 (78.333%). Every paired outcome is identical, including all 56 old-pool games. The old pool result is 51/56 (91.071%) for each; the existing official Mage/Greedy entry is 3/4 for each. Two additional official no-model client smoke games against Greedy both win, but are not pooled into the policy comparison.

The primary paired gain is 0.000 percentage points. Resampling the complete 40 seed groups yields a degenerate interval [0.000, 0.000] because every observed paired outcome is identical. **This does not demonstrate equivalence or remove uncertainty on other seeds.** The old-pool check has only two groups and provides limited regression coverage. Full paired, opponent and actual-turn-order tables are in [final-results.json](final-results.json).

The new gate activates on only five decisions in five core games. Four activations retain the original root. Only one changes the first action; that game is a win under both policies. Four other games have different action traces with the new gate inactive and different time-bounded search truncations. All five first divergences have identical public starting states and unchanged outcomes. These four timing-sensitive differences are not attributed to the policy repair. [final-decision-changes.json](final-decision-changes.json) preserves the evidence.

This explains the plateau: the broad fixes change enough decisions to regress, while the safe restriction reaches too few decisions to improve this sample. The next useful hypothesis is complete, comparable coverage of random development followups, with continuation-consistent scoring. Increasing search depth or adding response hypotheses before fixing that comparison is not supported by these results. No further candidate was tuned on final seeds.

## Reliability, artifact and budget

The 1,360 normal new matches make 37,725 own decisions, with zero illegal actions for either player, zero timeouts, zero fallbacks and zero policy decisions above two seconds. The W3 core pure-policy maximum is 0.776 seconds.

The exact extracted ZIP passes official `hs-arena validate --no-game`. Sixty cold CLI invocations have P95 0.248 seconds, P99 0.336 seconds and maximum 0.336 seconds. Across all 74 cold/fault cases the maximum is 1.831 seconds, including deliberately hung workers. Eight isolated stale-observation plus hung-worker tests return refresh requests, with zero stale actions, zero outer timeouts and maximum 1.853 seconds. Normal fallback counts are zero; injected fault cases intentionally exercise fallback paths. The prior historical concurrent-load Y1 timeout remains documented and is not erased by these independent passes.

The two extracted-artifact official client games produce 50 exact current-sequence relays, with zero deviations, worker errors, illegal actions or timeouts. No hosted Luna/Haiku or real Astra match was run. [integrity.json](integrity.json), [runtime-release.json](runtime-release.json), [client-audit.json](client-audit.json), and the [isolated stale report](../secret_hunter_response/winrate-release-isolated-stale.json) contain raw checks.

The remaining 1,401 charged full attempts were used as follows: 288 development matches, 960 fresh core matches, 112 old-pool matches, 24 conditional continuations, two client games, and 15 conservatively reserved mechanism-fixture attempts. The cumulative ledger is **16,000/16,000 full attempts**, 42,438/80,000 short reservations, and 2,348.10/21,600 cumulative experiment seconds. No full-game budget remains. Failed and unused reservations from the earlier round remain charged. [checkpoint.json](checkpoint.json) extends the prior seed archive; the old checkpoint is preserved.

Research artifact: `dist/secret-hunter-krush-winrate-w3.zip`, 42,474 bytes, 24 competition files, no training data or weights. SHA-256: `3db718b39ec0901c9d7a019d7e7f2af6077cef5530f31619e26c58aa30edb997`. Frozen W3 source hash: `aae8e1ccfa7f797fcc4c063e143c49c4f19e092557df00fa6bbb61d5fd78a0e2`.

**Recommended baseline remains** `dist/secret-hunter-krush-y1.zip`, SHA-256 `e1427f2acdf25da33b97bb6ea6ea9d57b9c56d13722224213149f621c40f9084`. W3 is a reproducible research artifact, not a winning replacement. The previous champion pointer is unchanged. See [REPRODUCE.md](REPRODUCE.md) for audit and replay commands and [archive.json](archive.json) for the candidate lineage.

Implementation and experiment commit: `796767a46486d7346ac4b11bcd18078bebcf1e6d`. The final metadata commit is available in branch history. The whitespace check reports one inherited trailing-space line in each copied `improvements.py`; all four copies are byte-identical to frozen Y1 and were preserved to keep evaluated source hashes stable. Newly authored files have no whitespace-check findings.
