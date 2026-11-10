# Face Hunter Agent

This is a separate Hunter skill for official hs-arena 0.2.2 / basic-classic-1.
The final configuration is V3 with the original 30-card deck. Paladin and Zoo retain
their original code, configuration, champion pointers and ZIP files; 45 protected
SHA-256 values are checked against `development/checkpoints/pre-face-hunter-sha256.json`.
The repository origin is `https://github.com/YuxiangLiu-lyx/hearthstone_agent`; tag
`pre-face-hunter` preserves the initial project. No course submission was made.

## Architecture and protocol

The Luna skill is a relay: read one observation, run `python scripts/decide.py`, send
the returned seq/action unchanged through MCP, then observe and replan. Setup explicitly
submits the validated deck through MCP. Mulligan, choice, main and terminal phases are
handled. There is no cross-game state, network call, extra model, or hidden opponent access.

| Module | Responsibility |
|---|---|
| `decide.py` | Current-state input, exact seq, legal validation, subprocess watchdog and recovery |
| `action_validator.py` | Instantiate and check the host's legal-action templates |
| `baseline.py` | Low curve mulligan, board development, face pressure, blocking Taunts and spare-mana power |
| `tactical_model.py` | Conservative public-state projection with supported effects only |
| `lethal_planner.py` | Deduplicated bounded beam search; separate uniform Companion branches |
| `next_turn.py` | Mana-feasible burn, Beast setup, board survival, weapon and Wolf/Hounds reach |
| `strategy.py` | Guaranteed lethal, stable pressure and high-risk comeback arbitration |
| `state_features.py` | Official card catalog, own deck/public history and shared public features |

Lethal search includes mana/Coin, Taunts, armor, shields, charge, attack availability,
Wolf/Leokk auras, seven-slot capacity, Beast-dependent Kill Command and Hyena death
triggers. Synthetic token IDs exist only in explanatory plans; execution always uses
one root legal action. New weapon attacks require observed public turn history.

Production limits: 1,600 nodes, 0.2 seconds per guaranteed search, bounded depth/beam,
and a separate two-second worker watchdog. The fixed V3 holdout averaged 4.37 ms per
in-process decision, with a maximum of 256 ms. This excludes interpreter startup and
model relay latency. Companion evaluation has its own 0.05-second bound. The watchdog
regression deliberately stalls the policy and verifies a legal fallback before the
official 180-second timeout.

Unknown opposing secrets, unmodeled triggers and unobserved draws cause search
abstention. Beam pruning and deadlines can miss real lethals. No-search-result does
not prove that a lethal is absent. Windfury availability is conservative when ambiguous.

Next-turn survival, opponent responses and stable win confidence are uncalibrated
heuristics, not inferred hidden cards or measured probabilities. Each Companion result
has known probability 1/3; successful searched continuations provide conservative
coverage. Risk mode requires that coverage to exceed the stable heuristic plus 0.08,
with high estimated survival risk or very low stable confidence. Guaranteed lethal
takes priority. Four weights are centralized and configurable: 22 next-turn value,
60 survival reduction, 3 combo enablement, and 0.08 random-comeback margin.

## Deck and isolated deck experiment

The supplied Beast Face Hunter recipe remains unchanged: two copies each of Timber
Wolf, Stonetusk Boar, Scavenging Hyena, Bloodfen Raptor, River Crocolisk, Jungle Panther,
Savannah Highmane, Arcane Shot, Explosive Trap, Animal Companion, Kill Command,
Unleash the Hounds, Eaglehorn Bow, Leper Gnome and Wolfrider. Official card IDs, costs,
effects and legality are recorded in [deck-audit.json](deck-audit.json).

Only after strategy stabilization, a deck-only challenger replaced two Highmanes with
two Bluegill Warriors. Eight of 69 losses in the expanded V3 training arm had Highmane
in the final observed hand, motivating a faster-charge hypothesis. Across 400 paired
games the challenger won 239 versus 236: +0.75 percentage points, seed-cluster 95%
interval [-3.75, +5.25]. This is insufficient evidence to change the deck. Both recipes
and results are retained; see [deck comparison](deck-comparison/comparison.md).

## Experiments and selection

All outcomes below come from the official engine. Model-free batches use our Python
policy, not Luna. Each seed is played in both seat assignments; seeded first-player
selection is recorded separately. The pool is equally weighted greedy Mage, frozen
Paladin, frozen Zoo and frozen Priest. Results do not establish performance against
Mystery Bot, Astra or arbitrary opponents.

The first four 40-game strategy screens exposed a missing `poisonous` field on hero
attackers. The exception caused legal fallback, affecting 29/26/24/22 decisions in
V0/V1/V2/V3 respectively. Those 160 games are retained and rejected for promotion.
A regression test and a default false value repaired the issue before comparisons
were repeated. Guaranteed search also precedes baseline scoring.

Five substantive iteration records were retained: current-turn search, next-turn
planning, risk arbitration, reliability repair, and the isolated deck challenger.
Repeated seeds for paired ablations are intentional; expanding sample size did not
change parameters. No further tuning used the independent validation outcomes.

| Arm | Development wins | Independent validation wins | Validation rate |
|---|---:|---:|---:|
| V0, basic | 115/200 | 113/200 | 56.5% |
| V1, guaranteed search | 224/400 | 116/200 | 58.0% |
| V2, next-turn value | 115/200 | 115/200 | 57.5% |
| V3, risk aware | 236/400 | 119/200 | 59.5% |

