# Sources and testable adaptations

This round continues the pinned audits in `../secret_hunter_next/SOURCES.md` and
`../secret_hunter_program/reference-fetch.json`. No external policy code is copied.

* [Silverfish, pinned PenalityManager.cs](https://github.com/noHero123/silverfish/blob/cf6d1657e9dc99b9bcac9cc6e3c26f6ed8d0f2c7/ai/PenalityManager.cs), random-order penalties around lines 1030–1190: protect a Juggler until useful summons, resolve random information before committing follow-up actions. Adaptation: explicitly compare public chance outcomes and replan after each actual action, with independent effect/search/value modules. Do not transplant penalties, assume a full search, or copy unlicensed code.
* [DimfrostHS, Secret Hunter guide](https://www.reddit.com/r/CompetitiveHS/comments/55dois/top_200_legend_with_obsolete_secret_hunter_64_wr/), card choices: synergy, contextual Explosive Trap, experiments with Hounds/Dire Wolf/Snake Trap. Adaptation: compare summoning and trading order within our fixed D1 list. The 2016 deck, card balance and claimed ladder win rate are not this course environment. The guide was reopened this round; it is a hypothesis source, not empirical evidence for our policy.
* [Garcia-Sanchez et al., Sections 3.1–3.2](https://arxiv.org/html/2410.19681v1): retain the prior protocol of same-block parent/child evaluation and fresh confirmation. No new weight-only ES or opponent coevolution.
* [Hearthstone AI Coach](https://github.com/barnabys-drew/hearthstone-ai-coach/tree/f720601bc3bb75730658f76825f1088ace671992), previously audited LessonTrigger/LessonStats: preserve failed cases and whole-game train/validation splits. No runtime RAG or model.

The installed course engine is authoritative: `neutral_rare.NEW1_019`,
`hunter.EX1_538`, `actions.Summon/Play/Hit/Deaths`, `game.action_end`, and
`dsl.selector.RANDOM_ENEMY_CHARACTER` were inspected. Tests must verify deferred
deaths, shield/armor, enrage/aura refresh, capacity and unknown deathrattles.
Random evaluations never become guaranteed-lethal proofs. The production seed is
derived only from public projected state/action, never the match RNG/seed.
