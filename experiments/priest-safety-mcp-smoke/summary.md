# control-priest-v2 experiment

Transport: real MCP client, no model. Runtime: hs-arena 0.2.2.

Results: 3/3 wins (100.0%); Wilson 95% interval [0.438, 1.000].
Mean global turns: 29; mean outgoing hero damage: 29.666666666666668.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Initial fixed-deck baseline.

Next hypothesis: Add bounded tactical search without changing the deck.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Completed MCP integration; exact outcomes and reliability are in metrics.json.
