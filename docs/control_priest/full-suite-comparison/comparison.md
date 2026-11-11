# Full Control Priest validation: 1,120 games per arm

The earlier final check used five opponents, 30 seeds and two seats (300 games).
The 3,240-game total pooled development and multiple comparison arms; it did not
establish 1,120-game coverage for the final agent. This report closes that gap.

Both versions were frozen before fresh seeds 152000–152039. The population,
opponent policies and decks exactly match the historical Zoo 14-opponent suite.
Each opponent receives 40 seeds in both seats, or 80 games per arm. The official
hs-arena 0.2.2 engine executes real games without model calls. The 300-game result
against five stronger/current local opponents remains a separate test population.

## Overall results

| Agent | Wins / games | Rate | Wilson 95% | Mean turns | Mean hero damage |
|---|---:|---:|---|---:|---:|
| Original opposing Priest | 892/1120 | 79.64% | 77.19%–81.90% | 22.21 | 28.54 |
| Frozen final Priest V2 | 1012/1120 | 90.36% | 88.49%–91.95% | 21.75 | 30.72 |

Paired V2 improvement: **+10.71 percentage points**,
95% seed-cluster bootstrap interval [+6.61, +14.91] points.
There are 180 paired gains and 60 paired losses.
Bootstrap uses 10,000 whole-seed resamples with analysis seed 598. The interval
describes this fixed local population; it is not a Mystery Bot or Astra estimate.

## Every opponent

| Opponent | Original wins / 80 | V2 wins / 80 | V2 rate | Change |
|---|---:|---:|---:|---:|
| official-mage | 64 | 67 | 83.75% | +3.75 pp |
| aggressive-hunter | 45 | 58 | 72.50% | +16.25 pp |
| control-priest | 79 | 78 | 97.50% | -1.25 pp |
| tempo-paladin | 61 | 78 | 97.50% | +21.25 pp |
| value-warlock | 77 | 76 | 95.00% | -1.25 pp |
| adversarial-zoo | 55 | 69 | 86.25% | +17.50 pp |
| search-paladin | 65 | 75 | 93.75% | +12.50 pp |
| historical-mage | 52 | 66 | 82.50% | +17.50 pp |
| control-mage | 69 | 73 | 91.25% | +5.00 pp |
| tempo-warlock | 74 | 78 | 97.50% | +5.00 pp |
| aggressive-paladin | 61 | 76 | 95.00% | +18.75 pp |
| value-priest | 77 | 77 | 96.25% | +0.00 pp |
| search-shaman | 73 | 76 | 95.00% | +3.75 pp |
| adversarial-priest-v1 | 40 | 65 | 81.25% | +31.25 pp |

## Actual first and second player

Seat assignment and actual first player are distinct; both seats were tested.

| Actual order | Original wins / games | V2 wins / games |
|---|---:|---:|
| First | 467/560 | 516/560 |
| Second | 425/560 | 496/560 |

## Reliability, failures and limits

Across both complete arms (2,240 games), neither player has a policy exception,
illegal action, timeout, forfeit or engine void. Full schedules and both-player
execution records are checked before producing this report.

Final V2 loss signals (overlapping observations, not proven causes):

- visible_board_lethal_threat: 64
- low_hand_resources: 20
- opposing_taunt: 18
- race_or_board_loss: 40

Every loss has a concrete public state and chosen action in
`experiments/priest-full-v2-holdout/failure-states.json`; official replays remain
locally in that run's ignored `games/` directory. Direct-lethal priority is
audited separately; no exhaustive zero-missed-lethal claim is made.

No card, strategy weight, submitted source or ZIP changed in this extension.
Previous 25 engine tests and real Luna 2–1 / 125 exact relays remain applicable.
The historical suite is broader in styles, while the smaller current pool contains
newer frozen champions. Do not compare their aggregate percentages as a strength
change. Do not directly rank this Priest against historical Zoo percentages from
different seeds; that would require a fresh paired comparison.

Acceptance: complete historical coverage and report the frozen result without
retuning. Next hypothesis: improve stabilization against the modern Face Hunter
and test any future change on new development seeds before fresh validation.
