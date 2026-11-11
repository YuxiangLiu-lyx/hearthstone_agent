# priest-full-original-smoke experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 21/28 wins (75.0%); Wilson 95% interval [0.566, 0.873].
Mean global turns: 25.321428571428573; mean outgoing hero damage: 27.321428571428573.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Extend validation to the historical 14-opponent suite; frozen policy and deck.

Next hypothesis: Report coverage and per-matchup weaknesses; do not retune on these seeds.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Acceptance: All 28 integration games pass across 14 opponents and both seats; excluded from final holdout statistics.
