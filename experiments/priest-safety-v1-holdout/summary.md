# v1 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 231/300 wins (77.0%); Wilson 95% interval [0.719, 0.814].
Mean global turns: 21.813333333333333; mean outgoing hero damage: 27.86.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: v1

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Frozen V1 reference for the V2 safety correction; same 231/300 outcomes.
