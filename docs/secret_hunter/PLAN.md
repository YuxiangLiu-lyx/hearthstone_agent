# Fixed-deck Secret Hunter research plan

Status: execution started on 2026-11-10 (America/New_York), from HEAD
6a7fc2475a17190268594ef2f5940b5b3a62f8f0 on research/secret-hunter-20261110.
The working tree was clean and no applicable AGENTS.md was found. Earlier releases
and frozen opponents are protected by a file manifest. No remote publishing or course submission.

## Contract and population

Official hw2.md was fetched directly; the web renderer could only display the SPA
loading screen. Course skill, client, MCP server, protocol and example playbooks were
inspected. Luna means the official gpt-6-luna session, medium effort. A Python match
does not establish model quality; a client match does not establish skill compatibility.

Use exactly the requested 30-card multiset, including Ooze, King Krush and six
Secrets. Freeze the latest complete 14-opponent zoo-research pool used by the
Control Priest full-suite report. The recent smaller five-opponent specialist pool
contains stronger modern Zoo/Paladin/Hunter variants; the historical four-opponent
Face Hunter and other old holdouts are different populations. Do not merge them.
Report official-mage separately; primary result equally weights the other 13.

## Initial hypotheses and uncertainty

The existing balanced tempo policy is a runnable baseline, but lacks deliberate
Secret deployment and Tracking valuation. Existing Hunter lethal projection can be
reused only inside its declared effect coverage. Unknown effects or truncated search
must yield unknown, not a proof of no lethal. Guide knowledge suggests a board-first
opening and a contextual transition to Bow/power/burn; delayed secrets, bad trap bait,
and premature burn are plausible failure modes, not established causes.

A is the fixed-deck script default. B is guide-initialized with model authority over
legal alternatives. C will be selected after at least two evidence-linked iterations.
The model may choose face/trade/curve/resource/secret plans and request extra search;
scripts calculate, validate and provide defaults. Only the main course model calls act.

First establish real skill startup, deck submission, model choice logging and tool
watchdog behavior. Audit independent submission feasibility before spending on scale.
There is no HS_ARENA_MCP environment in SkillSeat (only ClientSeat). Never assume it.
Use 2-second default calculation and 5-second normal / 10-second extra-search caps;
40-second model adoption deadline from publication, 90-second target and 30-second
official reserve. These cannot cancel or independently rescue a stalled main model
without an officially accessible transport. Mark this limit explicitly if unresolved.

## Adaptive stages and budget

Hard ceilings: 6,000 full Python games, 20,000 short cases/branches, 200 real model
games. Reserve at least 100 real model games until the final challenger is frozen.
Start with one real B game and 56 Python games per script arm (14 opponents x 2
development seeds x both seats). Inspect losses, wins, plan disagreements and
unsupported states from full public observations. Increase development samples only
for useful discrimination. Separate tutorial microfixtures and post-hoc diagnostics
from full games. Never use hidden state, seed or opponent labels for action selection.

Development seeds start 62000; candidate selection 62500. Python final confirmation
starts 162000, real confirmation 163000, unused in the inspected metadata. Split by
whole game / case family. Before confirmation freeze candidate, configs, pool, tool
chain and ZIP bytes. Real two-arm comparison with K=14, S=2, both seats costs
4*K*S=112 games. This is a maximum scheduled target contingent on measured speed
and available login/quota, not a promise to use all 200. Failed model attempts count.
If practical limits prevent that schedule, retain all negative evidence and label
unperformed comparisons unavailable; do not substitute Python percentages.

Round changes must follow previous results. Prefer a structural intervention such
as action-group diversity, effect coverage or public-history inference over a grid.
At least one review must change the diagnostic/sampling method itself. Every run
records immutable candidate/deck/config hashes, seed/seat, actual first player,
raw results, exceptions and budget. No unattended evolution is claimed: this main
development session proposes, implements and reviews each iteration.

## Frozen scoring and release gates

Draws count as losses, forfeits remain in denominators. Report W/L/D/forfeit,
opponent and actual-first-player strata, Wilson intervals as descriptive, and paired
seed-cluster gain intervals; few clusters are explicitly inconclusive. Primary 90%
is observational only. Never sample until a desirable number appears. Promotion
requires a valid ZIP, genuine model choices, exact tested artifact, no unresolved
own execution defect, honest timing claims and evidence of benefit or tradeoffs.
Unresolved official execution or strict-deadline control => research-only.
Unknown course opponents remain unknown. No deck changes, new opponents or self-play.
