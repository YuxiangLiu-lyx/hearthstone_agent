# Hearthstone Agent Arena

## Secret Hunter and teacher evaluation (2026-11-11)

The canonical general-purpose Secret Hunter release is **H7**, selected by
[`SECRET_HUNTER_CHAMPION.json`](SECRET_HUNTER_CHAMPION.json):
[report](docs/secret_hunter_tactics/REPORT.md), [ZIP](dist/secret-hunter-program.zip),
[strategy](docs/secret_hunter_tactics/STRATEGY.md). H7 won 960/1040 on the earlier
fixed 13-opponent holdout against F2's 910/1040. That result does not estimate
performance against the teacher's Astra agent.

The teacher-returned **Submission 1** actually used Warlock: bot1 6–0, bot2 1–3,
Astra 0–4. The original files are preserved in
[`experiments/teacher-submission-1/raw/`](experiments/teacher-submission-1/raw/),
with SHA-256 hashes in the parent manifest. The new Hunter investigation uses
revealed cards and several explicit deck/strategy hypotheses as its core tests:
[analysis, results and release decision](docs/teacher_eval/REPORT.md),
[core opponent manifest](development/teacher_eval/core.json),
[reproduction commands](docs/teacher_eval/REPRODUCE.md).
These are local proxies, not new official Astra results.

The separate [D1 teacher-focused ZIP](dist/secret-hunter-teacher-d1.zip) replaces
King Krush and Misdirection with two Arcane Shots. Its frozen core confirmation
won 393/480 versus H7's 355/480, but it failed the original-pool regression guard
(240/280 versus 252/280). D1 is a scoped candidate; H7 remains the default.

The champion pointer and `secret-hunter.code-workspace` remain at the repository
root because existing verification scripts and relative workspace paths use
those locations. The focused workspace now includes Teacher tests and Teacher
results. See [workspace layout](docs/WORKSPACE.md).

Historical rounds remain available: [F2](docs/secret_hunter_program/REPORT.md),
[the ES continuation that retained F2 at that time](docs/secret_hunter_es/REPORT.md),
and [earlier hybrid research](docs/secret_hunter/PLAN.md). The ES ZIPs are research
artifacts; H7 supersedes the old F2 recommendation.

Control Priest adds permanent/temporary theft, attack-reduction setup, health-buff
exchanges and durable minions: [report](docs/control_priest/README.md),
[deck](docs/control_priest/DECK.md), [ZIP](dist/hearthstone-control-priest.zip).
Final V2 wins 231/300 on fresh five-opponent validation versus 151/300 for the copied
opposing Priest, a paired +26.7 points (95% seed-cluster interval +18.7 to +35.0).
The restored [full 14-opponent test](docs/control_priest/full-suite-comparison/comparison.md)
uses 40 fresh seeds and both seats: **1012/1120 (90.36%)** versus **892/1120 (79.64%)**,
a paired +10.71 points (95% seed-cluster interval +6.61 to +14.91), with no execution
defects in either arm. These populations have different difficulty; the policy is unchanged.
The original Priest opponent and all earlier agent releases remain unchanged.

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

The supplied handout lists November 15, 2026, 23:59:59 Eastern Time as the deadline.
The teacher export records Submission 1. Local runs do not consume formal submission
opportunities; the remaining allowance follows the course records. Formal upload requires explicit approval.
