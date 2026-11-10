# v1 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 21/40 wins (52.5%); Wilson 95% interval [0.375, 0.671].
Mean global turns: 13.5; mean outgoing hero damage: 24.45.
Illegal actions: 0; timeouts: 0; early exits: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Fixed-deck strategy comparison

Next hypothesis: Use False for absent hero poisonous flag, test it against the engine, then repeat all arms.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.
