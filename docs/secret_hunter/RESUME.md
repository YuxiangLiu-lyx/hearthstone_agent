# Run and resume this research

Working directory: `/Users/liuyuxiang/Documents/USA/agenticForEverything/hearthstone`.
Branch: `research/secret-hunter-20261110`. The original HEAD is recorded in PLAN.md.
Use the existing `.venv`; no package installation or new service is required.

## Integrity and status

These commands were actually run. They do not start matches:

```sh
.venv/bin/python -m development.secret_hunter.verify
.venv/bin/python -m development.secret_hunter.status
.venv/bin/python -m development.secret_hunter.archive
```

`verify` checks the final ZIP against its manifest and extraction, all 30 fixed
cards, the allowed dependencies, 339 installed runtime files, the 14 frozen
opponents, and 205 protected historical files. It runs the official static validator.
`status` shows completion, active decision sequences and forfeits without reading
held-out wins. `archive` reconciles completed/reserved budget and version hashes.

The final extracted artifact also passed this exact 16-test mechanism/fault command
(123 microfixtures, separately budgeted; running it again consumes more short cases):

```sh
.venv/bin/python -m development.secret_hunter.checks --candidate development/secret_hunter/frozen-C5/secret-hunter-agent --out docs/secret_hunter/checks-extracted.json
```

The final C5 extraction is `development/secret_hunter/frozen-C5/secret-hunter-agent`.
The C4 extraction and archived ZIP remain available separately. Do not modify a
frozen directory or use its old results to describe different bytes. Building again
is unnecessary for verification and requires a new, absent freeze directory.

## Real course skill launch

The following exact command was executed for the final C5 ZIP integration game.
Its existing output directory is an archive; do not overwrite it:

```sh
PATH="/Users/liuyuxiang/.vscode/extensions/openai.chatgpt-26.1007.21434-darwin-arm64/bin/macos-aarch64:$PATH" .venv/bin/hs-arena play --p1 skill:development/secret_hunter/frozen-C5/secret-hunter-agent --p2 greedy --games 1 --seed 62560 --parallel 1 --max-turns 180 --out experiments/secret-c5-zip-cli-smoke
```

The process-local PATH selects the working existing Codex installation; the global
`/opt/homebrew/bin/codex` was broken in this environment. The course loader selects
gpt-6-luna/medium using the existing login. Never print credentials. This is skill
mode, not client mode. No independent model endpoint, extra model or subagent is used.
The 180-turn draw cap is separate from the unchanged 180-second decision timeout.

The frozen C5 paired schedules were actually launched as follows, with the same
PATH prefix as above on both skill commands:

```sh
.venv/bin/python -m development.secret_hunter.run --candidate development/secret_hunter/frozen-C5/secret-hunter-agent --out experiments/secret-c5-model-confirmation --mode skill --start 163100 --seeds 1 --workers 2 --split confirmation
.venv/bin/python -m development.secret_hunter.run --candidate development/secret_hunter/ablation-C5/secret-hunter-agent --out experiments/secret-c5-ablation-confirmation --mode skill --start 163100 --seeds 1 --workers 2 --split confirmation
.venv/bin/python -m development.secret_hunter.run --candidate development/secret_hunter/frozen-C5/secret-hunter-agent --out experiments/secret-c5-python-confirmation --start 162100 --seeds 20 --workers 4 --split confirmation
.venv/bin/python -m development.secret_hunter.run --candidate development/secret_hunter/candidates/A0-script/secret-hunter-agent --out experiments/secret-a0-c5-python-confirmation --start 162100 --seeds 20 --workers 4 --split confirmation
```

## Safe continuation

Do not launch a second writer into an active run. Let existing official games finish;
killing the main model forfeits that game. If a scheduler has stopped, inspect its
log and every active game before using `--resume`. That flag checks the original
candidate/pool hashes and schedule, skips recorded complete games, and refuses any
unfinished or unrecorded game directories. It neither silently repeats an unknown
attempt nor repairs an interrupted official model session.

This no-op resume command was actually tested after its 56-game run completed;
it verifies hashes and reports that all scheduled games already exist:

```sh
.venv/bin/python -m development.secret_hunter.run --candidate development/secret_hunter/candidates/A0-script/secret-hunter-agent --out experiments/secret-a0-development --start 62010 --seeds 2 --workers 4 --resume
```

For an otherwise resumable incomplete schedule, append `--resume` to its original
command, keeping all schedule arguments identical. The completed-run no-op is the
tested recovery case; no interrupted main-model session recovery is claimed.
Three consecutive course-side failures stop scheduling unstarted work and allow
already running matches to finish. Own illegal actions, timeouts and early exits
remain losses; they are not reclassified as external quota failures.

Recompute reports only when all corresponding summaries exist:

```sh
.venv/bin/python -m development.secret_hunter.archive
.venv/bin/python -m development.secret_hunter.usage
.venv/bin/python -m development.secret_hunter.final_report --version C4
.venv/bin/python -m development.secret_hunter.final_report --version C5
```

The experiment runner executes a supplied frozen candidate; it is not an autonomous
research proposer. Further research requires a real development-agent session to
read SOURCES.md, ITERATIONS.md, REPORT.md, the budget and failure evidence, choose a
new hypothesis, create a new version, and run only unconsumed development seeds.
Do not tune on these confirmation seeds. The current session has not created a
mock proposer, background evolution service or unattended training claim.

The strict timing blocker is in CONTRACT.md: this official skill cannot submit
independently while its main Luna generation stalls. Changes to prompts alone
cannot establish that guarantee. Keep the release research-only until the official
host provides a supported control path and actual execution defects are resolved.
