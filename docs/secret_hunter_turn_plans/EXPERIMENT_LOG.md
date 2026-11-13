# Original Krush turn-plan research log

All win rates in this study are against frozen local proxy opponents. The course engine, ordered 30-card Y1 deck, six-opponent core, and fourteen-opponent guard pool are fixed. The study began at 2026-11-13 02:03:48 UTC with a four-hour wall budget. Final core seeds 31100000–31100039 and guard seeds 31200000–31200007 were reserved before development.

## Recovery and provenance

The initial local repositories and advertised GitHub refs did not contain `0066a30`. GitHub's commit API also returned no matching commit. The user subsequently supplied `hearthstone_astra_0066a30.zip`. Its SHA-256 is `d6983956db34718c42a2e3504b538750d9f4806ee94255369de2dbdf01321dc5`; all embedded checksums passed. The original Git bundle restored `0066a304931ae89415e6eff2a6735c2d6026b7d0` and its research branch.

The exact historical engine-trap-v2 rebuild has fingerprint `ad6194e2024f0375805be8a32c5f78230af7f8d3af06a161dd6748bd89e3abc9`, matching the recovered report. Strict `(opponent, seed, seat)` pairing reproduces Astra 176/240 versus 188/240, 19 gains and 7 losses; full core 389/480 versus 406/480. One old source seed, both seats and all six opponents, was rerun through the full CLI: both arms 11/12, with zero outcome mismatches against all 24 archived rows. Three original public replay turns were also rerun for Y1, engine-trap-v2, and the historical continuation prototype.

## Preliminary reconstruction, retained separately

Before recovery, R0 independently added public whole-turn alternatives to Y1; it is not engine-trap-v2. R1 enabled deterministic continuations. R4 canonicalized absent Boolean flags and hero-power affordability in predicted-state comparisons. These changes address the generic Y1 cache; they do not explain the historical specialized trap prototype, which uses different code.

The 36-game pilot gave 10/12 to each of Y1, R0, and R1. It has only one seed cluster. In a subsequent four-seed, 192-game full-CLI batch, Y1 won 43/48, R0 42/48, and R1/R4 each 41/48. R4 validated 382 cached steps in 48 games, compared with R1's 277. State mismatches fell from 166 to 66, but terminal wins did not improve.

Two inspected losses motivated narrower experiments: an early whole-turn replacement selected hero power instead of developing Knife Juggler; a cached attack overrode a freshly selected Explosive Trap. R5 preserves the early curve in trap-only contexts. R6 permits a divergent cached action only when the new plan ends the turn and the cached action plays a legal minion. Their unfinished screen was stopped when the authentic baseline arrived; incomplete arms are not reported as completed comparisons.

The preliminary 36-source-state continuation batch produced 1,084 terminal trajectories and rejected 20 forced-Coil hypotheses because its initial-hand conditioning could not handle an empty hand. This does not imply that Coil could not be drawn next turn. A small train-only route rule selected face pressure on Knife/Wolf training states (17/24 versus 15/24) but lost on held-out source states (8/24 versus 11/24). It was rejected. These preliminary continuation batches also preceded recovery of the historical unused-hero-attack reconstruction fix; the later corrected batch supersedes them for policy selection. A partially completed repeat is retained as interrupted diagnostic data, not independent evidence.

## Actual parent and continuation coverage

On 96 archived engine-trap-v2 Astra games, 59 had an active Explosive Trap, 19 had an active trap plus an enemy deathrattle, and only two actually targeted a deathrattle while the trap was active. Neither satisfied the historical continuation gate. One targeted Loot Hoarder with a one-action plan; the other broke Harvest Golem but had a later attack, which the old prototype rejected. No affordable Secretkeeper was omitted at end turn in these 96 games.

Across 1,392 older Y1 development games, there were 8,829 end-turn decisions, 12 with an affordable minion and a free slot, and seven with an affordable Secretkeeper. None of the seven also had the active-trap/deathrattle pattern. These are opportunity counts, not proof that playing the minion would improve the result.

E2 (parent engine-trap-v2) completes a verified minion play only if fresh replanning otherwise ends the turn; it follows fresh decisions in other conflicts. E3 (same parent) continues any verified deterministic plan. Both preserve lethal checks and submit only one currently legal action. They reproduce Kill Command on Harvest Golem, Steady Shot, Secretkeeper, end turn in the original translated public replay. E4 (parent historical trap-commit-v3, rebuilt from engine-trap-v2) broadens the narrow trap continuation to deterministic attack tails and checks synthetic token IDs against the observed board before reuse. The archived Golem tail becomes executable, but its first difference only changes attack/power order; that is not a demonstrated win-rate gain.

## Reliability observed during development

