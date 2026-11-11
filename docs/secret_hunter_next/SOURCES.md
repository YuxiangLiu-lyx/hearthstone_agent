# Sources, adaptation, and portability

This continuation read the existing pinned audits in
[`../secret_hunter_program/SOURCES.md`](../secret_hunter_program/SOURCES.md) and
[`../secret_hunter_tactics/SOURCES.md`](../secret_hunter_tactics/SOURCES.md).
No external agent implementation was executed or copied. The following ideas are
independent implementations on the course public observation, not reproductions
of a reference agent's reported performance.

| Source and inspected location from the existing audit | Adaptation in this round | Evidence and limitation |
|---|---|---|
| [Silverfish](https://github.com/noHero123/silverfish/tree/cf6d1657e9dc99b9bcac9cc6e3c26f6ed8d0f2c7), `Ai` lethal dispatch, `MiniSimulator.doallmoves`, `cuttingposibilities`, endpoint scoring | Extend the independent proof entrypoint to already implemented Houndmaster/Secretkeeper effects; preserve the existing beam, endpoint evaluation and visible replies; add excluded/deduplicated/beam-pruned/stop-reason telemetry | M1 mechanism and engine differentials. A finite beam is incomplete. No source code or constants copied; prior audit found no explicit license. |
| [HB](https://github.com/lijhnihaoa/HB/tree/177af7409047237733b0fd243fd48e028b9c1017), `MiniSimulator`, `RulesEngine`, `Playfield.Attack`, GPL-3.0 | Keep effect semantics in `tactical_model`, search in `turn_search`/`lethal_planner`, evaluation in `race_plan`; reject unsupported random triggers rather than fabricate deterministic damage | Amani/Imp fixtures found real course ordering differences. No Wild-card semantics transplanted. |
| [Garcia-Sanchez et al.](https://arxiv.org/html/2410.19681v1), Sections 3.1–3.2, Algorithm 2; [SabberStone optimizer](https://github.com/fergunet/SabberStone/blob/1360ba1532f2322a82767fa71f6415cb7dd740fd/core-extensions/SabberStoneCoreAi/coevolutionary.py) | Re-evaluate parent and structural children on each shared new development block; retain a simpler candidate and freeze before final tests | Mechanism, response, local coverage and preference-learning directions tested. No self-play, opponent coevolution, transferred weights, or repeated weight-only ES. |
| [Hearthstone AI Coach](https://github.com/barnabys-drew/hearthstone-ai-coach/tree/f720601bc3bb75730658f76825f1088ace671992), `LessonTrigger`, `LessonStats`, `Lesson`, `match_lessons`, MIT | Save source game/sequence, public observation, root alternatives, continuation policy, random samples, errors and validation status in `counterfactual-v2.jsonl` | Six terminal samples per alternative, split by whole source game. Conditional on existing hidden hands; no claim to reconstruct them from public information. No runtime model, embeddings, retrieval or services. |

The official course engine is authoritative. Installed
`hs_arena/_vendor/fireplace/cards/classic/neutral_common.py:EX1_393`,
`neutral_rare.py:EX1_597`, `actions.py:Attack/Hit`, and
`game.py:refresh_auras` were read. The first 48-fixture differential had four
mismatches, retained in `mechanisms-v1.json`. Two were fixture-induced stale enrage
auras, one was pending-death board capacity, and one was the timing of Secret
trigger attack refresh. The corrected differential matched 48/48. Subsequent
recorded development branches matched 644/644 for M1 and 657/657 for M2.
The latter counts are short nonterminal checks, not matches won.

The [current HW2 assignment](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md)
was fetched again for this round (archived verbatim as `current-assignment.md`, SHA
in the ZIP manifest). It permits Python decisions and exact model relay, requires
one skill folder in one ZIP, Python-only execution, existing course dependencies,
and a 10 MB limit, and forbids bundled model weights. Therefore the fitted L1
linear evaluator is an offline research artifact only. The final M1 submission
contains deterministic policy code/configuration and no learned model.
The HTTP fetch used curl after the web tool could not open the page. No official
upload or new model-host call was made.
