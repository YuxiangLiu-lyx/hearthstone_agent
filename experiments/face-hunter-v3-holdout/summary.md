# v3 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 119/200 wins (59.5%); Wilson 95% interval [0.526, 0.661].
Mean global turns: 13.755; mean outgoing hero damage: 28.075.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Independent validation after V3 selection; no parameter selection or tuning

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Final decision: Preselected V3 retained; 119/200, with modest and uncertain advantage. No tuning on these seeds.

Next hypothesis: Improve Zoo defense with one isolated change and fresh holdout.
