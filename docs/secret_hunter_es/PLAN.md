# F2 loss-driven evolutionary continuation

Started 2026-11-11 06:51:29 UTC; maximum 4 hours, 6,000 full games and
20,000 experimental short continuations. Frozen F2 is the same-deck baseline.
The previous 14 opponents, runtime, and 30-card deck remain unchanged.

Screen B0 and three hypotheses on 4 seeds each (448 games): exact public
effect coverage; interpretable state features; visible attack exposure.
Train a (mu=2, lambda=4) self-adaptive evolution strategy for 3 generations,
re-evaluating every parent and child on a fresh shared 4-seed block (2,016).
Validation uses 8 fresh seeds and at most 5 arms (1,120).
Freeze one candidate, then compare against F2 on 40 untouched seeds (2,240).
Reserve 56 reproduction games, 2 client games, and at most 2 relay smoke games.
Planned total 5,884, with 116 contingency games. Both seats, all 14 opponents.
Fitness and primary outcome exclude official Greedy, reported separately.

The 90% goal is aspirational. Promotion requires a positive primary paired
seed-bootstrap 95% interval, at least 1 percentage point point gain, zero own
illegal/timeout/forfeit, reliable CLI fallback, and observed decisions below 2 s.
If no candidate meets those gates, preserve F2. Do not cherry-pick holdouts.
Validation ties favor simpler modules, then the older candidate.

Paper adaptation: real-valued explanatory features, per-gene mutation scales,
parent re-evaluation, and elitist (mu+lambda) retention. Fixed opponents replace
the prohibited competitive coevolution. Use multiplicative log-normal sigma
adaptation with bounded scales; the HTML equation (9) prints an additive sigma
expression, so this is an explicit ES variant, not a literal paper replication.
No rarity score, external simulator source, runtime model, or private inputs.

Development amendment before final holdout: spend 112 of the 116 contingency
games on D1, a minimal Snake token coverage/Beast identification correction.
The engine differential fixture directly supports this additional direction.
Validation will include B0, D1, C1, the untrained feature parent matching the
best evolved finalist's exposure flag, and that evolved finalist (5 arms).
This preserves 2,300 final games and keeps the planned total at 5,996.
