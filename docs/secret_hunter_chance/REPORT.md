# Secret Hunter chance round: C2 passes the frozen gates

**Recommend C2 as the new separately packaged general and specialist release for these fixed local populations.** It passes the predeclared primary, family, practical old-pool and reliability gates. Original H7/D1 files, ZIPs and the historical H7 champion marker are preserved. This is not a real Astra result or an official course submission.

## M0: continuation, preservation and locked protocol

Base commit: `9ef30c2382aabc6a62ecbc2f3058de611b687a87`, previous completed M1 round. Branch: `research/secret-hunter-chance-20261111`. The tree was clean; no applicable AGENTS.md was found. Main remains at `6a7fc2475a17190268594ef2f5940b5b3a62f8f0`. The previous M1 was unpromoted: its prior final primary interval crossed zero. This round starts its experimental child from that mechanism reference, while original D1 and H7 remain frozen controls.

The D1 30-card deck is fixed; no additional opponents, self-play, models or opponent evolution. `freeze.json` fixes the six core and fourteen guardrail opponents. Integrity checks preserve 3,585 historical tracked files and 339 installed engine files. Astra proxies are hypotheses from public observations; their hidden hands, decks and programs are not the real Astra.

`seed-audit.json` scanned historical result rows and nested configuration/plan fields, finding 1,011 prior seed values. Audit used 940000–940001; development used 940100–940111, 940120–940135 and 940160–940191. The final core 941000–941039, guardrail 942000–942019 and client 943000–943001 blocks were reserved before development. These blocks are now examined and must not be called unseen in another round.

`plan.json` preserves the 8,000 full-attempt / 30,000 short-branch / four-hour experiment limits and reserves 3,200 full attempts for final work. Primary = 0.5 × Astra-family average + 0.5 × bot2-family average. Bot1 and all-six totals are separate. Specialist requires at least +1 primary point versus D1 with paired 95% lower bound >0, and no >5-point family drop. General additionally requires old-pool drop versus H7 ≤3 points overall and ≤10 points per opponent. These old-pool rules are practical screens, not statistical noninferiority tests.

## M1: observed gaps and effect semantics

Initial M1 audit: 16/24 games. Of 616 main states, 577 were supported and 432 expanded ordinary transitions; 59 exited because the highest-ranked root was not modeled. Five ordinary searches and two independent lethal searches hit a finite bound. Grouping by opponent, win/loss and actual first/second player is in `audit-m1-audit.json`. Hidden Secrets, Mana Wyrm and Sorcerer's Apprentice remained state guards. These associations do not establish loss causes.

C1 independently adds bounded public chance projection for Juggler summon triggers and Companion outcomes. Small trees are enumerated exactly; larger trees restart as fixed-count IID samples using a hash of public projected state/action, never the game seed or RNG. Mortally wounded random targets are excluded before death cleanup, shields/armor and capacity are honored, and unknown sampled/enumerated effects invalidate comparison. Actual play executes only the first current legal action and replans from the next observation.

Guaranteed lethal remains a separate deterministic search. Expected damage or sampled endpoint lethal mass never sets its guaranteed flag. No stale simulated token IDs are submitted. The chance evaluator branches by observed outcome, runs bounded deterministic continuation for each, and can consider one additional summon chance action. It clips endpoint terminal utility rather than treating one low-probability terminal as a deterministic million-point win.

Official-engine validation: **96/96 directed nonterminal cases** and **160/160 recorded development branches** matched. Four proof/deadline regressions verify probability mass, exclusion of a killed target, a 50% chance that is not a proof, metadata invariance and legal fallback. The first mechanism fixture omitted a mandatory Beast target for Houndmaster; the first metadata test compared intentionally different game IDs. Both harness issues are archived, corrected, and charged.

Additional terminal checks preserve a genuine representation difference: raw exact projection **18/24**, nonterminal **17/17**, terminal payoff **7/7**. In six won positions the engine stops before clearing dead enemy bodies, whereas the projector cleans them. The checked payoff is identical and no later actual action occurs. `terminal-checks-v2.json` retains the raw mismatches; `terminal-semantics.json` explains the narrow equivalence. Do not generalize this into complete terminal-trigger coverage. The first terminal fixture ended during setup when summoning a second Juggler against a one-health hero; that attempt is also archived and fully charged. No frozen policy was changed to address these test-only findings.

## M2: training loop, response ablation and negative learning result

| Fresh paired development block | M1 | C1 | C2 | D1 |
|---|---:|---:|---:|---:|
| 12 seeds, 144 games per arm | 123 | 122 | — | — |
| 16 seeds, 192 games per arm | 164 | 166 | 166 | — |
| Independent 32-seed retention, 384 games per arm | 325 | 327 | 328 | 319 |

C1 scores expected own-turn endpoints. Loss review showed it could override a defensive action previously checked against visible attacks. C2 applies bounded visible-attack response scoring to each evaluated chance endpoint, with supported own Secrets, and rejects the entire comparison on an unsupported response. It does not assume hidden burn/buffs/taunts are known or absent. C2 was retained for the final test. Its increment over M1 on retention is **+1.04 primary points, paired 95% [−0.26,+2.86]**; versus D1 it is +2.60 [+.52,+4.69]. Thus the chance/response increment itself is not statistically established.

