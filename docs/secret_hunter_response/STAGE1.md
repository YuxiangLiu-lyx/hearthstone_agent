# Stage 1: public response calibration

Frozen original Y1 won 397/480 new development games (82.71% overall, 83.23% equal-family primary) on seeds 960000–960039. All 13,574 own decisions were legal, with zero errors, fallbacks or 2-second overruns. This differs from the unavailable user-supplied dataset and is not its reproduction. Full CLI latency is tested separately.

We extracted 2,962 public response windows. Fit/calibration/test have 1,804/575/583 rows from 24/8/8 disjoint source-seed groups. The six labels co-occur: development 2,615; buffs 842; taunts 398; noncombat minion damage 551; noncombat hero damage 612; visible trades 1,031.

| Offline predictor | Test macro Brier (lower is better) | ECE, 5 bins | Own turns 2–4 Brier |
|---|---:|---:|---:|
| Class + mana | 0.13234 | 0.02859 | 0.13491 |
| + board/resources | 0.12706 | 0.03892 | 0.12724 |
| + public history | 0.12833 | 0.03452 | 0.12834 |
| Class/mana + filtered old Bigram | 0.13254 | 0.02776 | 0.13567 |
| Board/resources/history + Bigram | 0.12855 | 0.03701 | 0.12867 |

State features reduce Brier by 0.00528, paired seed-bootstrap 95% interval [-0.00831, -0.00215]. History added on top of state does not improve the point estimate. Bigram does not improve the baseline. More detailed features improve error but do not automatically improve calibration. Temperature is selected on calibration seeds only. Label-level bins, sample counts, proxy-level metrics and leave-one-proxy-out fits are in `calibration.json`; interval implementation is `predictive_analysis.py`. Only eight held-out seed groups limit certainty.

The board/resources model improves all three Astra proxy Brier scores and Mage, but worsens both Bot2 scores (face 0.1070 -> 0.1147, trade 0.1318 -> 0.1347). It is therefore not a uniformly better response model. We keep learned coefficients and old counts offline, reject external Bigram for deployment, and use public-compatible low-influence scenarios in C arms. These runtime scenarios are robust sensitivity analyses, not learned probability estimates or claims that a card is actually held.

A reproducible public-response case is the first record of `opponent_replies.jsonl`: its audit fields identify the source game and end-turn seq; `features` is the before-response input, while `public_events` and `labels` show what was actually observed. Regenerate every record with `python -m development.secret_hunter_response.data` after reproducing the source 480-game batch.

The early deficit clue is supported in these new trajectories: 46 Astra losses reached our turn 4; 42 were down at least four board attack. By actual turn order, 13/16 first-player losses and 29/30 second-player losses had that deficit. `turn4-inventory.json` includes the available hand, seat, opponent and outcome. This is an association and sampling lead, not proof that a turn-4 deficit caused defeat or that any earlier choice was wrong. Own-turn starts 2–4 are retained for complete-plan counterfactual diagnosis.
