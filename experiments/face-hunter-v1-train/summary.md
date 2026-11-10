# v1 experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 91/160 wins (56.9%); Wilson 95% interval [0.491, 0.643].
Mean global turns: 13.3; mean outgoing hero damage: 27.20625.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Fixed-deck strategy comparison

Next hypothesis: Inspect measured failure categories before choosing one further change.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Tactical audit: 1 confirmed missed-lethal turns (bounded, non-exhaustive). See docs/face_hunter/v1-turn-lethal-audit.json.
