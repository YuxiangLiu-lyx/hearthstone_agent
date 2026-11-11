# generic experiment

Transport: official Python runner, no model. Runtime: hs-arena 0.2.2.

Results: 159/300 wins (53.0%); Wilson 95% interval [0.473, 0.586].
Mean global turns: 22.576666666666668; mean outgoing hero damage: 22.473333333333333.
Illegal actions: 0; timeouts: 0; early exits: 0.

Policy exceptions: 0; CLI fallbacks: 0.

Small samples are smoke tests, not reliable estimates of long-run competitive strength.

Change: generic

Next hypothesis: Review paired results and concrete failures before further changes.

See config.json for exact seeds, deck, code fingerprint and conditions; metrics.json for per-game results.

Decision: Retained policy/deck ablation. No promotion of the copied generic policy with the new deck.
