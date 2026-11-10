# v3 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 239/400 wins (59.8%); Wilson 95% interval [0.549, 0.644].
Mean global turns: 13.68; mean outgoing hero damage: 28.045.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Deck-only challenger: replace two Highmanes with two Bluegill Warriors to test faster charge reach; 8 of 69 V3 training losses held Highmane in the last observation.

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Final decision: Rejected: +3 wins in 400 paired games; uncertainty interval includes meaningful regressions.

Next hypothesis: Retain the original deck and prioritize tactical coverage.
