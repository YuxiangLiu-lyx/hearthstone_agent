# Whole-turn evidence and its limits

All terminal labels below come from the unchanged course engine and frozen local proxy policies. Hidden hands, remaining decks, source seed, and terminal outcome are offline audit/label fields. The tested policy receives only the normal public observation and public history. Both routes in a pair start with identical sampled hands/decks and initial RNG; only the tested own turn changes. Later own turns use frozen Y1, and the opposing policy is the same within the pair.

## Explosive Trap, Harvest Golem, and the missing Secretkeeper

The recovered public replay is a previously known C2 game, translated by replacing its two Arcane Shot slots with the original deck's Misdirection and King Krush. It is explicitly a synthetic transfer fixture, not a new original-deck game. The complete legal turn differs after its first two actions:

| Replanning with engine-trap-v2 | Verified continuation |
| --- | --- |
| Kill Command on Harvest Golem | Kill Command on Harvest Golem |
| Steady Shot | Steady Shot |
| End turn | Play Secretkeeper, then end turn |

Twenty-four new paired future hypotheses were evaluated for each frozen opponent policy, using the existing compatible sticky deck template. No original 0066a30 outcome is counted as a new result.

| Proxy policy | Replan | Continue | Flips | Regressions | Preserve resources |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zoo | 12/24 | 15/24 | 6 | 3 | 16/24 |
| Tempo | 16/24 | 19/24 | 3 | 0 | 16/24 |

These are 192 terminal trajectories across four routes, **one public source game and one source seed group**. The two proxy variants and 48 futures are not 48 independent source games. Zoo sample 0 is a reproducible flip: the baseline loses after 40 total engine actions, and the continuation wins after 42. `continuation-evidence.json` records exact verification of every public state, action, and terminal winner.

The wider natural-sample training set did not support a general Keeper rule. It improved from 27/44 to 29/44 on 11 training source groups, but declined from 37/40 to 36/40 on ten held-out groups. That rule was rejected. A legal plan completion is not automatically a better plan.

## Why the old continuation prototype rarely triggered

The 96 archived engine-trap-v2 Astra games contain 2,626 main-phase decisions. There are 59 games with an active Explosive Trap and 19 with both the trap and an enemy deathrattle, but only two actual targeted-deathrattle opportunities. One is a one-action Loot Hoarder line; the other breaks Harvest Golem but has an attack later in the plan. The original prototype rejects both. It did not merely lose an otherwise applicable plan in its executor. These are the archived development traces, not the separate 144-game historical continuation screen: that screen's paired result rows are present, but its per-decision observations are absent from the supplied archive, so the reported zero-trigger count cannot be independently recounted for those exact 144 games.

E4 accepts a validated deterministic attack tail for the second case. The stored replay shows a legal change in attack/hero-power order. That alone is not a win-rate gain. In a new 72-game whole-game screen E4 had one game with a cache hit, zero changed actions, and identical outcomes to engine-trap-v2. E2 changed one game in the preceding 96-game screen and zero in the 72-game screen. Both repaired the famous CLI replay, but encounter frequency remained the limiting factor.

The broader E3 executor changed actions in 72/96 development games and lost four parent wins without gaining any. Its first divergences included a face attack overriding a fresh trade and a hero power overriding fresh minion development. All were legal, verified continuations. The failure class is evaluation/commitment, not only simulation or legality. E2 consequently follows fresh replanning except when a verified legal minion play would otherwise be omitted by an immediate end turn.

## Knife Juggler versus Dire Wolf versus face

The corrected sample contains 19 source groups with both enemy targets, including two training cases with no current hand or board slot. A next-turn draw is still possible; zero current hand does not prove zero response resources.

| Route objective | Training wins, 44 futures / 11 groups | Held-out wins, 32 futures / 8 groups |
| --- | ---: | ---: |
| Current replanning | 31 | 17 |
| Prefer Juggler removal | 31 | 18 |
| Prefer Wolf removal | 30 | 14 |
| Prefer face damage | 31 | 15 |

The two resource-limited training cases yielded 4/8 for every route. There were no matching resource-limited held-out cases. This is a coverage gap: the data do not establish a low-resource rule under which Wolf removal wins more often. The one-point held-out Juggler advantage is descriptive and was not used to select a rule after seeing validation. Train-only fitting selected unchanged replanning.

The route labels are objectives, not assertions that a particular target was always killed. In all 76 natural futures, the Juggler objective actually targeted Juggler 60 times; the Wolf objective targeted Wolf 60 times. Other actions still adapt to the observed state and legal moves. Detailed coverage is in `continuation-evidence.json`.

## Amani: attack routes, cheap prevention, and conditional stress

The grouped sample includes 23 Amani source cases. The corrected stress test restricts to 20 cases with an undamaged, unsilenced, non-frozen Amani that can benefit from Coil. Three already-damaged source cases are not applicable, producing 60 explicit exclusions across four futures and five routes. The strict test completes 400 terminal trajectories. Empty-hand cases are handled by conditioning the next deck draw on Coil without changing hand size or card multiset.

On the same 20 source cases, each half has ten source groups and 40 paired futures per route. In this grouped table, "no Coil" means absent from the initial response hand and ordinary next draw; a later Life Tap or deathrattle draw is not excluded. A separate strict no-Coil response control is reported below.

| Route objective | Train no Coil | Train natural | Train forced Coil | Held-out no Coil | Held-out natural | Held-out forced Coil |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current replanning | 27 | 28 | 25 | 31 | 31 | 31 |
| Prefer Highmane | 26 | 26 | 28 | 31 | 31 | 32 |
| Prefer Taunt | 26 | 26 | 28 | 31 | 31 | 32 |
| Prefer Bow/Amani removal | 23 | 23 | 25 | 31 | 31 | 32 |
| Prefer trades into Amani | 25 | 25 | 23 | 29 | 29 | 32 |

