# v1 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 111/200 wins (55.5%); Wilson 95% interval [0.486, 0.622].
Mean global turns: 21.205; mean outgoing hero damage: 23.385.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: v1

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Retained development comparison; the final selection was frozen before the subsequent validation block.
