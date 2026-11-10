# Repository and preserved agents

Remote: https://github.com/YuxiangLiu-lyx/hearthstone_agent

The repository was initialized from the existing workspace before Face Hunter development.
The `pre-face-hunter` tag preserves this starting point. Face Hunter is developed in a
separate `face_hunter/` skill and does not replace the existing agents.

## Existing releases

| Agent | Source | Frozen checkpoint | Release |
|---|---|---|---|
| Paladin Champion | `submission/hearthstone-agent` | `development/checkpoints/v3-paladin-relay-champion` | `dist/hearthstone-agent.zip` |
| Zoo v6 | `development/candidates/v6-zoo-guide` | Existing candidate is retained | `dist/hearthstone-zoo-candidate.zip` |
| Zoo v7 | `development/candidates/v7-zoo-strength` | `development/checkpoints/v7-zoo-strength` | `dist/hearthstone-zoo-strength.zip` |

Historical candidates, champion pointers, deck recipes, benchmark code and reports remain
versioned. `development/checkpoints/pre-face-hunter-sha256.json` records the original skill
files and release hashes so later changes can be checked for unintended regressions.

## Local artifacts

The official `hs-arena-0.2.2/` distribution, virtual environment, raw experiment directories,
and generated replay media are retained on the development machine and excluded from Git.
Obtain the official course distribution and place it in `hs-arena-0.2.2/` before following
the installation commands in the root README. Do not replace the course engine with a
different implementation.

The official runtime and all historical raw logs remain available locally. Git stores
the development scripts, recorded analyses and release artifacts needed to inspect the
existing work. New experiment summaries should be committed; large raw game logs stay
under each experiment's ignored `games/` directory.
