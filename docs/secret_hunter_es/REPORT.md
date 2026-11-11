# Secret Hunter loss-driven ES round

**F2 remains the champion. The new C2 candidate was rejected. The 90% goal was not reached.**

On 40 fresh seed clusters (both seats), F2 won **867/1040 (83.37%)** across the 13 primary opponents; C2 won **843/1040 (81.06%)**. The paired difference is **−2.31 percentage points**, seed-cluster bootstrap 95% interval **−5.77 to +0.96**. This does not support promotion. The independent relay gate also failed once. The previous champion folder, ZIP and marker remain byte-identical.

## Frozen confirmation

The deck, installed hs_arena 0.2.2 runtime and 14-opponent manifest are unchanged. Greedy Mage is separate from the equally weighted 13-opponent primary pool. Every opponent has 80 games per arm. Shared seeds do not guarantee the same later random draws after actions diverge. These results do not estimate Mystery Bot, Astra or classmate performance.

| Group | F2 W/N (rate; Wilson 95%) | C2 W/N (rate; Wilson 95%) | Paired difference pp (seed 95%) |
|---|---:|---:|---:|
| Primary 13, equal macro | 867/1040 (83.37%; 80.98–85.51) | 843/1040 (81.06%; 78.56–83.32) | -2.31 (-5.77–0.96) |
| Official Greedy Mage | 63/80 (78.75%; 68.58–86.29) | 65/80 (81.25%; 71.34–88.29) | +2.50 (-2.50–8.75) |
| All 14, equal macro | 930/1120 (83.04%; 80.73–85.12) | 908/1120 (81.07%; 78.67–83.26) | -1.96 (-5.18–1.07) |

Single-version seed-cluster 95% intervals for the primary macro are F2 **80.19–86.35%**, C2 **77.21–84.62%**. Wilson intervals above are descriptive and ignore within-seed dependence. Old F2 10-seed results are historical and are not pooled into this new test. No new point estimate or interval supports >90% primary performance.

| Opponent | F2 wins / 80 | C2 wins / 80 | Difference pp |
|---|---:|---:|---:|
| adversarial-priest-v1 | 59 (73.75%) | 58 (72.50%) | -1.25 |
| adversarial-zoo | 61 (76.25%) | 47 (58.75%) | -17.50 |
| aggressive-hunter | 66 (82.50%) | 69 (86.25%) | +3.75 |
| aggressive-paladin | 76 (95.00%) | 71 (88.75%) | -6.25 |
| control-mage | 61 (76.25%) | 57 (71.25%) | -5.00 |
| control-priest | 71 (88.75%) | 70 (87.50%) | -1.25 |
| historical-mage | 58 (72.50%) | 58 (72.50%) | +0.00 |
| official-mage | 63 (78.75%) | 65 (81.25%) | +2.50 |
| search-paladin | 58 (72.50%) | 53 (66.25%) | -6.25 |
| search-shaman | 70 (87.50%) | 74 (92.50%) | +5.00 |
| tempo-paladin | 60 (75.00%) | 56 (70.00%) | -5.00 |
| tempo-warlock | 78 (97.50%) | 78 (97.50%) | +0.00 |
| value-priest | 72 (90.00%) | 72 (90.00%) | +0.00 |
| value-warlock | 77 (96.25%) | 80 (100.00%) | +3.75 |

Per-opponent paired intervals and discordant counts are in `final-paired.json`; these exploratory subgroup comparisons are not multiplicity-adjusted. Zoo is the clearest regression (61 to 47 wins); search Paladin, tempo Paladin and control Mage also weaken. Gains on Shaman, Hunter and value Warlock do not offset those losses. Primary discordant pairs are 89 F2-only wins and 65 C2-only wins.

## Implemented changes and paper adaptation

Historical F2 losses exposed a missing Snake token in both exact projection and Beast identification. The latter undervalued Kill Command. C1 adds Snake coverage, exact Secret deployment/Secretkeeper growth, Houndmaster, Ooze, first-Juggler deployment and single-target Deadly Shot. C2 uses 21 interpretable end-turn coefficients. C3 adds a soft visible attack-exposure estimate. D1 isolates only the Snake correction. Unknown random triggers and hidden enemy Secrets remain excluded from exact proofs.

