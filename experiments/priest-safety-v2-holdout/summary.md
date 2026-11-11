# v2 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 231/300 wins (77.0%); Wilson 95% interval [0.719, 0.814].
Mean global turns: 21.816666666666666; mean outgoing hero damage: 27.866666666666667.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: v2

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Accepted final V2: targeted safety correction, zero execution defects, 231/300 on fresh validation. No measured incremental win gain over V1.
