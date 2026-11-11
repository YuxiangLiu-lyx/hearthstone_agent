# Copied generic policy and new theft deck; missing hero flag compatibility repair only experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 114/240 wins (47.5%); Wilson 95% interval [0.413, 0.538].
Mean global turns: 22.4625; mean outgoing hero damage: 20.770833333333332.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: Copied generic policy and new theft deck; missing hero flag compatibility repair only

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Retained policy/deck ablation. No promotion of the copied generic policy with the new deck.