The R4 cold/concurrent/fault suite completed 41 calls with zero invalid outputs and zero calls above two seconds. Ordinary P99/max was 0.700 s; the complete injected-fault suite maximum was 1.824 s. Two injected failures correctly used fallback; ordinary calls had none. The final candidate receives its own independent runtime suite.

Five inherited engine mechanism tests passed: Dire Wolf aura removal, friendly Mortal Coil activating Amani, King Krush's nine-mana attack through a cleared Taunt, secret order/Bow/Misdirection, and Juggler plus Hounds. Four Explosive Trap differential cases and the generic-cache regression also passed. Actual CLI deck submissions were checked against the exact ordered Y1 list for six restored/new versions.

Further completed batches, source-group fitting, final freeze, independent results, and recommendation are recorded in REPORT.md and the machine-readable artifacts.

## Actual-parent development screen (completed)

Eight new complete seed groups, both seats and all six core opponents, produced 384 full-CLI games. Y1 won 93/96, engine-trap-v2 91/96, E2 91/96, and E3 87/96. Relative to engine-trap-v2, E3 lost four paired games and gained none. Its validated continuation changed actions in 72/96 games; E2 changed only 1/96 and preserved all parent outcomes. E3 is rejected. These are development results, not the final estimate.

The recovered Golem replay was separately tested on 24 new paired future hypotheses for each frozen proxy policy (192 terminal trajectories across four route objectives). Replanning versus verified continuation was 12/24 versus 15/24 for Zoo (six flips, three regressions) and 16/24 versus 19/24 for Tempo (three flips, no regressions). Resource preservation gave 16/24 and 16/24 respectively. These two proxy variants share one public source game; they are not two independent source groups. Exact stored-action replay reproduced the positive sample-zero Zoo pair, including every public state and final winner.

## Corrected grouped continuation fitting (completed)

The corrected world builder and authentic engine-trap-v2 parent were used for 63 source cases (36 older Y1 cases and 27 recovered parent/Y1 cases). Of 2,020 scheduled conditional trajectories, 1,960 terminated and 60 forced-Coil hypotheses were rejected by the initial-hand-only sampler: all three affected source states had empty opponent hands. Natural samples alone fit constants or one public-feature threshold with a complexity penalty. The Keeper route won 29/44 versus 27/44 on 11 training source groups, but 36/40 versus 37/40 on ten held-out groups, so it was rejected. Knife/Wolf (11 training, eight validation groups) and Amani (12 training, 11 validation groups) selected the unchanged replanning policy. Forced-Coil outcomes were never used for selection. The corrected stress rerun permits Coil as the next draw from an empty hand, excludes already-enraged source Amani, and avoids forcing a self-killing Coil after a defensive trade; the earlier stress versions are retained separately.

## Final selection, freeze, and post-freeze diagnostics

The six-seed targeted screen completed 288 games: Y1 47/72, engine-trap-v2 52/72, E2 52/72, and E4 52/72. All engine-trap/E2/E4 paired outcomes matched. E2 changed zero actual actions in this batch; E4 had one validated continuation game but also zero action changes. E2 was frozen as the research challenger, with its exact source fingerprint recorded before opening final core seeds. This is selection for measurement, not release promotion.

The final experiment runs every atomic decision through a fresh supervised CLI. During that immutable run, an additional known Amani replay was used only to diagnose missing route coverage. Explicit reactive routes exercise actual Highmane development, one cheap Hound trade, Bow removal, and Companion followed by replanning after its random summon. On the first twelve futures per proxy, cheap trading preserves natural wins and protects against forced Coil. Because none of those twelve natural draws contained Coil, natural sampling was expanded to 48 futures per proxy. This diagnostic is excluded from policy selection; final candidate bytes remain unchanged.

The Git snapshot preserves all twelve candidate fingerprints. `git diff --check` reports one inherited whitespace-only line in each copied `scripts/improvements.py`; those bytes were deliberately preserved to keep tested snapshots and original fingerprints identical. Newly authored source files pass compilation. Read-only status access was corrected to avoid taking the active trainer's writer lock; replay paths now support extracting the evidence archive at a different repository location. These harness/documentation changes do not modify any frozen policy.

The final audit also corrected a measurement label: the generic in-game action checker deliberately excludes `submit_deck`, so its earlier `valid: false` field was not a course deck-validation result. Six complete CLI deck envelopes were rerun, their sequence and ordered cards checked, and their returned decks accepted by `hs_arena.deck.deck_from_ids`. All six passed. The prepared fixed-deck path intentionally logs `fallback: true` without launching a worker; these startup flags are reported separately from runtime failure fallbacks. No policy code changed. Two explicit Juggler-on-board/Hounds-in-hand states were additionally run through all three final CLIs: all six chose legal Hounds plays, zero fallbacks, maximum 0.215 seconds.