C2 was frozen at commit `92daa80` before final outcomes. M1 already includes the previous Amani/Imp mechanics, proof-entry coverage and deadline work. The final C2-versus-D1 gain is the combined package; this round cannot causally allocate it among those inherited fixes and the new chance/response code. C1 and C2 differ only in response scoring and its time allocation; C1 is archived, not stacked into another learned model.

Counterfactual selection found early changed actions in 36 source games. Fourteen cases (two source losses and twelve source wins) received two alternative actions × eight shared future RNG/deck-order samples = **224 completed terminal continuations**, with no continuation errors. Existing hidden hands stayed conditional on the source game and were never passed to a policy. Action divergence need not consume identical randomness. Whole source games determine the 11 training / 3 validation split. Each record contains the observation, source action, alternative, budget, subsequent policies, samples and terminal outcomes.

An offline five-threshold gate fitted on the training cases selected the original one-point margin. Conditional mean training gain was +2.27 points, but held-out gain was **−12.50 points** over only three games. This is weak negative evidence, not a population estimate. The fitted gate was not deployed; its numerical coincidence with the pre-existing hand-set margin does not constitute a learned improvement. No bundled model weights, runtime retrieval, model calls or network. Per-case paired intervals are in `counterfactual-summary.json`. No original lost game is certified repaired, and the first changed action in a turn-4–14 scan is not necessarily the earliest causal error.

## M3: independent three-arm confirmation

40 shared seed clusters × both seats × six core opponents, 480 games per arm.

| Opponent or metric | H7 | D1 | C2 |
|---|---:|---:|---:|
| astra-board-proxy | 48/80 (60.00%) | 52/80 (65.00%) | 65/80 (81.25%) |
| astra-tempo-proxy | 68/80 (85.00%) | 68/80 (85.00%) | 69/80 (86.25%) |
| astra-sticky-proxy | 56/80 (70.00%) | 56/80 (70.00%) | 65/80 (81.25%) |
| bot2-face-proxy | 61/80 (76.25%) | 67/80 (83.75%) | 70/80 (87.50%) |
| bot2-trade-proxy | 70/80 (87.50%) | 69/80 (86.25%) | 72/80 (90.00%) |
| bot1-mage-proxy | 67/80 (83.75%) | 76/80 (95.00%) | 77/80 (96.25%) |
| All six | 370/480 (77.08%) | 388/480 (80.83%) | 418/480 (87.08%) |
| Primary Astra/bot2 macro | 76.77% | 79.17% | 85.83% |

| Paired C2 comparison | Primary change, pp [95%] |
|---|---|
| Versus D1 | +6.67 pp [+3.44, +10.00] |
| Versus H7 | +9.06 pp [+2.71, +15.42] |

| Astra matchup | Versus D1, pp [95%] | Versus H7, pp [95%] |
|---|---|---|
| astra-board-proxy | +16.25 pp [+6.25, +26.25] | +21.25 pp [+11.25, +31.25] |
| astra-tempo-proxy | +1.25 pp [-5.00, +7.50] | +1.25 pp [-8.75, +11.25] |
| astra-sticky-proxy | +11.25 pp [+5.00, +17.50] | +11.25 pp [+0.00, +22.50] |

C2's weakest core matchups are board and sticky, both 65/80 (81.25%). Astra combined is 199/240 (82.92%); bot2 combined is 142/160 (88.75%); bot1 is 77/80 (96.25%). Intervals use 10,000 paired bootstrap resamples of whole shared seed clusters, retaining both seats/all opponents. All schedules, both players' errors, actual-first fields, duplicates/missing pairs and summaries were reconciled to individual rows. Actual-first and family detail are retained in `final-results.json`. These are fixed local proxies after adaptive development selection, with few clusters and multiple descriptive subgroups. Shared seeds do not ensure identical hands/draws, especially for H7's different deck.

Old pool, 20 separate shared seeds × fourteen opponents × both seats: H7 **495/560 (88.39%)**, D1 **519/560 (92.68%)**, C2 **519/560 (92.68%)**. C2 versus H7 = +4.29 pp [-0.18, +9.11]. The largest per-opponent point drop is tempo-paladin, −2.50 points. The practical old-pool screens pass; the old-pool interval still includes zero and is not evidence of statistical superiority there.

**All predeclared promotion gates pass, including reliability. Recommend C2 for use while preserving the historical H7 marker and both older releases.** Only C2 entered final confirmation as the new candidate. No final-driven candidate change or official upload occurred.

## Coverage, timing, reliability and budget

| Final core diagnostic | D1 | C2 |
|---|---:|---:|
| Main states | 13,983 | 13,239 |
| Supported states | 10,763 | 12,665 |
| Ordinary search expanded | 8,355 | 9,832 |
| Ordinary search bounded | 224 | 433 |
| Lethal search bounded | 35 | 86 |
| Internal production nodes | 986,770 | 1,941,250 |

