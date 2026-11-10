# v0 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 113/200 wins (56.5%); Wilson 95% interval [0.496, 0.632].
Mean global turns: 13.86; mean outgoing hero damage: 28.1.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Independent validation after V3 selection; no parameter selection or tuning

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Final decision: Independent baseline reference; not a tuning run.

Next hypothesis: Use new seeds for any future tuning evaluation.
