# priest-full-v2-holdout experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 1012/1120 wins (90.4%); Wilson 95% interval [0.885, 0.920].
Mean global turns: 21.748214285714287; mean outgoing hero damage: 30.71607142857143.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Extend validation to the historical 14-opponent suite; frozen policy and deck.

Next hypothesis: Report coverage and per-matchup weaknesses; do not retune on these seeds.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Acceptance: Full 1,120-game coverage completed; report both frozen arms and all 14 matchups. No policy tuning on these seeds.
