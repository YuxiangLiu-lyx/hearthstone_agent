# Loss evidence and mechanism boundaries

The 38 losses from the previous F2 confirmation are now development data.
`loss-audit.json` preserves their identities and early unsupported public states.
Snake tokens caused 225 unsupported board observations. Among unsupported top
plays were 31 Knife Jugglers, 29 Freezing Traps, 21 Companions, 18 Oozes and 18
Houndmasters. These are observation counts, not 225 distinct games or causal loss
counts. A newly tested rule bug was the missing Snake token in `is_beast`:
a Snake plus Kill Command must do 5 spell damage. The rejected first test report
is retained; the fix passed the official-engine comparison.

The expanded model supports deterministic Secret deployment and own Secretkeeper
growth, Snake tokens, Houndmaster's +2/+2 and Taunt, weapon destruction by Ooze,
playing the first Juggler, and Deadly Shot when exactly one enemy minion exists.
Secrets receive conditional potential, not realized kills/protection. Random
summons with an existing Juggler still stop the exact branch. Hidden Secrets,
unknown draws, multi-target Deadly Shot and Companion remain outside normal
exact turn search. The signature now includes Taunt and active Secret order.

`checks.json` contains 13 successful mechanism tests after the Snake correction.
`new-lethal-checks.json` adds 3 actual engine wins from the Snake/Kill Command,
Secretkeeper/Secret and Houndmaster/Beast lethal fixtures. These are constructed
regressions, not claims that three historical match outcomes changed.
`differential.json` compares 805 legal one-step projections in the 38 historical
losses against engine clones; all match the tested fields. This is useful
coverage, not proof of a complete simulator. Hero HP/armor, ordered bodies,
attack/health, Taunt, shield, freeze, stealth, mana, hand IDs, Secrets and weapons
are compared. Unobserved future draws are never projected.

`diagnostics.json` preserves 10 earliest C1-vs-recorded-F2 divergences and 20
legal current-turn continuations under a common extended-coverage policy.
All endpoints are nonterminal. Several differ only in action order; no changed
historical winner is asserted. For example, `f7f8e4e9b6b04dcd`, turn 14, preserves
4 more own health and reduces enemy health by 2 in the alternative continuation;
this local advantage is not a proven full-game win. Other early changes spend
mana on hero power before a Secret, or choose a different minion, with mixed
resource/board tradeoffs.

Taxonomy: the Snake type/coverage gap is a confirmed rules/model issue; the three
lethal fixtures cover missed-lethal risk. Trade/placement, Secret timing,
resource use and combo order have public divergence evidence but incomplete
causal attribution. Avoidable death, mulligan quality, and draw/random variance
remain unresolved at match level. Budget faults are tested separately. Losses
are not automatically assigned to randomness or to the final turn.

## Frozen confirmation regressions

The final comparison was inspected only after both immutable arms completed.
`regressions.json` contains 12 earliest changes from F2-win/C2-loss pairs;
`weak-matchup-regressions.json` adds four each for Zoo, search Paladin and control
Mage. Each includes two legal current-turn continuations under the same C2
continuation policy. All 48 endpoints across these two files are nonterminal;
these diagnostics explain decisions, not counterfactual match winners.

A specific Zoo case, `268393d8aff7447c`, turn 4, compares Explosive Trap with hero
power against a visible 3/2 Faerie Dragon and 3/2 Flame Imp. Current-turn endpoints
have the same boards and own health, while the hero-power branch gains two face
damage but leaves the Trap in hand. The weighted conditional Secret potential
does not capture the next opponent turn's tactical choice well enough. In
`fc6bd930cf9548ab`, turn 5, the new line equips Bow and removes one Flame Imp,
paying three own health; the old action deploys Explosive Trap against three
small minions. Neither line's eventual superiority is proved by this short
continuation. These cases support researching opponent responses to Secrets,
rather than raising the same static coefficients indiscriminately.

Another case, `12a99366782242d1`, plays Leper before Juggler instead of Juggler
before Leper, losing a possible knife in the tested continuation. This exposes a
boundary in expanded deterministic search: admitting Juggler while rejecting
subsequent random summons can distort the comparison. A future implementation
should keep a guard around unmodelled combo continuations or model their public
chance branches, and must use new holdout seeds. No such post-holdout strategy
change is mixed into this round's frozen result.

The paper-derived ES retained the unmutated C2 parent in every generation.
Large simultaneous normalized mutations did not demonstrate a benefit in this
small three-generation budget. Smaller mutation scales or staged feature groups
are next-round hypotheses, not established improvements. D1's minimal Snake fix
won four extra validation games, but was not separately confirmed on a fresh
final block and is not promoted after observing the C2 failure.
