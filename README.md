# Hearthstone Agent Arena

Face Hunter is available as a separate validated skill: [project report](docs/face_hunter/README.md),
[submission ZIP](dist/face-hunter-agent.zip), [skill](face_hunter/SKILL.md), and
[offline win/loss review](docs/face_hunter/review.html). V3 won 119/200 on an untouched,
equally weighted four-opponent holdout (95% Wilson interval 52.6%–66.1%). Three real Luna
games completed with two wins and all 77 actions relayed exactly from Python. The
original fixed Hunter deck is retained after an inconclusive deck-only challenger.
Hunter has its own `FACE_HUNTER_CHAMPION.json`; existing Paladin and Zoo releases are unchanged.

Validated local Champion: `v3-paladin-relay-champion`, a stateless Python tempo/value Paladin policy with a Luna MCP relay.
The exact course runtime and files in `hs-arena-0.2.2/` are unchanged. Nothing has been submitted to Slack.

Submission: [`dist/hearthstone-agent.zip`](dist/hearthstone-agent.zip).
Skill: [`submission/hearthstone-agent/SKILL.md`](submission/hearthstone-agent/SKILL.md).
Results and limits: [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md), [`docs/STRATEGY.md`](docs/STRATEGY.md).
Resume state: [`docs/PROGRESS.md`](docs/PROGRESS.md).

Original Paladin release: 8,294-byte ZIP (20,513 bytes uncompressed). Its 5,724 Python benchmark games completed without
illegal actions, timeouts or execution failures. Current policy: 323/400 on the expanded development pool;
382/480 on the harder fresh holdout including the evolved Priest. The final relay completed three real Luna
games with three wins, zero forfeits and exact script relay for all 103 non-setup actions. Earlier model
timeouts, early exits and action deviations are retained and discussed in the report.

Recommended Zoo branch: [v7 loss analysis, deck and validation](docs/ZOO_OPTIMIZATION.md),
[v7 ZIP](dist/hearthstone-zoo-strength.zip). Sea Giants and bounded coordinated exchanges improved fresh
paired holdout wins from 875/1120 (v6) to 920/1120 (v7), a +4.02 percentage point gain with a 95% seed-cluster
interval of [+0.89, +7.14]. This round adds 8,960 Python benchmark games without execution defects.
[The original v6 guide and evidence](docs/ZOO_WARLOCK.md) and its ZIP are retained. The Paladin Champion,
formal release, immediate-lethal branch and retained research planner remain unchanged. The separate
`ZOO_CHAMPION.json` selects v7 for Zoo only. No fresh Zoo LLM validation has occurred.

## Reproduce

From this directory, Python 3.11:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links hs-arena-0.2.2/wheels hs-arena-0.2.2/hs_arena-0.2.2-py3-none-any.whl
.venv/bin/hs-arena validate submission/hearthstone-agent --no-game
.venv/bin/python development/tests/test_agent.py submission/hearthstone-agent -v
.venv/bin/python development/tests/test_agent.py development/candidates/v4-paladin-search -v
.venv/bin/python -m development.benchmarks.run --candidate submission/hearthstone-agent --population development/opponents/expanded.json --out development/experiments/reproduce-champion --start 3000 --seeds 25
.venv/bin/python -m development.benchmarks.compare development/experiments/mage-expanded development/experiments/reproduce-champion
.venv/bin/python -m development.benchmarks.audit_replays development/experiments/paladin-expanded --out development/reports/reproduced-audit.json
.venv/bin/python -m development.benchmarks.verify_tactics
.venv/bin/python -m development.report
.venv/bin/python development/build.py
```

Each experiment destination must be new, preventing accidental overwrite. Benchmark seeds below 100000 are
development seeds. Holdout uses `--split holdout --start 100000` or greater; do not reuse already examined
holdout blocks to claim fresh validation. Historical outcome/action determinism was checked after loader isolation.

## Real model integration

Use the official launcher and an installed, logged-in CLI:

```sh
.venv/bin/hs-arena play --p1 skill:submission/hearthstone-agent --p2 greedy --games 3 --seed 970 --parallel 1 --out development/experiments/reproduce-skill
.venv/bin/hs-arena play --p1 skill:submission/hearthstone-agent --p2 skill:submission/hearthstone-agent --games 1 --seed 940 --out development/experiments/reproduce-selfplay
.venv/bin/hs-arena replay development/experiments/integration-paladin/g_20261110_000002
```

On the development machine, `/opt/homebrew/bin/codex` is a broken wrapper (missing arm64 executable).
Tests use the existing VS Code binary by prepending this directory to PATH for the command:

```sh
PATH="/Users/liuyuxiang/.vscode/extensions/openai.chatgpt-26.1007.21434-darwin-arm64/bin/macos-aarch64:$PATH" .venv/bin/hs-arena play --p1 skill:submission/hearthstone-agent --p2 greedy --games 3 --seed 970 --parallel 1 --out development/experiments/reproduce-skill
```

This changes only that process's PATH. No global installation or authentication was changed.
For the general CLI interface see [official Codex CLI documentation](https://learn.chatgpt.com/docs/codex/cli).

Cheap MCP transport test:

```sh
.venv/bin/python -m development.benchmarks.make_client submission/hearthstone-agent development/clients/reproduce
.venv/bin/hs-arena play --p1 client:development/clients/reproduce --p2 greedy --games 3 --seed 950 --out development/experiments/reproduce-client
```

Development optimizers never promote automatically:

```sh
.venv/bin/python -m development.optimizers.local_search --out development/experiments/reproduce-deck-search --start 4000 --seeds 8
```

The supplied handout lists November 15, 2026, 23:59:59 Eastern Time as the deadline. The user retains all
three formal submission opportunities; local runs do not consume them. Formal upload requires explicit approval.
