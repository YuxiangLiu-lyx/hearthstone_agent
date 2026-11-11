# Control Priest: theft, durable boards and favorable exchanges

This independent Priest skill starts from the existing local opposing Control Priest
at `development/candidates/adversaries/priest-control`. The original opponent is kept
unchanged. Paladin, both Zoo releases and Face Hunter also retain their code and ZIPs.
The new skill is `control_priest`; the separate release is
`dist/hearthstone-control-priest.zip`.

The final release is **V2**, which also blocks already-provable self-lethal attacks
from visible Leper Gnome/Abomination deathrattles or fatigue draws. On its fresh
300-game validation it wins **231/300 (77.0%, Wilson 95% 71.9%–81.4%)**, versus
151/300 for the original opponent, a paired +26.7 points [18.7, 35.0]. All previously
completed V1 results below remain recorded separately.

## Deck and actual runtime rules

See [the full 30-card deck](DECK.md) and [official catalog audit](card-audit.json).
The final list has 19 minions and 11 spells. It combines:

- Permanent control: two Cabal Shadow Priests and one Mind Control.
- Temporary control/copying: Shadow Madness, Faceless Manipulator and two Thoughtsteals.
- Setup and buffs: two Scarlet Subjugators, two Kul Tiran Chaplains, two Defenders of
  Argus, two Temple Enforcers and one Power Word: Shield.
- Removal: two Shadow Word: Pain, two Shadow Word: Death, two Holy Novas and Natalie Seline.
- Durable bodies: Cairne Bloodhoof, Sunwalker, two Sen'jin Shieldmastas and two Harvest
  Golems; Acidic Swamp Ooze retains weapon interaction.

Cards can have overlapping roles in the description above. Legendary copies are
limited to one, and all cards/class/counts pass official validation.

The strategy follows this packaged engine rather than another Hearthstone patch.
Shield costs zero and does not draw; Nova costs four and does not damage the enemy
hero; Thoughtsteal costs two; Shadow Madness costs three. Power Infusion is printed
as +2/+6 but actually executes +2/+2. Both original-deck and copied-card handling use
the observed effect in the specialist. It is absent from the final deck. Northshire
Cleric, Auchenai Soulpriest and Divine Spirit are not in the permitted card pool.

## Decisions and preserved behavior

The copied opponent policy remains the basis for general legal decisions and unknown
copied cards. Direct lethal takes priority before Priest adjustments. Public-state
specializations then improve target selection and sequencing:

1. Scarlet can turn a four-Attack target into a legal Cabal target or make a four/five-
   Attack target vulnerable to Pain. Mana and all required board slots are checked.
2. Permanent theft values both removing the enemy threat and retaining its body.
   Cabal needs room for itself before the acquired minion arrives. Natalie values the
   target's current Health, matching the engine rather than assuming maximum Health.
3. A borrowed Shadow Madness minion is spent in useful same-turn exchanges. Public
   own-turn history tracks it; permanent health investment is discouraged. Its deathrattle
   triggers for its controller at death. Frozen/cannot-attack bodies are not assumed ready.
4. Health buffs and healing favor surviving trades. Nova includes its healing value;
   Ruin counts friendly casualties. Faceless favors a high-value body such as Cairne.
5. Thoughtsteal helps replenish a small hand without assuming which hidden cards will
   be copied. It does not deplete the opposing deck and is avoided on an empty deck.
   Known fatigue and visible lethal pressure increase hero-healing priority.

An inherited bounded exchange scorer searches at most three actions/1,600 nodes with
supported effects only. A small buff-lethal helper handles current legal face attacks
and up to three Shield/Inner Fire/Power Infusion spells; it abstains on secrets and
unsupported triggers. These are not exhaustive planners. The two-second watchdog,
phase handling and legal-template validation remain in the Python entrypoint. The
Luna skill relays exactly one action, then reads the next observation. No hidden files,
live engine state, RNG seed, external API or network is used by the submitted policy.

## Paired development and independent validation

The fixed pool contains official greedy Mage, frozen Paladin, frozen Zoo, frozen Face
Hunter V3 and the original opposing Priest. Each seed is played in both seats. First
player is separately seeded and reported. All outcomes use official hs-arena games.

Development seeds 51000–51023 produced these results:

| Version | Wins / games | Rate |
|---|---:|---:|
| Copied opposing deck and policy | 124/240 | 51.7% |
| Specialist policy, original deck | 133/240 | 55.4% |
| Specialist, core synergy deck | 178/240 | 74.2% |
| Specialist, final theft deck | 185/240 | 77.1% |
| Generic copied policy, final theft deck | 114/240 | 47.5% |

The final theft variant replaces one Ooze and one Shield from the synergy list with
Shadow Madness and Faceless. Its +2.9-point advantage over that list has an interval
crossing zero, so the particular two-card choice is not established as uniquely optimal.
The larger specialist/deck combination gain over the original is well supported in
this local pool. Generic policy with copied foreign weapons receives only a missing
hero `poisonous` flag compatibility repair; the original opponent itself is untouched.

V1 was frozen before using seeds 151000–151029. Three arms share exactly the same
300 seed/opponent/seat assignments in that original V1 validation:

| Version | Wins / games | Rate | Wilson 95% |
|---|---:|---:|---|
| Original opposing Priest | 157/300 | 52.3% | 46.7%–57.9% |
| Generic policy with new deck | 159/300 | 53.0% | 47.3%–58.6% |
| V1 specialist Control Priest | **231/300** | **77.0%** | **71.9%–81.4%** |

