# Experiments (2026-11-10, America/New_York)

All game counts below come from real hs-arena 0.2.2 runs. No formal course submission was made.
Exact seeds/configurations are in each experiment's manifest.json, per-game result.json and games.jsonl.
Public replay.jsonl and seat-view observations.jsonl are retained. Raw benchmark logs are development-only.

## Design and promotion rule

Paired comparisons use the same seed/opponent and both seat assignments. The engine chooses first player;
first/second statistics use result.first_player, never assume P1 starts. A draw counts as a loss for course
scoring. Any engine/harness failure invalidates a paired promotion comparison. No failures were silently removed.

Before promotion require: zero illegal actions/timeouts/early exits/policy errors; positive lower bound of a
95% paired bootstrap interval; no individual opponent win-rate decline greater than ten percentage points;
then an independent holdout passing the same rule. Bootstrap resamples seed clusters across opponents/seats,
5000 draws with fixed analysis RNG. Training selection is exploratory; intervals are not a guarantee against
all multiple-comparison effects. Wilson intervals in summaries describe marginal rates, not paired improvement.

Opponent procedures include original Greedy, face-first aggression, survivor-first control, hand-packing tempo,
draw/deathrattle value, two-ply combat search, frozen historical Champions and separately tuned adversarial policies.
The stronger adversarial Priest is a frozen copy of the generic observation-only policy with its own deck/config.
It does not inspect the Champion's hidden information. The official baseline source and original deck are intact.

## Rounds

| Experiment | Seeds | Games | Wins | Result / decision |
|---|---|---:|---:|---|
| Initial baseline fast | 1000–1001, 6 opponents × 2 seats | 24 | 15 | Stable starting checkpoint |
| Original policy + original Mage | 2000–2019 | 240 | 132 (55.0%) | Baseline |
| New policy + original Mage | same | 240 | 147 (61.25%) | +6.25 pp, CI −2.5 to +15; reject |
| Original policy + new Mage | same | 240 | 164 (68.33%) | +13.33 pp, CI +6.25 to +20.83 |
| New policy + new Mage | same | 240 | 163 (67.92%) | −20 pp vs Hunter relative to deck-only candidate; reject |
| Old Mage / new Mage holdout | 100000–100024, 4 new configurations | 200 each | 119 / 140 | +10.5 pp, CI +2.5 to +18.5; promote deck |
| New Mage + bounded search | 2000–2019 | 240 | 164 | Identical outcomes, slower; reject |
| Original policy + Paladin | 2000–2019 | 240 | 149 (62.08%) | Deck-only ablation |
| New policy + Paladin | same | 240 | 211 (87.92%) | +19.58 pp over Mage Champion, CI +10.83 to +28.33 |
| Mage / Paladin holdout 2 | 100100–100124, 5 new configurations | 250 each | 183 / 211 | +11.2 pp, CI +3.2 to +18.8; promote Paladin |
| Mage / Paladin expanded | 3000–3024, 8 opponents | 400 each | 264 / 323 | +14.75 pp, CI +7.75 to +22; confirms improvement |
| Deck local search | 4000–4007, 8 opponents | 128 per candidate | 105 baseline; 110 legendaries; 101 early; 99 draw; 95 burst | None passed screening gates; retain baseline |
| Adversary screening | 5000–5029, Champion as opponent | 60 per candidate | Priest 32; Hunter 16; aggressive Paladin 28; value Paladin 29 | Freeze Priest as a hard opponent |
| Paladin + search | 3000–3024 | 400 | 330 (82.5%) | +1.75 pp, CI +0.5 to +3.5; send to fresh holdout |
| Paladin / search holdout 3 | 100200–100239, 6 configurations incl. adversarial Priest | 480 each | 382 / 385 | +0.625 pp, CI 0 to +1.458; reject search |
| Loader isolation regression | 3000–3001, 8 opponents | 32 | recorded in summary | Every candidate action, winner and turn count exactly reproduced |

The search candidate's first implementation failed a real-engine Coin cap differential test. The original
failed source was preserved; the corrected search passes the differential suite. It remains unpromoted.
The final Paladin decision policy is byte-identical to the tested one; a later CLI watchdog and relay instruction
change were separately tested, and successful action sequences reproduced after benchmark module isolation.

## Current Champion by opponent

Expanded development benchmark, 50 games each; not an estimate over all possible opponents:

