# control-priest-v2 experiment

Transport: real GPT-6-Luna skill through official MCP launcher. Runtime: hs-arena 0.2.2.

Results: 2/3 wins (66.7%); Wilson 95% interval [0.208, 0.939].
Mean global turns: 21.666666666666668; mean outgoing hero damage: 27.666666666666668.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Initial fixed-deck baseline.

Next hypothesis: Add bounded tactical search without changing the deck.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

## Acceptance and next hypothesis

Passed final V2 model integration: 2 wins in 3 games; all 125 actions exactly relayed, zero execution defects. This sample is not a competitive win-rate estimate.

Improve early stabilization against Face Hunter in a separate future development block; do not tune on consumed validation seeds.
