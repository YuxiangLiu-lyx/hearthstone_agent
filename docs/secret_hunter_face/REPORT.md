# Face-priority preference follow-up

**F2 implements the requested playing style; it is not a verified win-rate improvement.** Favor face damage when the visible health reserve permits it, use the existing Secret response model for control, and retain high-value removal and combo behavior. Y1 remains the validated baseline. No new full match or terminal continuation was run because the shared 16,000-attempt budget was already exhausted.

Parent commit: `b8c652542a6297051b7575e48f6a67830851a5df`. Independent branch: `research/secret-hunter-face-priority-20261111`. The ordered 30-card Y1 deck, Krush, Misdirection and Ooze are unchanged. No engine, opponent, prior final candidate or champion pointer was changed.

## What the existing policy already does

The prior 480 development games, seeds 960000–960039, contain 4,616 own attack decisions: 3,036 face attacks (65.77%) and 1,580 attacks on minions. Thus Y1 already attacks face most often. Among minion attacks, 1,117 have a legal face alternative. Under F2's conservative public guards, 237 also target an ordinary small minion in a pressure window. These are opportunities to inspect, not proven mistakes. Being behind on board attack alone does not establish that more trading is the right policy.

Sampling uses opponent, actual turn order, original source outcome and the public trade category, with at most two observations per bucket. Those audit fields never enter the policy. Existing final seeds are excluded. F2 is evaluated on 86 selected historical trade states from 20 development seed groups; the baseline decision is reproduced in all 86. F2 changes 27 decisions, including 17 trade-to-face changes and 13 with the same attacker. All actions are legal and no policy exception occurs. This selected audit does not measure a full-game face-attack rate or win rate.

## Candidate lineage and behavior

F1 adds a conditional damage bonus to the turn evaluator and action rank, and discounts the removal reward for ordinary small minions. Its initial 90-state audit changes 33 decisions, including 23 trade-to-face decisions. It fails a concrete strategy requirement: against an enemy Knife Juggler, the Bow removal fixture becomes Hero Power. F1 is rejected and preserved.

F2 adds an explicit engine-minion guard. The extra aggression adjustment is disabled while an unsilenced recurring-value or growth engine remains, including Juggler, Hyena, Secretkeeper and Imp Master. Existing Y1 removal evaluation handles those positions. In the Bow fixture, F2 equips Bow and kills Juggler, matching Y1.

The implementation is in `face_preference.py`, integrated into `race_plan.value` and `tactics_rank.adjust`. The added coefficients are prespecified strategy preferences: 0.45 per effective face damage already dealt and a 0.25 discount on ordinary small-body removal value. They are not fitted weights or win probabilities. Ordinary bodies exclude engines, larger attack/health values, Taunt, Divine Shield, Poisonous, Windfury, Deathrattle and Stealth. The face adjustment is disabled with an opposing Secret or Taunt. The visible incoming-damage reserve is checked before response evaluation; after modeled attacks, the existing hidden-damage reserve remains. A Secret is never treated as guaranteed survival.

Guaranteed lethal still runs before heuristic search. The existing combo rewards, actual Secret trigger/order projection, unsupported-effect rejection, legal-action validation, first-action-only execution and observation replanning remain. The engine guard is deliberately broad and may suppress useful aggression in some positions; full-game validation is required before changing the recommended baseline.

## Course-engine replay: damage and Secret control

The stored public source position is development seed 960000, seat 2, sequence 14 against the sticky proxy. Y1 originally won this source game; the replay is not evidence of rescuing a loss. Our hero has 27 health, the opposing hero 23. We have a 2/2 Hyena, a 3/4 Secretkeeper and an active Explosive Trap; the opponent has a 2/3 Harvest Golem. The hand contains Deadly Shot and Unleash the Hounds, with five mana available.

The archived 28-action prefix reconstructs the exact public state in the original course engine:

