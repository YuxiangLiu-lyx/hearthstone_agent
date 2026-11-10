# Architecture and initial audit

Source of truth: the supplied hs-arena 0.2.2 wheel, source, handout and protocol. The official files remain unchanged.
Python 3.11 in `.venv` is installed exclusively from the supplied wheels.

## Boundary and protocol

The host owns Fireplace, seeded randomness, hidden cards, validation and the public replay. A policy receives
only a JSON seat observation. Own hand and remaining deck counts are visible; opposing hand, deck order,
secret identities and draw identities are hidden. Development policies receive no Engine object or seed.
Nine classic classes; 367 allowed Basic/Classic cards; 30 cards, class/neutral, at most two copies, one legendary.
Use the supplied catalog rather than contemporary Hearthstone rules.

MCP begins with deck_submission (you/opponent are null), then mulligan, main, choice and game_over.
`legal_actions` are templates, not always directly submittable: expand targets, Choose One options and
positions. Standalone choice has a minimum/maximum selection count. Entity ids are integers; deck ids are strings.
Fresh seq per decision, including rejection. Act usually returns the next decision. No early exit.

## Baseline audit

Official Greedy scores attack+health+keyword weights. It prioritizes favorable single trades, cheap kills,
large bodies, basic removal and spare hero powers. Its lethal check sums currently available attacks and
greedily packs direct damage by damage/mana. It cannot plan taunt removal, new charge units, buff ordering,
spell discount sequences or coordinated trades. Its harmful-text heuristic can choose bad battlecry targets;
unknown spells and many deathrattles/synergies have crude estimates. Its generic evaluation is not evidence
that each coefficient is well tuned. Official baseline remains unchanged in experiments.

## Implementation and experiment separation

`submission/hearthstone-agent`: executable stateless policy, legal guard, bounded planner, recipe, Skill relay.
`development`: population, benchmarks, tests, optimizers, immutable snapshots, real reports and replays.
Benchmarks use original `hs_arena.runner.play_game`, instrumented Player adapters and process workers.
Only view dictionaries enter decision policies. Model integration uses the official `skill:` launcher.
Cheap `client:` tests validate MCP without claiming model validation.

## Risks and mitigations

- Engine mechanics differ from live card history: inspect local card scripts and verify simulated transitions.
- Hidden information cannot be reconstructed as fact: no host state or replay metadata passed to policy.
- Local simulators omit triggers: conservative whitelist and unsupported-state fallback; never claim universal lethal completeness.
- Statistical noise/overfit: paired seeds/seat swaps, fixed opponents, reserved holdout, preset promotion gates.
- Runner builtin timing is cooperative: measure policy time and report benchmark limitations separately from process/MCP tests.
- Model launcher/account incompatibility: test genuine skill mode; record failures without substituting model names.
- 180 seconds/three illegal actions/early exit all forfeit: fallback, bounded search and explicit relay loop.
- P1 is not synonymous with first player: use result.first_player in metrics.

The local handout lists November 15, 2026 at 23:59:59 America/New_York as the deadline. No Slack submission is authorized.