The ordinary natural labels, not forced stress labels, select strategies. These objectives frequently collapse to other actions because the required cards are absent. For example, actual Highmane plays occur in only four held-out futures, and actual hero attacks into Amani in twelve of the forty held-out Bow-objective futures. The matching Highmane/Taunt totals are not independent evidence that those specific plays are equivalent.

Two exact natural-sample replays demonstrate why full executed routes matter:

- `amani-h007`, validation sample 100: current policy spends Kill Command on Amani and loses. The alternate develops Leper Gnome and Snake Trap, preserves Kill Command, and wins. Despite its internal `bow_amani` objective name, no Bow is played. Exact full replay lengths are 68 and 56 actions.
- `amani-031`, validation sample 100: current policy plays Animal Companion, then Secretkeeper attacks Voidwalker, and wins. The legal alternative equips Bow, attacks Voidwalker with the hero, sends Secretkeeper face, and loses. Exact replay lengths are 45 and 33 actions. This is a concrete example of an available alternative making a winning game worse.

Ten sampled natural source cases lost every tested route and every paired future. They are listed in `continuation-evidence.json`; this does not prove that no winning route exists outside the searched set.

## Post-freeze explicit Amani diagnostic

The original known Amani replay has nine own health, six mana, three ready Hounds, and Highmane, Bow, Animal Companion, and Coin in hand. The enemy has six visible attack and an undamaged Amani. Four executable public reactive routes were specified, with immediate guaranteed lethal still taking precedence:

1. Highmane and Hounds face.
2. One Hound removes a one-attack, one-health enemy, then Highmane and the remaining Hounds face.
3. Bow attacks Amani, then current replanning completes the turn.
4. Animal Companion first, then replan after observing the random companion. Taunt is not guaranteed or forced.

On the first 12 paired futures per proxy, the cheap one-Hound trade preserves ordinary wins (22/24) and increases forced-Coil wins from 12/24 to 24/24. The forced gain is entirely against Tempo: Zoo already wins 12/12 after the forced response, while Tempo moves from 0/12 to 12/12. Bow gives 23/24 under stress but 21/24 in natural samples; Companion gives 20/24 under stress and 21/24 naturally. This illustrates both proxy dependence and the cost of excessive defense.

The first 12 natural samples contain zero next-draw Coil hypotheses. Natural sampling was therefore expanded to 48 futures per proxy as an explicitly post-freeze diagnostic. Two of the 48 shared hidden samples then have Coil as the next draw. Over the resulting 96 paired continuations, cheap trading gives 91 wins versus 90 (two flips, one regression), Companion 89, and Bow 88. The cheap-trade gain comes from Tempo (44 to 45); Zoo stays 46/48. The entire explicit diagnostic finishes 720 terminal trajectories, with zero excluded jobs. It is not used to modify or select the frozen candidate. This one known source game cannot establish a population improvement.

A further 120 terminal continuations explicitly exclude Coil plays for the first opposing response, including after additional draws. This is a controlled offline response ablation, not a changed benchmark opponent or a natural-policy label. The same twelve futures per proxy yield replan/Highmane/cheap trade 22/24 each, and Bow/Companion 21/24 each. The strict no-Coil result therefore agrees with the initial availability-conditioned control in this replay.

## Independent final regression: a minion can enable Enrage

The frozen final core batch changes E2's action in three of 480 games. Two remain wins for both versions; the third, `(astra-sticky-proxy, 31100027, seat 1)`, changes an engine-trap-v2 win to a loss. There are no incremental core flips.

At sequence 14, own turn four (engine turn 7), the current public state has one mana, no friendly minions, and an undamaged enemy Amani. The fresh parent chooses end turn. E2 reuses a previously verified Leper Gnome play. On the opponent's response, Amani attacks the Gnome and becomes 5/2. In the parent branch it instead attacks face while remaining 2/3. Later turns diverge; the parent wins on engine turn 17, and E2 loses on turn 16.

A differential check from that exact public state confirms that the existing public model and original engine both predict Gnome death, two deathrattle face damage, and a 5/2 Amani. This is evidence against treating the failure as a missing Enrage effect. The harmful choice is commitment overriding the fresh endpoint evaluation. Detailed observed actions, next-turn public states, and the verified prediction are in `final-core-action-changes.json`. No candidate was changed after this final seed was inspected; it must be marked development data if a future strategy is tuned to this example.

The preceding sequence 13 exposes a more specific search cause. `turn_search.plan` stores only one endpoint for each first action, chosen by its **pre-response** score. Both full plans below begin with the same Hound attack into Dire Wolf:

| Full remaining route | Pre-response value | After-response value | Weighted comparison value |
| --- | ---: | ---: | ---: |
| Kill Wolf, then end turn | -22.5603 | -22.9603 | -22.9003 |
| Kill Wolf, then play Gnome | -20.3607 | -24.6927 | -24.0429 |

Higher is better. The one-endpoint-per-first-action map retains Gnome because its pre-response value is higher, discarding the better defended endpoint before opponent simulation. Once the Wolf attack has executed, end turn and Gnome become different root actions, and fresh replanning can compare them correctly. The extra opponent response computation takes only one versus two response nodes in this case. Retaining a few resource-distinct full-turn endpoints per first action, within the same total response budget, is therefore the most concrete next search hypothesis. This is a read-only final diagnosis, not an unvalidated change to the release candidate.