V0/V2 use development seeds 42100–42124; V1/V3 were expanded to 42149. Comparisons
always intersect identical seed/opponent/seat keys, rather than subtract unequal-pool
rates. V3 was provisionally selected before opening holdout seeds 142100–142124.
Its 400-game development advantage over V1 was 3.0 points, with an exploratory paired
interval [0.0, +6.0]. This is modest evidence, not conclusive superiority.

Independent validation marginal effects: V1−V0 +1.5 points; V2−V1 −0.5 points;
V3−V2 +2.0 points. V3−V0 is +3.0 points with seed-cluster interval [-2.0, +7.5].
The V3 win-rate Wilson 95% interval is [52.6%, 66.1%]. Intervals are exploratory,
not adjusted for sequential selection/multiple comparisons. Next-turn planning alone
has no demonstrated average benefit. Risk handling partially recovers its losses;
stronger general-win-rate claims are not justified.

See [development comparison](development-comparison/comparison.md) and
[holdout comparison](holdout-comparison/comparison.md) for exact denominators, paired
discordances, turns and damage. All 2,400 repaired Python games have zero policy
exceptions, illegal actions, timeouts, early exits or engine voids. The rejected 160
pre-fix games are excluded from this reliability statement.

## Tactical evidence and failure review

All 31 automated tests pass, including all 12 requested lethal cases, actual-engine
one-step differential checks, public-history Bow attack availability, Hyena growth,
next-turn power/Kill Command, a genuine one-third comeback, survival trades and the
hard watchdog. The constructed Highmane case proves that baseline development can
consume mana needed for a real lethal. See [test output](planning-tests.txt).

An offline audit examines observed main decisions in turns that did not actually win,
with at most one finding per game/turn. A larger bounded search screens candidates;
the completed game is reconstructed in the official engine and the alternative is
executed using only public observations. V0 has **17 engine-confirmed missed-lethal
turns in 200 development games**. V1 has **one in the same 200 games**. V3 has zero
detected in 400 development games and zero detected in 200 holdout games. These are
lower bounds, not exhaustive guarantees.
An eventual win can still contain an earlier missed-lethal turn.

The remaining V1 miss is Zoo seed 42121, seat 2, turn 9, seq 15: production search
hit its 0.2-second deadline; the larger audit finds a Hounds/attack/power continuation.
This is a concrete remaining search-budget limitation. See
[V0 engine confirmations](v0-confirmed-misses.json),
[V1 engine confirmation](v1-confirmed-misses.json), and the corresponding full-state
`*-turn-lethal-audit.json` files. End-turn-only checks found no positives and would
have missed these earlier resource-commitment errors.

On V3 holdout, opponent results were greedy 43/50, Paladin 26/50, Priest 30/50 and
Zoo 20/50. Among 81 losses, 73 final observations had visible opposing board attack
at least equal to own effective health, 66 had at most one card in hand, and 18 had
an opposing Taunt. Signals overlap and are not proven causes. Every loss has a
concrete state/action in its experiment's `failure-states.json`.

The next worthwhile experiment is selective search widening and better threat/board
survival estimates against Zoo, with a fresh validation block. Do not claim that more
two-turn heuristics or a cheaper deck automatically improve results. Other requested
failure classes (overstated random lethal, unnecessary trade, burn wasted before a
next-turn kill) are not reliably labeled automatically; targeted tests and concrete
logs are available, but no invented case counts are reported.

## Integration, packaging and reproduction

Real MCP smoke results: initial V0 3/3 against random and 1/3 against greedy; corrected
V0 2/3 and corrected V1 2/3 against greedy. Final V3 also completed 3 real MCP games
at seeds 43010–43012, winning two. All these clients invoke the watchdog CLI, including
deck setup. Three real Luna games at seeds 43000–43002 finished 2–1 with zero illegal
actions, timeouts, early exits or fallbacks. All 77 submitted actions, including deck
setup, match actual printed CLI outputs. See `experiments/face-hunter-skill-smoke`
and [relay audit](luna-relay-audit.json) for exact action-relay verification.
These integration samples are not competitive win-rate estimates.

Final artifact: `dist/face-hunter-agent.zip`, 17,538 bytes compressed, 44,533 bytes
uncompressed, 12 files. Scripts are Python only. The extracted ZIP passes official
static validation and a 30-card setup-response check. The archive has no bytecode,
development fixtures, network dependencies or replay files. SHA-256 and per-file
hashes are in `dist/face-hunter-agent.manifest.json`.

The official course package is installed locally but excluded from Git. A fresh
checkout requires the course-provided hs-arena 0.2.2 distribution as described in the
root README. Raw games are retained locally under ignored `experiments/*/games/`;
configs, metrics, failure snapshots and analysis are tracked. To reproduce:

```sh
.venv/bin/hs-arena validate face_hunter --no-game
.venv/bin/python -m unittest tests.test_face_hunter -v
.venv/bin/python -m development.face_hunter.run --config development/face_hunter/configs/v3.json --out experiments/reproduce-hunter --start 42200 --seeds 25
.venv/bin/hs-arena play --p1 client:development/clients/face-hunter-final --p2 greedy --games 3 --seed 43100 --out experiments/reproduce-mcp/games
.venv/bin/hs-arena play --p1 skill:face_hunter --p2 greedy --games 3 --seed 43110 --out experiments/reproduce-luna/games
.venv/bin/python -m development.face_hunter.build
```

The local Homebrew Codex wrapper is broken; the existing VS Code Codex executable was
used by setting PATH for the launcher process only (see root README). No global
installation/authentication was changed. Open [review.html](review.html) directly in a
browser for a recorded win and loss; it is an offline observation viewer, not a video.
