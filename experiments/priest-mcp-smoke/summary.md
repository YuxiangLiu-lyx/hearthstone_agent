# control-priest-v1 experiment

Transport: real MCP client, no model. Runtime: hs-arena 0.2.2.

Results: 2/3 wins (66.7%); Wilson 95% interval [0.208, 0.939].
Mean global turns: 26; mean outgoing hero damage: 24.333333333333332.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Initial fixed-deck baseline.

Next hypothesis: Add bounded tactical search without changing the deck.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Completed MCP integration; exact outcomes and reliability are in metrics.json.