| Opponent | Wins | Rate |
|---|---:|---:|
| Official Greedy Mage | 43/50 | 86% |
| Aggressive Hunter | 42/50 | 84% |
| Control Priest | 41/50 | 82% |
| Tempo Paladin | 40/50 | 80% |
| Value Warlock | 41/50 | 82% |
| Adversarial Zoo | 44/50 | 88% |
| Search Paladin | 39/50 | 78% |
| Historical Mage Champion | 33/50 | 66% |

Fresh holdout 3, 80 games each: Control Mage 70; Tempo Warlock 60; Aggressive Paladin 72;
Value Priest 76; Search Shaman 69; evolved adversarial Priest 35. Total 382/480 (79.58%).
This harder Priest result is materially worse than the original control baseline and must not be concealed.

## Integration and execution evidence

`development/reports/model_integration.json` contains exact model results, decision latency and token counts.
`development/reports/benchmark_summary.json` contains every benchmark's first/second performance, timings,
unused mana and failure replay paths. Raw Python decision times exclude interpreter and model overhead.

The first genuine skill attempt failed before any decision because the system Codex wrapper's binary was
missing. Using the already-installed VS Code CLI fixed launch. A subsequent original baseline game completed
and won. Of three Mage Champion model games, two completed normally and one forfeited because Luna ended
its session at turn 18. This led to the explicit no-final-message-until-game-over instruction in the final Skill.

The final Paladin is tested separately using three `skill:` games against Greedy, one `skill:` vs `skill:` game,
and three inexpensive `client:` games. Pending outcomes must be read as pending until their result.json exists.
The client games completed 3/3 with wins and zero forfeits; they are MCP transport tests, not model games.

The first Paladin relay revision completed two Greedy games and self-play normally, but one Greedy game
timed out at turn 23 after the host published an end-turn-only decision. The CLI log also recorded model-list
request timeouts; this is correlated evidence, not a proven cause of the decision timeout. A later serial run
(seed 960) completed and won in 147.613 seconds. These outcomes are all retained.

Action-fidelity audit found 29 differences from the Python policy across 274 non-setup model decisions in
the first Paladin Greedy/self-play tests. Only 176 of those decisions had a recorded script invocation followed
by an exact relay. Some uninvoked moves happened to match the policy. This prompted a shorter, stricter
transport-only Skill (`development/candidates/v5-relay`), tested separately in `integration-relay-v2`.
Do not transfer Python win-rate estimates to model sessions that improvise their own actions.

The exact packaged Python CLI was timed on 100 recorded real observations: mean 54.14 ms, P95 58.12 ms,
P99 59.55 ms, maximum 71.41 ms, no errors. These include interpreter startup, worker process, JSON and
validation. The policy alone is much faster; see the per-run summaries. A 2-second watchdog failure was
injected in an isolated temporary copy and produced a legal fallback within the test's 1.5-second bound
(the injected test used a 0.1-second configured budget).

Luna is the local model recommendation because it is actually available and tested. Haiku was not tested:
`claude` is absent from PATH. No reliability comparison between the two models is claimed.

## Final release acceptance

The minimal relay revision passed all three genuine Luna skill games (seeds 970, 971, 972): three wins,
zero illegal actions, zero timeouts and zero early exits. Durations were 180.053, 119.535 and 160.518 seconds;
game lengths were 24, 12 and 13 global turns. Every one of the 103 non-setup actions had a recorded script
invocation and was relayed exactly; all three decks were accepted. Measured model/MCP decision latency:
mean 4.217 s, P95 5.714 s, maximum 16.363 s. These are three smoke games, not a statistically precise model win rate.

Promoted relay snapshot: `development/checkpoints/v3-paladin-relay-champion`. Its Python files, deck and config
are byte-identical to `v2-paladin-champion`; only SKILL.md changed. The final ZIP is 8,294 bytes, 20,513 bytes
uncompressed, with seven files under exactly one skill root. SHA-256 and the file list are in dist/build.json.
The archive was checked against the checkpoint and tested from an isolated extraction. No dependency installation
or development directory is needed at runtime.

Total real Python benchmark games across all recorded experiments: 5,724; illegal actions, timeouts, early
exits, engine/harness errors: all zero. This total includes repeated regression and screening games; it is not
an independent sample for calculating one overall win rate. Model failures are reported separately above.

Current policy timing and positional statistics: expanded pool 162/200 first and 161/200 second; harder
holdout 3 201/240 first and 181/240 second. Mean global game length 19.05 / 19.76 turns. Mean unused mana per
ended turn 0.72 / 0.79. See the JSON summaries for all distributions, per-class results and failure replay paths.
