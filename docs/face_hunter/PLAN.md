# Face Hunter architecture and experiment plan

Runtime: official hs-arena 0.2.2; pool basic-classic-1 (367 cards). The existing
Paladin and Zoo agents are preserved at Git tag `pre-face-hunter` and by 45 SHA-256 hashes.

## Milestones and acceptance criteria

1. M0: inspect official docs, MCP examples, card catalog and Hunter effect scripts.
   Validate the exact user-specified deck; record `deck-audit.json`.
2. M1 / V0: deterministic baseline, template validation, watchdog and recovery;
   run at least three full official MCP games with no illegal actions, timeout or exit.
3. M2 / V1: bounded current-turn lethal search. Verify all twelve requested scenarios
   against the actual engine, including auras, board space, armor and randomness.
4. M3 / V2 and V3: explicit next-turn and survival estimates; label heuristic risk
   separately from known Animal Companion probabilities; test each mode independently.
5. M4: paired official-engine comparisons with the same deck and seeds. Preserve
   every configuration. Up to five evidence-based challenger rounds; accept only
   with a reliability check and a meaningful measured benefit.
6. M5: freeze a separate Hunter Champion, static validation, three actual Luna skill
   games, verify replayed script actions, and package a Python-only skill below 10 MB.

## Data boundaries and reproducibility

The policy sees only `game/state.json`, its own deck recipe and the public card catalog.
Development fixtures may set up engine states; those helpers are not shipped. Every
match uses the official engine. A local analytical tactical model must abstain on
unsupported effects and cannot replace the official engine for benchmark outcomes.

V0 has no multi-action search; V1 adds guaranteed lethal; V2 adds two-turn value;
V3 adds survival-aware selection and conditional random comeback. All versions use the
same fixed deck initially. Deck changes, if any, require a separate later experiment.

Initial MCP smoke seeds: 42000-42005. Initial development paired seeds: 42100-42124;
V1/V3 were subsequently expanded through 42149 to resolve uncertainty. The deck-only
challenger used 42100-42149. The independent validation block was 142100-142124 and
did not select parameters. Final MCP seeds were 43010-43012; Luna seeds 43000-43002.
Seat swapping is separate from the seeded first-player choice; report actual first/second.

Each experiment saves config.json, metrics.json, summary.md and failures.md, with raw
official game files under ignored games/. Metrics include real win counts, a Wilson
interval, turns, outgoing hero-damage events, reliability, decision latency and supported
lethal audits. Zero detected misses is not a claim of exhaustive tactical coverage.

Luna integration is reported separately from Python-only and MCP-client tests. No local
result is evidence against the unreleased Mystery Bot or Astra. Nothing is submitted
to the course Slack agent by this workflow.
