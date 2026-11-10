# Resume checkpoint

Current stable release: `development/checkpoints/v3-paladin-relay-champion`.
Its Python policy/deck are unchanged from `development/checkpoints/v2-paladin-champion`.
Current submission: `submission/hearthstone-agent`; build provenance: `development/checkpoints/CHAMPION.json`.
Archive: `dist/hearthstone-agent.zip`; exact bytes/hash: `dist/build.json`.
All previous Champions and failed candidates are retained. Official package source is unchanged.

Completed: source audit, offline runtime install, baseline, real-engine harness, eight-style opponent population,
paired deck-policy ablation, independent holdouts, two Champion promotions, bounded tactical search research,
engine differential tests and replay verification, deck neighborhood search, adversary search, MCP transport
testing, real Luna integration, stateless watchdog entrypoint and reproducible ZIP builder.

Do not promote v1 Mage heuristics, v2 Mage search, local deck mutations, or v4 Paladin search: they failed
the predefined acceptance gate. Four missed lethal scenarios are verified, but the rare tactical gain remains
statistically uncertain in holdout. Search is retained for future work, not shipped.

Main remaining research issue: evolved control Priest (Champion 35/80 on fresh seeds), especially late-game
resource depletion. Existing local substitutions did not reliably solve it. Opponent hidden-hand modeling,
random-lethal probability estimation and broad Monte Carlo planning were not justified or completed.

Model integration uses the official `skill:` launcher. The system Codex wrapper is broken; prepend the VS Code
binary directory documented in README. The corrected relay must be checked against `integration-paladin`
and `integration-selfplay` results. Historical early-exit failures remain visible in the reports.

The relay-only candidate `development/candidates/v5-relay` passed `integration-relay-v2` with seeds 970–972:
three wins, no forfeits/illegal actions/timeouts, and 103/103 non-setup actions produced by the script and
relayed exactly. It was promoted to v3-paladin-relay-champion. The final ZIP has been rebuilt and verified.
No experiment or integration run is pending. The retained research limitations are not hidden blockers.

Final ZIP: 8,294 bytes, uncompressed 20,513 bytes. SHA-256:
`4e4e47761e603d9ff44866f13103710a5704e132a879e765a1514407c44ca26b`.
Python benchmark total 5,724 games, zero execution faults. Hard holdout 382/480; evolved Priest 35/80.

To continue, first read `development/reports/benchmark_summary.json`, `model_integration.json`,
`paladin-loss-audit.json`, `tactics-engine-verification.json` and CHAMPION.json. Use a new experiment directory.
Consumed holdout blocks: 100000–100024, 100100–100124, 100200–100239. Choose new seeds and reserve them
before tuning. Do not infer unrun outcomes, overwrite Champion with a candidate, or count transport tests as LLM tests.

Useful next experiment: test a narrowly specified resource-preservation policy or deck change against the frozen
Priest and the full fixed population, then a new holdout. Avoid optimizing exclusively against that Priest.
Keep sample sizes predetermined; do not keep sampling until a significance threshold is crossed.

No course Slack submission has occurred. The user must explicitly authorize any formal submission.

## Zoo extension — 2026-11-10

User requested Zoo guide research, a legal deck, and specialized decisions while preserving the current
important strategy and lethal mechanisms. Completed as optional `development/candidates/v6-zoo-guide`;
see `docs/ZOO_WARLOCK.md` for sources, full deck, rules, evidence and reproduction.

The Champion and formal submission artifact are unchanged (24 protected files verified by SHA-256).
Zoo inherits exact `base_policy.py`, action validation, evaluation and watchdog from the Champion.
The existing research planner is unchanged and remains disabled. All 339 immediate-lethal decisions in
15,228 recorded Zoo states match the original policy. Specialized rules change 2,124 main decisions.

Six fixed-schedule experiments add 1,296 Python games, all without execution defects. Development:
Zoo 156/192, generic policy with identical Zoo deck 149/192, Champion 163/192. Fresh holdout:
Zoo 188/240, generic Zoo 176/240, Champion 185/240. Both paired gain intervals cross zero; no promotion.
Control Priest remains weak (16/40). The candidate was frozen before holdout; no tuning on holdout.