V1 minus original is +24.7 percentage points; paired seed-cluster 95% interval
[+15.3, +33.3]. V1 minus generic on the identical deck is +24.0 points, interval
[+18.0, +30.0]. These are exploratory intervals over a fixed local population, not
claims against Mystery Bot, Astra or all future opponents. Complete paired outputs:
[development](development-comparison/comparison.md), [policy ablation](policy-ablation/comparison.md),
[holdout](holdout-comparison/comparison.md).

During V1 loss review, `hunter-s151000-p2`, turn 12, seq 15 exposed an attack into a
Leper Gnome at two Health with healing available. The known deathrattle immediately
killed our hero. V2 adds a narrow pre-attack guard, with engine tests for Leper,
Abomination and Loot Hoarder fatigue. The old holdout is now diagnostic for this
refinement; it is not reused as fresh V2 evidence. No scoring weights or deck changed.
See [the concrete case](leper-self-lethal-case.json).

Development outcomes remain 185/240 in both versions. V2 was frozen and all three
arms rerun once on fresh seeds 151100–151129: original 151/300, V1 231/300, V2 231/300.
There are zero discordant V1/V2 game outcomes in this sample. The refinement fixes a
proved bad action but has **no measured incremental win-rate gain**. See the
[new independent comparison](safety-holdout-comparison/comparison.md).

| Fresh V2 holdout opponent | Final wins / games | Original Priest wins |
|---|---:|---:|
| Greedy Mage | 53/60 | 44/60 |
| Face Hunter V3 | 31/60 | 19/60 |
| Paladin champion | 52/60 | 33/60 |
| Original control Priest | 48/60 | 30/60 |
| Zoo V7 | 47/60 | 25/60 |

There are 3,240 model-free games in this iteration: 1,440 development/ablation and
1,800 validation. All completed without policy exceptions, illegal actions, timeouts,
early exits or engine voids. Final holdout in-process decisions average 0.116 ms,
maximum 1.67 ms; interpreter/model relay latency is excluded.

## Tests, observed combinations and weaknesses

[Twenty-five engine tests pass](tests-final.txt), including actual buff/steal semantics,
Scarlet→Cabal/Pain, board capacity, temporary control return and deathrattle ownership,
freeze, Faceless copying, Nova healing, Ruin friendly damage, fatigue, and a real
Shield→Inner Fire lethal. The shield/no-draw and Power Infusion discrepancy are direct
engine checks, not text assumptions.

The V1 holdout [decision audit](decision-audit.json) covers 12,896 main decisions. All 230
inherited immediate-lethal choices are preserved exactly. Adjacent public observations
confirm 218 permanent steals, 97 temporary steals and 10 Scarlet→Cabal combinations.
Concrete before/action/after examples are saved in the audit. This does not claim zero
missed lethals outside the supported subset. The [final V2 audit](final-decision-audit.json)
covers 12,726 main decisions, preserving all 231 inherited immediate-lethal choices;
it records 247 permanent steals, 83 temporary steals and 13 Scarlet→Cabal combinations.

Of 69 final V2 losses, 39 had visible opposing board damage at least as large as own
effective health in the final observation, 15 had at most one card in hand, and seven had
an opposing Taunt. Signals overlap and are observational, not proven causal labels.
Every loss has a key state/action in `experiments/priest-safety-v2-holdout/failure-states.json`.
Hunter is the weakest matchup (31/60), suggesting early stabilization as the next isolated
experiment. Unknown generated-card combinations and limited multi-action search remain
limitations. Do not tune on the consumed holdout seeds.

Open [review.html](review.html) for a recorded V1 win and loss against the original Priest.
This offline observation viewer includes real board/hand/action snapshots and no opposing
hidden hand. It is a development aid, excluded from the submission.

## Integration and release

Official static validation passes on both source and extracted ZIP. Extracted setup
returns a valid 30-card Priest submission. V1 MCP-client smoke at seeds 52010–52012
finishes 2–1 with zero illegal actions, timeouts, exits or CLI fallback. V1 real Luna
smoke at 52000–52002 finishes 3–0, with all 137 actions exactly relayed. V2 receives
separate MCP and Luna smoke at 52030–52032 and 52020–52022; final results are stored in
`experiments/priest-safety-mcp-smoke`, `experiments/priest-safety-luna-smoke` and the
corresponding relay audit. Integration samples are not competitive win-rate estimates.

The independent release contains 12 files, 18,200 bytes compressed / 46,252 bytes
uncompressed, all executable scripts Python-only. The manifest records hashes.
51 protected files from the previous agents/opponent remain unchanged. No formal
course submission is performed. Commands (use new output directories/seeds):

```sh
.venv/bin/hs-arena validate control_priest --no-game
.venv/bin/python -m unittest tests.test_control_priest tests.test_priest_safety -v
.venv/bin/python -m development.priest.run --candidate control_priest --out experiments/priest-reproduce --version reproduce --start 51100 --seeds 20
.venv/bin/hs-arena play --p1 client:development/clients/control-priest-v2 --p2 greedy --games 3 --seed 52100 --out experiments/priest-reproduce-mcp/games
.venv/bin/python -m development.priest.build
```

Real Luna uses the installed VS Code Codex binary via a process-local PATH, as documented
in the root README. Raw games remain local under ignored `games/`; configs, metrics,
failure states, tests and reports are tracked in Git. A fresh checkout requires the
course-provided hs-arena 0.2.2 distribution, which is intentionally not vendored here.
