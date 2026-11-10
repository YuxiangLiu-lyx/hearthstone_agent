# v0 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 25/40 wins (62.5%); Wilson 95% interval [0.470, 0.758].
Mean global turns: 13.675; mean outgoing hero damage: 27.825.
Illegal actions: 0; timeouts: 0; early exits: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Fixed-deck strategy comparison

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Tactical audit: 4 confirmed missed-lethal turns (bounded, non-exhaustive). See docs/face_hunter/v0-turn-lethal-audit.json.
