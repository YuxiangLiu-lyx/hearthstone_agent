# Program-only Secret Hunter research

Frozen before comparisons on 2026-11-11. Four-hour round starts 05:54:40 UTC and ends 09:54:40 UTC. Maximum 6,000 full games and 20,000 short continuations. At least 1,680 games (28%) reserved for final paired confirmation. No runtime strategic model, self-play, new opponents, hidden-state features, deck changes or formal submissions.

The baseline P0 preserves the existing C5 default Python action (guide ranking plus covered deterministic lethal search). Historical holdouts and replays are development data. The frozen 14-opponent pool is unchanged; report 13-opponent equal-weight macro and official Greedy Mage separately. `splits.json` fixes development, validation and final seeds, both seats. Seed pairing does not preserve later random trajectories after actions diverge.

1. Profile P0 and diagnose early decisions in losses. Validate actual course interactions and conservative simulation boundaries.
2. Test three separate hypotheses on 168 paired development games per arm: P1 survival/resource scoring; P2 finite whole-turn search; P3 conditional secret/combo/weapon ordering. Keep unsupported random effects outside deterministic proofs.
3. Use measured outcomes for a small local parameter search over interpretable weights and search limits. Validate finalists and critical module ablations on the fixed 280-game validation block. Development screening has selection bias.
4. Freeze one candidate before opening the 840-game-per-arm final block. Use seed-cluster paired bootstrap, per-opponent Wilson intervals and equal-weight macros. Promote only with positive paired confidence interval, reliability and latency gates; otherwise retain P0.
5. Package a single skill root with the same Python policy and an exact relay playbook. Run official client without a model, static/extraction checks, and at most two official relay smoke games. Log each script output and compare actual act calls.

All policy inputs are public observation plus within-game public event history. Offline replay tools may reconstruct the official engine for counterfactual validation, but never pass private engine objects, seed, opponent name, deck order or RNG into policy. Full-game and short-continuation ledgers are separate. Reference repositories are read only; implementations are repository-native and no external simulator is vendored.