C2 chance search activated on 731 main states, completed 574 comparisons and changed 182 decisions. It evaluated 7,415 exact and 453 sampled distributions; these are internal planner expansions, not offline training branches. It rejected 126 comparisons for unsupported visible responses and 21 for an unmodeled baseline; 10 hit the chance deadline. Visible reply searches hit their node bounds 6,594 times. Coverage is finite and the resulting state distributions differ, so these counters do not prove causality.

| Local measurement | P50 | P95 | P99 | Max |
|---|---:|---:|---:|---:|
| Warm file/history/parse/features/decision, 100 states | 28.2 ms | 150.7 ms | 230.9 ms | 270.7 ms |
| Cold complete CLI, 60 normal/crowded states | 116.2 ms | 194.7 ms | 304.9 ms | 304.9 ms |
| Cold complete CLI, 24 largest development chance trees | 376.3 ms | 623.7 ms | 628.3 ms | 628.3 ms |

74 standard CLI/fault cases plus 24 targeted chance-tree cases passed. Forced worker hang/crash, published-action checkpoint, tiny budget, long/malformed history, malformed state and cache/sequence changes were checked. Including faults, max was 1.828 s; the separate stale-observation-while-hung test requested refresh in 1.829 s without emitting an old action. No sampled complete CLI exceeded two seconds. A unified monotonic deadline limits soft search to 1.5 s from CLI entry, and the supervisor leaves output/termination margin around 1.8 s. This is an engineering target, not hard real time. Warm imports are already initialized; game-harness policy-only timers are not full CLI times. No new model-host evaluation was performed, so model/tool/network latency is unmeasured.

Across 163,124 scheduled Python-policy decisions, zero unexpected exceptions, emergency fallbacks, illegal actions or timeouts occurred; both players were audited. The three explained fixture/test harness failures and the raw terminal representation differences above are separately archived. Terminal counterfactuals had zero errors.

Budget: **5,926/8,000 full-attempt charges**, covering 5,827 observed terminal games/fixtures: 5,592 scheduled Python matches, 224 counterfactual continuations, two clients, and nine terminal microfixtures including one fixture-setup terminal. There are 99 conservative unused full reservations. **15,478/30,000 short-branch charges**; failed/reserved work is never silently refunded. Summed experiment wall time is **22.48/240 minutes**, conservatively adding overlapping runs. Final matches/ZIP/client used 3,170 of the 3,200 protected reserve. This time excludes coding/reading/report preparation. Internal policy nodes are separate.

Remaining boundaries include Snake Trap with Juggler during opponent attacks, some deathrattle summon/draw chains, hidden enemy Secrets, Wyrm/Apprentice states, unobserved thaw and full-hand responses. Sampled chance sets are estimates; an unsampled unsupported outcome can exist. Neither a bounded response nor the absence of a found lethal proves safety from unseen cards. Final loss flags are observations, not repaired-loss labels (`final-loss-inventory.json`).

## M4: release, reproducibility and next hypothesis

Source: `development/secret_hunter_chance/candidates/C2`. SHA-256 `d167be11f4924e82b9c499a92f1a709d7de0ba426529c8ead3b235c4136a4811`.

ZIP: [`../../dist/secret-hunter-chance-c2.zip`](../../dist/secret-hunter-chance-c2.zip); SHA-256 `334937f7ed3b39e0e4342b9d8a8cdd0b4688bf1540db6fbf8190c1b0f345b033`. Size: 41,827 compressed / 109,874 unpacked bytes. One skill folder, Python and JSON/Markdown only, no training samples, logs, private evaluator state, environment or model weights. The current course assignment was fetched again and format validation passed.

Exact extracted ZIP: **48/48 matched outcomes and complete action traces** on already examined confirmation seeds. Two official no-model local client games: **56/56 exact current-sequence actions**, no relay deviations. This validates the local client path, not a real model host or Astra. Runtime wall-clock bounds can produce different legal traces on other hardware/load; the observed reproduction is not a universal determinism guarantee.

Next hypothesis: add **bounded public chance responses for Snake Trap + Juggler**, starting from the archived early/mid-game cases rejected as `unsupported_visible_response`. First isolate which rejections are actually Snake/Juggler rather than unknown draws or thaw. Test pending combat, trap order, dead attackers, board capacity, shield/enrage and deathrattle interactions against the course engine. Compare preserve-Juggler/Hyena, force a trade and hold Secret lines, then use whole-game held-out terminal continuations and new paired C2/D1 development seeds. Keep guaranteed proof separate. The current response rejection count motivates this hypothesis; it does not prove 126 recoverable positions.

Reproduce and resume instructions: [`REPRODUCE.md`](REPRODUCE.md). Pinned sources, specific script/guide adaptations and licensing are in [`SOURCES.md`](SOURCES.md). Candidate provenance and negative results are in `candidates.json`; final promotion logic is in `decision.json`.
