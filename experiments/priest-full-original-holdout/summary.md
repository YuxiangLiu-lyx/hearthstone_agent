# priest-full-original-holdout experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 892/1120 wins (79.6%); Wilson 95% interval [0.772, 0.819].
Mean global turns: 22.2125; mean outgoing hero damage: 28.538392857142856.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Extend validation to the historical 14-opponent suite; frozen policy and deck.

Next hypothesis: Report coverage and per-matchup weaknesses; do not retune on these seeds.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Acceptance: Full 1,120-game coverage completed; report both frozen arms and all 14 matchups. No policy tuning on these seeds.
