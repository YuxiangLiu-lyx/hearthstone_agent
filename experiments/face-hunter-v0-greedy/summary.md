# v0 experiment

Transport: real MCP client, no model. Runtime: hs-arena 0.2.2.

Results: 1/3 wins (33.3%); Wilson 95% interval [0.061, 0.792].
Mean global turns: 13.333333333333334; mean outgoing hero damage: 22.666666666666668.
Illegal actions: 0; timeouts: 0; early exits: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Initial fixed-deck baseline.

Next hypothesis: Add bounded tactical search without changing the deck.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.
