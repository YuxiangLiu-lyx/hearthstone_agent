# Sources and adaptation

The prior source audit remains at ../secret_hunter_program/SOURCES.md, including
actual files, functions, commits, licenses and accepted/rejected ideas. No external
simulator source was copied into this round.

- [García-Sánchez et al., Optimizing Hearthstone Agents using an Evolutionary Algorithm](https://arxiv.org/html/2410.19681v1), v1, 2024-10-25. Re-read sections 3.1/3.2, Algorithm 2, equations 9–13 and experimental settings on 2026-11-11. Adopted 21 real-valued policy coefficients, individual mutation scales, parent re-evaluation and (mu+lambda) retention. Our 21 features differ: no rarity, no absent mechanics, separate own/enemy attack/health, conditional Secrets, exposure and beast resources. Our population is 2 parents plus 4 offspring for 3 generations, under the user's match budget. The paper used a much larger 10+10 population and 100 generations. Fixed historical opponents replace coevolution; this is not a reproduction of the paper's tournament result. The HTML's equation 9 prints addition of an exponential to sigma; our explicitly documented variant multiplies sigma by a log-normal factor, with [.01,.35] normalized bounds.
- SabberStone ParametricGreedyAgent.cs / coevolutionary.py, commit `1360ba1532f2322a82767fa71f6415cb7dd740fd`: previously read scoreTask, calculateScoreHero/minions/Secrets, scoreMinion, setAgentWeights, generate_weights, evaluate_hearthstone and run_one. Ideas reused through fresh Python implementation; source not copied. Repeated-parent evaluation is important because fitness seeds change every generation.
- Course `hs_arena 0.2.2` remains the authoritative mechanism implementation. Official-engine microfixtures and historical-replay differential checks found that Snake Trap tokens are Beasts and that the prior feature catalog omitted them. New Secret deployment implements the course's own-only Secretkeeper trigger, rather than the historical printed card text. Random Knife Juggler summons, Companion, multi-target Deadly Shot, hidden enemy Secrets and unobserved draws remain excluded from exact proof.
- Current course assignment retrieval through web returned an error; a direct HTTPS fetch then succeeded. Its SHA-256 `994756797ee569ea368cd7938a0d17cb73af86475a7846b8d5dab6cd0937a27a` exactly matches the prior fetched assignment. The program-decision and minimal-relay contract remains unchanged. See course-refresh.json and the prior local handout/protocol audit.

No inference from an opponent name, seed, deck order or private cards enters a
runtime decision. The engine clone in offline counterfactual tests has hidden
state only to replay a historical game; the policy receives the recorded public
observation or the engine's public view. Shared seeds do not guarantee identical
random draws after different action paths.
