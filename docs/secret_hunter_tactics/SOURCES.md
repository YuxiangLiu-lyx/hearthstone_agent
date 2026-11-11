# Source audit and adaptation

The complete pinned-source/license audit is retained in
[the program source table](../secret_hunter_program/SOURCES.md) and its
`reference-fetch.json`. The previous ES round's actual algorithm audit is in
[its source note](../secret_hunter_es/SOURCES.md). This round reuses those inspected
sources rather than claiming to have executed their agents. No external simulator
or automation-client code was copied into the policy.

| Source | Material inspected / reused | Tactical adaptation and limits |
|---|---|---|
| [noHero123 Silverfish](https://github.com/noHero123/silverfish/tree/cf6d1657e9dc99b9bcac9cc6e3c26f6ed8d0f2c7), `cf6d1657…` | Re-read `BehaviorFace.getPlayfieldValue/getEnemyMinionValue`, `PenalityManager.getAttackWithMininonPenality/getAttackWithHeroPenality`, Hounds special penalty; reused prior `MiniSimulator.doallmoves` and enemy-response audit | Separate lethal, end-turn scoring and bounded replies. Conditional low-health pressure, protection, Bow and Hounds opportunity cost. Our public attack-only response is much narrower than a complete simulator. No rarity score or copied constants. |
| [HB](https://github.com/lijhnihaoa/HB/tree/177af7409047237733b0fd243fd48e028b9c1017), `177af740…` | Prior inspected generic search, RulesEngine, Attack and Wild Reno Hunter behavior | Modular rules/search/evaluation. Reject automatic Explosive clear merely because a fragile enemy exists. Wild Reno deck and current game card stats are not this deck. |
| [García-Sánchez et al.](https://arxiv.org/html/2410.19681v1), 2024 v1; [SabberStone optimizer](https://github.com/fergunet/SabberStone/blob/1360ba1532f2322a82767fa71f6415cb7dd740fd/core-extensions/SabberStoneCoreAi/coevolutionary.py), `1360ba15…` | Prior full sections 3.1/3.2, 21 parameters, mutation/retention and evaluation audit; paper refreshed this round | Empirically select meaningful parameters, re-evaluate parents on each fresh shared seed block, retain stronger candidates, then validate independently. This round uses one compact (1+5) interpretable mutation generation, not the paper's coevolution or full ES schedule. The previous larger ES failed confirmation; no paper-derived gain is assumed. |
| [Hearthstone AI Coach](https://github.com/barnabys-drew/hearthstone-ai-coach/tree/f720601bc3bb75730658f76825f1088ace671992), `f720601b…` | Prior `LessonTrigger/LessonStats/Lesson/match_lessons` and progressive-RAG audit | Offline loss triggers, alternatives, provenance and evidence. No runtime model, embedding lookup or retrieval service. |
| [ur2ezchaos, Naxx Midrange Hunter, 2014](https://www.hearthpwn.com/decks/84233-naxx-midrange-hunter) | Strategy text opened earlier in this round; later refresh returned 403 | Contextual Houndmaster, Bow/Explosive versus wide pressure, Dire Wolf trades and Hyena/Hounds. Its deck contains different cards; adopt only ideas applicable to our fixed list, verified against the course engine. Other modern guide snippets were not treated as fully read sources. |
| Course `hs_arena 0.2.2` | Installed `_vendor/fireplace/cards/classic/hunter.py`, `actions.Attack/Bounce/Reveal`, `game.end_turn_cleanup`; official-engine fixtures and replay differentials | Authority for actual cards, pending-death Secret ordering, Bow reveals, Snake Beasts and thaw behavior. Missing public attack/exhaustion data causes conservative response rejection instead of invented certainty. |

Previous historical-guide audits remain in the program source table. All borrowed
ideas are hypotheses; paired matches, not the authority of a script or guide, decide
promotion. Unseen classmate/Mystery/Astra results remain unknown. The exact frozen
opponent pool, deck, runtime and base commit remain recorded in the round manifests.
