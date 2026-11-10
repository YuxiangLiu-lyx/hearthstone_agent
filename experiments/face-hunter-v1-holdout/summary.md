# v1 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 116/200 wins (58.0%); Wilson 95% interval [0.511, 0.646].
Mean global turns: 13.625; mean outgoing hero damage: 27.825.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Independent validation after V3 selection; no parameter selection or tuning

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Final decision: Independent ablation: +1.5 percentage points versus V0.

Next hypothesis: Selective search widening should be tested on development data.
