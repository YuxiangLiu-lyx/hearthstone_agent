# original experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 151/300 wins (50.3%); Wilson 95% interval [0.447, 0.560].
Mean global turns: 21.79; mean outgoing hero damage: 21.973333333333333.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: original

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Retained original opponent reference; never changed the actual opponent source.