The implemented ES uses two parents, four offspring, three generations, 21 normalized real-valued genes with separate evolving sigmas, plus categorical width/depth/node mutations. Each generation re-evaluates parents and offspring on a new shared seed block; elitist selection retains the best two. This follows the methodological ideas in [García-Sánchez et al.](https://arxiv.org/html/2410.19681v1), rather than claiming to reproduce its coevolution, decklists or competition result. We use bounded multiplicative log-normal sigma updates; this explicitly differs from the additive expression printed in equation 9 of the HTML. Fixed opponents replace prohibited self-play. See `SOURCES.md` and `evolution.json`.

| Generation | Parent/offspring primary wins (each /104) | Retained |
|---|---|---|
| 1 | C2: 82, C3: 81, E11: 82, E12: 80, E13: 81, E14: 79 | C2, E11 |
| 2 | C2: 90, E11: 78, E21: 84, E22: 80, E23: 84, E24: 83 | C2, E21 |
| 3 | C2: 87, E21: 81, E31: 83, E32: 76, E33: 84, E34: 80 | C2, E33 |

C2 survived unchanged in all three generations. E33 was the best evolved finalist in generation 3, but lost to the untrained C2 parent on independent validation. No gain is attributed to evolved weights. The training budget is much smaller than the paper’s 100-generation setting. Repeated development selection has substantial bias; final confirmation controls the promotion decision.

## Initial paired screen

All five screen arms used the same four development seeds (104 primary and 8
Greedy games per arm). F2/D1/C3 each won 92 primary games; C1/C2 each won 91.
Greedy wins were 5 for F2/D1 and 6 for C1/C2/C3. No screen result established an
improvement. These tiny, repeatedly inspected blocks are selection data only.

## Independent validation / ablation

| Arm | Primary wins /208 | Greedy wins /16 | Interpretation |
|---|---:|---:|---|
| B0 | 154 (74.04%) | 12 | Frozen F2 |
| D1 | 158 (75.96%) | 12 | Snake-only correction |
| C1 | 158 (75.96%) | 12 | Broader exact coverage and Secret potential |
| C2 | 159 (76.44%) | 12 | Untrained 21-feature evaluator |
| E33 | 157 (75.48%) | 12 | Evolved feature/search parameters |

C2 was selected before final seeds were opened. Its validation lead was only one game over C1/D1 and five over F2; the fresh confirmation did not replicate that apparent gain. D1 is not retroactively promoted after seeing C2 fail: it lacks its own fresh final confirmation.

## Failure evidence and reliability

Mechanism checks passed after the Snake fix: 13 test methods, 805/805 one-step comparisons from historical losses, plus 3 constructed real-engine lethal wins. The original failing Snake/Kill Command test is preserved. Offline diagnosis saved 34 early-divergence cases with 68 legal current-turn branches across the historical and final-regression audits. All endpoints are nonterminal; no counterfactual full-game win is claimed. `DIAGNOSTICS.md` records uncertainty and examples.

The new static evaluation sometimes chooses two face damage instead of Explosive Trap against multiple fragile attackers. Expanded deterministic coverage also permits comparisons that omit random Juggler continuations. A better Secret/opponent-response model and safeguards around partially modelled combos are more promising next hypotheses than treating wider coverage as sufficient. Smaller/staged ES mutations and an independently confirmed minimal Snake fix remain untested follow-ups.

| Measurement | F2 final | C2 final |
|---|---:|---:|
| Pure policy P50 ms | 0.26 | 0.47 |
| Pure policy P95 ms | 18.89 | 32.23 |
| Pure policy P99 ms | 76.15 | 110.24 |
| Pure policy maximum ms | 284.97 | 290.48 |

Across **185,260** Python decisions: **0 policy exceptions, 0 emergency fallbacks, 0 >2-second decisions**. All completed matches have zero own illegal actions, timeouts and forfeits. C2 node P95/P99/max: 360/1216/1950. C2 exact-lethal coverage rejects 1801/33333 main states versus F2 5601/34077; broader coverage did not translate into higher win rate.

Supervised cold CLI P50/P95/P99/max: 75.71/122.64/262.47/262.78 ms. Including forced hangs/crashes, maximum 1.824 s, 0 over 2 s, 0 illegal fallback actions. Cold component costs are in `component-profile.json`. These are measured bounds, not a hard-real-time proof.

The exact research ZIP reproduced **56/56 outcomes and 56/56 action traces**. Two official client games passed with 73/73 exact actions. Two Luna-medium host games won, but **61/62** actual actions had matching script output: at game `386be7bf18554160`, seq 5, the host directly sent `end_turn` without running the script. Even though this was the only non-concede action, it violates the all-program relay requirement. This failure is retained, not counted as an exact-relay pass. Host game durations were 75.806 and 296.361 s; program latency is separate from host/tool latency.

The separate relay-fix ZIP changes only `SKILL.md` to explicitly prohibit this shortcut. Source/config bytes are otherwise identical; two repeated official client games matched all 73 prior script actions. **The revised playbook has not been model-host retested**, because the two-game allowance is exhausted. Neither research ZIP is promoted. F2’s previous successful relay evidence is historical, not a guarantee against this newly observed host behavior.

## Artifacts, budget and scope

Completed **5998/6000** full games: 5,992 pure Python, 4 official client, 2 official Luna relay. Charged **2246/20000** short experimental cases, including conservative supplements; internal runtime search nodes are reported separately. Elapsed wall time at archival: 29.9 minutes (four-hour limit). The final pair plus reproduction used 2,296 games, exceeding the 25% reserve requirement. The remaining two games cannot support another balanced full-pool confirmation. No extra host smoke is allowed this round.

Verified 477 protected historical files, 339 runtime files, 14 opponents, and 185,260 public policy inputs. The fixed deck SHA-256 is `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`. Research ZIP: `dist/secret-hunter-es.zip`, 31,568 bytes compressed / 81,434 unpacked; SHA-256 `4f9481653297c82fa1b2feb80f0c8e82d4e77e6c7ea327315e754b3b9d3d876b`. Instruction-only revision: `dist/secret-hunter-es-relay-fix.zip`, SHA-256 `0f479e27644dbfe04ee99cb127956f9c4670aab6261d7e72cd5ecc96da6189d9`. Both are below 10 MB and pass official static validation.

Recommended artifact remains `dist/secret-hunter-program.zip` with the original `SECRET_HUNTER_CHAMPION.json`. Source/candidates, budget, hypotheses, hashes, splits and commands are archived alongside this report. See `REPRODUCE.md`. No formal submission, remote push, opponent modification, engine modification, cross-game policy memory or extra installed dependency was used.

Using retained F2's new Greedy point estimate (78.75%) in a simple independent six-game binomial approximation gives 2.60/3 expected Bot-1 win-bonus points, or 7.60/8 conditional on completing all six games. This noisy plug-in estimate is not an earned grade and ignores dependence. Mystery Bot, Astra and ladder scores remain unknown.