- Y1 sends Secretkeeper into Golem, uses Hounds to remove the death token and grow Hyena, then attacks face and uses Hero Power. The opponent ends at 17 health: six damage dealt, seven friendly board attack, no enemy minion.
- F2 sends Secretkeeper face, uses Hounds to damage Golem and grow Hyena, then attacks face and uses Hero Power. The opponent ends at 14 health: nine damage dealt, seven friendly board attack, and the damaged Golem remains.

For one feasible visible reply, the remaining Golem attacks our hero. Explosive Trap kills it, cancels its attack and deals two more face damage. Our hero remains at 27; the opponent reaches 12 and retains the 2/1 death token. This illustrates the requested tradeoff: more face damage and contingent Secret control, with an enemy body still present. The opponent is not assumed to choose that reply, and no terminal outcome is inferred.

Full actions, public hashes and post-state measurements are in [secret-replay.json](secret-replay.json). The input and action prefix are committed, so this example can be replayed without the ignored original match logs.

## Checks and limits

Twelve nonterminal official-engine fixtures compare the full own-turn plans. Assertions preserve the tested Juggler/Bow removal, Taunt handling, danger cases, Hyena sacrifice and Houndmaster-before-attack order. The Juggler-plus-Hounds opening still plays Juggler before Hounds; after the observed random result, the candidate redirects more Hound damage to face. A separate lethal check confirms the guaranteed Krush attack without executing a terminal action. These are mechanism and strategy checks, not wins.

The F2 source passes 74 full-CLI cold/fault cases. Sixty cold calls have P95 0.234 seconds, P99 and maximum 0.326 seconds. Including injected hangs, maximum time is 1.828 seconds, with zero illegal outputs and zero calls over two seconds. The extracted artifact matches the evaluated source hash and passes official `hs-arena validate --no-game`. No new client match was run.

Two test-harness bookkeeping failures are retained: a loop variable shadowed the ledger name, then a renamed result key remained in a step counter. Both occurred after the policy assertions and evidence writes. Corrected harness execution completed successfully; its fresh reservation and both failed reservations remain charged. No candidate behavior was changed to fix these harness failures.

This follow-up adds zero full games and 2,920 short reservations. Cumulative usage is 16,000 full attempts and 45,358/80,000 short reservations; all reservations are closed. The earlier candidate and engine boundaries remain intact. See [integrity.json](integrity.json) and [archive.json](archive.json).

## Artifact and reproduction

Research ZIP: `dist/secret-hunter-krush-face-f2.zip` (43,437 bytes, 25 competition files).

SHA-256: `62b3bc975407224fe52ad0b853ad35588e2c3fc3b5ae5c033b83584b4d20eb0f`.

Source hash: `f055c456c8f315ab4c6134bc1f194cc6fc45f5e4ac2f0837fba2b963792a99f4`.

The ZIP contains code, fixed configuration and the original deck, with no training data or learned model. Its manifest lists every file hash. It is a preference research candidate pending fresh paired win-rate testing. Y1 remains the recommended validated baseline.

From the repository root and existing course environment:

```sh
.venv/bin/hs-arena validate development/secret_hunter_face/release/secret-hunter-face-f2 --no-game
.venv/bin/python -m development.secret_hunter_face.replay --name face-reproduce-example-1 --out /tmp/face-example.json
```

Use a unique ledger name for each replay; it consumes only a short reservation and never a terminal game. The original prefix and public state are committed. Runtime action traces can vary under different scheduling because search is time bounded.

Recorded commands for the existing evidence:

```sh
.venv/bin/python -m development.secret_hunter_face.audit --candidate F2
.venv/bin/python -m development.secret_hunter_face.checks --candidate development/secret_hunter_face/candidates/F2 --out docs/secret_hunter_face/f2-mechanisms.json
.venv/bin/python -m development.secret_hunter_response.runtime_checks --candidate development/secret_hunter_face/candidates/F2 --out docs/secret_hunter_face/runtime-f2.json
```

These existing reservation names cannot be reused. The full historical sampling audit requires the original ignored development observations; selected public observations and decision metadata are committed in `f2-public-decisions.jsonl` for inspection. No policy change has been inferred to increase wins. The next win-rate comparison needs a separately authorized full-game budget and newly reserved final seeds.
