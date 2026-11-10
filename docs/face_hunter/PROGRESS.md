# Face Hunter progress

M0: official hs-arena 0.2.2 inspected; exact 30-card deck validated.
M1: full real MCP transport works, with no illegal actions, timeout or early exit.
Initial smoke: 3/3 against random and 1/3 against greedy; these are small samples.

M2: current-turn search and official-engine differential tests pass, including all
12 requested combinations. A constructed engine scenario shows V0 spending mana on
Highmane instead of a lethal; the planner completes the actual lethal.
M3: next-turn and risk modules pass targeted tests. Thirty tests passed together;
an additional hard-watchdog regression passed separately. See planning-tests.txt.

The first four 40-game screens exposed a missing hero poisonous flag in the baseline.
The exception was contained by legal fallback, but the affected arms are rejected for
promotion and retained as diagnostic evidence. The repaired screens have zero policy
exceptions, illegal actions, timeouts or early exits:

| Version | Wins / games |
|---|---|
| V0 | 25 / 40 |
| V1 | 26 / 40 |
| V2 | 28 / 40 |
| V3 | 30 / 40 |

These development samples suggest a possible benefit; they do not establish a long-run
win rate. Search has a 1,600-node cap and a 0.2-second deadline in the repaired arms,
plus the separate 2-second CLI watchdog. Initial V1 screen used a 0.06-second deadline.

All four repaired versions are frozen in development/checkpoints/face-hunter-v*-fixed.
All 45 original Paladin/Zoo protected hashes remain identical. Next: larger paired
experiments, independent validation, final Luna integration and packaging.
