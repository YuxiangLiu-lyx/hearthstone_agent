# Astra sprint preregistration

Started 2026-11-15 01:25:10 UTC (2026-11-14 20:25:10 ET). The binding deadline is
2026-11-15 11:25:10 UTC (06:25:10 ET), ten hours after start. The later delivery
deadline is November 15 at 22:29:59 ET. The initial development/selection cutoff
is 08:25:10 UTC, leaving three hours for final CLI validation and packaging.

Anchor: `8c158c07280788d7b7872476dd728ba43e3e71ca`. Baseline is **DARCL2**,
source fingerprint `e0cf461721004b82ab70cd128fbdd99ab2d59bb8e6c561d11449f8ea06d3b6c4`.
The original fallback ZIP has SHA-256
`0130813f56655e7b802e2cbbe539526f6ab2a1a8f1acf4d27af6e5fdee5a9a0e`.
It contains one Arcane Shot and no King Krush. Old B is not this baseline.

## Resources and partitions

Every attempted game, including interrupted and failed launches, consumes the
18,000 full-game budget. Every attempted continuation consumes the independent
16,000 continuation budget. At least 5,000 full attempts remain unavailable to
development. The ledger also charges protocol games. Original ledgers and
opponent snapshots are preserved. All historical replay evidence is seen data.

| Partition | Inclusive source-seed interval |
| --- | --- |
| CLI pilot | 62140000–62140099 |
| Development | 62150000–62159999 |
| Label holdout | 62160000–62169999 |
| Optional conditional confirmation | 62170000–62179999 |
| Candidate selection core | 62250000–62250079 |
| Candidate selection guard | 62251000–62251007 |
| Frozen final core | 62350000–62350169 |
| Frozen final guard | 62450000–62450015 |
| Protocol acceptance | 62550000–62550099 |

One source seed's seats, opponents, roots, and alternate worlds remain in one
partition. Only the existing core six and guardrail fourteen opponents and
course Greedy Mage are permitted. Installed engine 0.2.2 and opponent files are
hashed in the run manifest before the first match.

## Initial measurement and diagnosis

The full CLI pilot uses four core groups at concurrency 3, then four new groups
at concurrency 6 (seeds 62140000–003 and 62140010–013). Compare throughput and
P95/P99/max decision time. Select concurrency from reliability and tail latency.
Before opening selection, choose 170 final core groups if measured completion
time plus a 45-minute protocol/packaging allowance fits; otherwise choose 100 if
they fit. If neither fits, validate and deliver original DARCL2. The choice is
independent of final outcomes and is never extended after final opening.

Initial replay sources: 60 development groups 62150000–059 and 40 independent
label-holdout groups 62160000–039, all core opponents and both seats. Natural
failure-pattern frequency uses every unscreened source game as denominator.
Mine at most 144 development roots and 96 holdout roots, with board/sticky/tempo
targets 60/60/24 and 40/40/16 respectively. Within proxy, prioritize balanced
engine-first/second strata and approximately two losses per win, filling rare
strata from available games. Round-robin source seeds limits domination by a
single seed. Choose the earliest legal action divergence in own turns T2–T5;
record unavailable/eligible denominators. A root may have baseline and at most
five distinct first-action alternatives covering coin development, targeted
clearing, ordinary development, secret ordering, face damage and hero power.

Each root is replayed from the original public prefix. World 0 reproduces the
original game; worlds 1 and 2 retain original hidden hands and independently
permute both remaining decks and future engine randomness. This is a limited
posterior, not an inference of the opponent's hand. All routes at one root and
world begin identically. Original baseline terminal and root state must match.
Development worlds 0/1 can inform route choice. World 2 and all source-holdout
labels are withheld from rule selection until a concrete hypothesis is locked.
Read both rescued losses and damaged original wins before advancing a rule.

The first mechanism must address observed candidate recall or pruning if the
evidence supports it. A ranking mechanism requires evidence that winning routes
were retained and misvalued. Every candidate has an immutable parent, hypothesis,
fingerprint and fixed search budget; first round fixes all 30 cards and mulligan.
Run fresh paired complete games before retaining a mechanism. Target 2–3 rounds;
stop unproductive directions after checking trigger/recall and regression cases.
Prior trap mulligan, TRPLY/TRPLY2 and Miller failures remain negative evidence.

## Selection and final decision

Selection compares DARCL2 with at most two candidates on the independent core
80 groups and guard 8 groups. Highest reliable equal-weight Astra mean wins.
Candidates within 0.5 percentage points of the best may be separated by the
same paired, seat-balanced 6/4/4 simulation's mean `max(score - 10, 0)`, then
fewer source edits, then stable name. Simulation sampling parameters must be
written before selection opens. Local simulation is not a formal course score.

Freeze a single challenger and original DARCL2 as exact ZIPs, with extraction
paths, engine/opponent fingerprints and final seed counts. Final core and guard
run the complete CLI. Monitor counts and failures only; read outcomes only after
both pools are complete. Match `(opponent, seed, seat)` and bootstrap complete
source-seed clusters, preserving all opponent/seat observations per seed.

Promotion requires Astra mean gain at least +2.0 pp, one-sided 90% lower bound
strictly above zero, and at least two Astra proxy point gains nonnegative.
Report two-sided 95% intervals and each proxy. Maximum regression: Bot1 2.0 pp,
Bot2 3.0 pp, guard 2.0 pp. Report both seats and actual engine order, flips, and
possible effects on the course's 5/6 and 3/4 win caps. Ordinary runs must have
zero illegal actions, timeouts, forfeits, early exits or unexpected fallbacks;
every full Python CLI decision must be at most two seconds.

Validate exact selected bytes with `hs-arena validate`, real entrypoint phases,
stale sequence and intentional fault recovery, Luna both seats and ClientSeat
protocol checks. Distinguish Python timing from state-publication-to-MCP-act
timing. If real Luna is unavailable, document the gap. Only recommend one ZIP;
any failed gate or incomplete final sample selects the original fallback bytes.
The user will make the formal Slack submission.