Consumed additional seeds: development 6000–6011; holdout 100300–100319. New holdout work should choose
another block (e.g. 100400+) and predeclare its sample size. Original benchmark summary files describe
the Paladin release; new evidence is in `development/reports/zoo-comparisons.json` and experiment folders.

Validation: Zoo tests 14 pass; candidate protocol tests 6 pass; existing Champion 6 pass and planner
research candidate 12 pass. 100 real-state CLI invocations average 59.06 ms, P99 73.22 ms, no errors.
Official MCP client test seeds 980–981: 2 wins, zero failures. This is not a Luna/Haiku test; the Zoo
candidate has no fresh LLM run. All six benchmark runs and both transport games are complete.

Independent package: `dist/hearthstone-zoo-candidate.zip`, 11,769 bytes; eight files, 30,338 bytes
uncompressed; SHA-256 `e62cdfc5340fc9984821e091b650575269f5d53ec50eca39042551983d6cccb0`.
Use `development/build_zoo.py` to reproduce it without altering `dist/hearthstone-agent.zip`.
No formal submission has occurred.

## Zoo v7 strength update — 2026-11-10

Completed the requested loss analysis and optimization. `docs/ZOO_OPTIMIZATION.md` is the current Zoo
report. Recommended Zoo branch: `development/candidates/v7-zoo-strength`; immutable copy in
`development/checkpoints/v7-zoo-strength`; separate pointer `development/checkpoints/ZOO_CHAMPION.json`.
The main CHAMPION.json, Paladin Skill/ZIP, v6 Zoo Skill/ZIP and research planner are unchanged (33 hashes).

Analyzed all 88 previous Zoo losses: 78 ended the last own decision with <=1 card, 45 encountered AoE,
35 had flagged taunt stalls. Offline replay-prefix verification and policy suffix comparison reproduced
all 35 old losses and recovered 5 with the combat change; selected-case diagnostics, not holdout games.

Final deck change: two Mortal Coils replaced by two Sea Giants; retain Abusive Sergeants. Added bounded
same-target combat scoring (<=3 actions, <=1600 nodes, <=1 burn, abstain on unknown triggers) and Giant
summon ordering with board-slot/self-damage guards. Original immediate lethal remains first; all 909
triggered lethal decisions among 39,017 final holdout observations match the inherited base exactly.

This round: 18 experiments, 8,960 complete Python games, all execution fault counts zero. Finite deck
screen 7000–7007, validation 7100–7123. Final validation 560/672 vs 523/672; paired gain CI [+2.38,+9.08] pp.
Frozen candidate held out on reserved seeds 100400–100439, 14 fixed opponents, both seats: 920/1120 vs
875/1120, +4.02 pp, paired seed-cluster 95% CI [+0.89,+7.14] pp. Both gates pass; no group down >2.5 pp.
This supports the Zoo branch update, not superiority over the main Paladin Champion. Strong Priest
remains 43/80 and search Paladin 48/80. No holdout tuning or significance-driven additional sampling.

Tests: 9 new +14 Zoo regressions +6 protocol/random-game/timeout tests pass. CLI100 mean63.92 ms,
P99 82.83 ms, max83.35 ms; no errors. MCP client seeds990–991: 2 wins, no failures. No new Luna/Haiku run.
All jobs are complete. New fresh holdout must avoid prior blocks, including100400–100439 (use100500+).

Artifact: `dist/hearthstone-zoo-strength.zip` (14,362 compressed /37,876 uncompressed bytes,9 files),
SHA-256 `ecf211e94327f0ed9c915eb04e6301497931bc98356055636c3a6e7a1a990b1e`.
Rebuild with `.venv/bin/python -m development.build_zoo_strength`. Candidate fingerprint matches the
validation copy, frozen selection, checkpoint and holdout manifest:
`80dcfb8c4dc79d39c36853acd1b848b8d2b02a4eced6bfb0334559dc9600a9c6`.
No formal submission occurred.
