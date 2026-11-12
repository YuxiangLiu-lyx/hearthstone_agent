# Original Krush Secret Hunter: MCGS research iteration

**Recommendation: retain Y1.** The implementation is executable and has changed real decisions, but the completed pilot does not establish a win-rate improvement. The detached experiment continues; final confirmation is unopened at this report's initial snapshot. The research ZIP is not a promoted submission. Nothing was submitted to the course.

## Frozen scope and provenance

The initial workspace HEAD was `b160f41b18ec698a4eab55a4160dab2adaae74d8`. Research started from the completed face-validation checkpoint `5afec0f074e56145723f544e23aba062f4be14e3` on `research/secret-hunter-mcgs-20261112`. The requested `8b9a1f30ca16a3587b04f15472d855e14c26a8ce` is an ancestor. `ca7c8d2` and R1 were unavailable. Existing user work and the submission ZIP were preserved. After a cloud-file failure, the active checkout moved to `/Users/liuyuxiang/.codex/worktrees/hearthstone-mcgs-20261112` with the same base and exact candidate fingerprints.

All candidates retain the **ordered** 30-card Y1 deck, SHA-256 `54c475d2f72ff3a36ec5d47d0e34bf33625eb1b20c75f213e171c73719cf61f4`, including EX1_543, EX1_533 and EX1_066. Deck multiset, order, course legality and actual submission output are checked. The reused response-project Y1 is the frozen policy baseline; the original DGM Y1 deck is the authority. The six core and fourteen guard opponents, scoring, installed engine and old results are unchanged.

Submission 2 is **C2, a different deck with two Arcane Shots**: official 8/14, comprising Bot1 5/6, Bot2 2/4 and Astra 1/4. All fourteen games are development data. Its public states, legal actions, historical events and next-turn response labels are in `submission2-public.zip`. Later reveals are labels or explicit offline hypotheses, not online features. No local proxy win rate is presented as an official Astra/Bot2 result.

## Completed paired full games

The initial pilot and structural revisions completed 336 games. Of these, the first 48 are diagnostic only because the initial simulator adapter gave Bow extra durability. The later four-version full-CLI batch completed another 48 games. A separate 96-attempt batch was aborted after cloud placeholders caused a read/fingerprint failure; all 96 remain charged and excluded from strategy selection. Counts in the live checkpoint increase as training runs.

| Batch / execution | Whole seed groups | Y1 | UCT | UCD fixed | UCD DPW |
| --- | ---: | ---: | ---: | ---: | ---: |
| pilot-100, warm Python, M3 | 2 | 16/24 | 19/24 | 18/24 | 17/24 |
| pilot-101, warm Python, M3 | 2 new | 22/24 | — | — | 21/24 |
| pilot-102, warm Python | 4 new | 28/48 | — | — | M3 29/48; M5 27/48 |
| cli-103, full CLI, M5 | 1 new | 9/12 | 9/12 | 9/12 | 7/12 |

M3 DPW and Y1 tie at 38/48 across the first two corrected batches. On pilot-102, M5 DPW's Astra/Bot2 equally weighted metric is **52.08% versus Y1 59.38%, −7.29 percentage points**, with a whole-seed paired 95% bootstrap interval **[−16.67, +2.08] pp**. There are five Y1-only wins and three M5-only wins among primary-pool pairs. Four seed groups are too few for a firm estimate. M3's known latent-particle defect also prevents treating its favorable samples as release evidence.

| pilot-102 opponent | Y1 | M3 DPW | M5 DPW |
| --- | ---: | ---: | ---: |
| Astra board | 4/8 | 5/8 | 5/8 |
| Astra sticky | 2/8 | 4/8 | 2/8 |
| Astra tempo | 6/8 | 4/8 | 6/8 |
| Bot1 mage | 5/8 | 7/8 | 6/8 |
| Bot2 face | 7/8 | 4/8 | 4/8 |
| Bot2 trade | 4/8 | 5/8 | 4/8 |
| Actual first | 16/24 | 15/24 | 16/24 |
| Actual second | 12/24 | 14/24 | 11/24 |

The full-CLI batch is more representative of deployment than warm Python calls: initialization leaves fewer search transitions. Its primary metric is Y1 75%, UCT/fixed 70.83%, DPW 54.17%. With **one seed group**, a bootstrap interval degenerates and is not inferential evidence; only the descriptive rates are meaningful. No current-run Greedy or fourteen-opponent guard result has been measured yet. Those are reserved for final validation, not borrowed from the previous face-policy study. `pilot-results.json` contains all opponent, family and actual-first/second tables and paired comparisons.

## Public response calibration

The requested training ZIP was absent. We reused the documented 480-game Y1 response data: **2,962 rows**, split by complete source seed into train 24 groups/1,804 rows, calibration 8/575 and test 8/583. Both seats and related states remain together. The previous local held-out results and new frozen-model transfer check are:

| Response model | Local test Brier | Local ECE | C2 transfer Brier | C2 transfer ECE |
| --- | ---: | ---: | ---: | ---: |
| Class + turn/mana | .13234 | .02859 | .14383 | .06784 |
| Public board/resources | .12706 | .03892 | .14298 | .09288 |
| Public history | .12833 | .03452 | .14549 | .08603 |
| External co-occurrence prior | .13254 | — | .14388 | .06944 |
| History + external prior | .12855 | — | .14603 | .09552 |

The C2 check has **90 response windows in 14 game groups**, without refitting on those games. It does not support deploying the history or old co-occurrence prior. Per-event sample sizes, class/agent slices and calibration bins are in `response-transfer.json`. Labels are multi-label public events; failure to play a card is not evidence that the card was absent. No game ID, source seed, private evaluator name, hidden hand, future event or winner is a response feature.

Online MCGS currently uses a broad class/copy-count-compatible public-history prior, not a calibrated posterior over archetypes. Hand size, legal mana use and seven board slots constrain actual engine actions. A visible-only scenario remains an offline ablation. This model limitation is central to the negative result; it is not described as solved calibration.

## Replayed complete plans and terminal labels

The four requested C2 positions were reconstructed from public observations and translated into legal original-deck engine states. Arcane Shot is replaced by missing original-deck cards while preserving the complete own-card multiset and distinct entity identities. The translations are synthetic experiments, not claims that the original C2 replay used Krush or Misdirection. Common public-compatible hypotheses and paired future RNG seeds are used per plan; decisions after randomness use the resulting view. Selection samples 0–3 and validation samples 100–107 are disjoint. All **240** corrected continuations reached a terminal outcome.

| Case / hypothesis | Validation terminal wins | Interpretation |
| --- | --- | --- |
| Bot2-03, turn 3, continued beast development | Y1 1/8; face 3/8; wolf then face 4/8; all trade 2/8 | Killing the aura source is valuable under this hypothesis |
| Same board, visible responses only | All four plans 8/8 | Hidden development assumptions change the ranking |
| Bot2-03, turn 6, Tracking at five mana | Y1 0/8; Companion 0/8; Highmane 0/8 | A legal alternative is not necessarily a rescue |
| Astra-02, turn 6, next draw is Mortal Coil | Y1 7/8; face 6/8; forced Amani trade 2/8 | Excessive trading can damage a winning continuation |
| Same board, no Coil | Y1 3/8; face 2/8; forced trade 2/8 | Response uncertainty remains important |
| Bot1-02, translated Coin opening | All three plans 7/8 | No useful signal in this small sample |

Immediate survival, next own/enemy attack, sample counts and terminal coverage are recorded in `continuations.json`; complete sample records are in the data ZIP. For the beast case, killing the wolf lowers mean next-turn enemy attack from **8.25 to 4.75**, while immediate survival is 8/8 for both plans. The selection samples prefer wolf-first 2/4 over Y1 1/4; its validation result is therefore not selected using those eight validation samples.

Two complete engine trajectories are in `run/evidence` inside the data ZIP:

* `wolf-102.json`: Y1 sends two Hounds face, then faces Hyena/Wolf development and eventually loses in 61 actions. The alternative sends one Hound into the existing Timber Wolf, the other face, adapts to the actual response and wins in 72 actions. Every action, current acting-player view and public engine event is retained through terminal. This is a positive example found by broader enumerated-plan/terminal evaluation. **Fast and 20-second MCGS both still chose face**, so the current search did not discover the better ranking.
* `amani-100.json`: Y1 plays Highmane and sends three Hounds face, eventually winning in 25 actions. Forced Amani trading consumes all three Hounds before Highmane and loses in 33 actions. The opponent rollout is fallible: in the first branch it uses Coil on Amani but attacks Highmane rather than taking the available hero lethal. This example exposes rollout bias; it does not prove that leaving Amani is safe. A separate exact mechanism test reproduces the nine-damage friendly-Coil lethal.

A third file, `mcgs-harmed-win.json`, is an **actual full-CLI paired game**, seed 10000600, Astra-board proxy, seat 1. The first divergence is on own turn 3 at zero mana: Y1 sends Hounds face; M5 DPW sends a Hound into Leper Gnome. The new decision's two leading root estimates have only two visits each (utility .651 versus baseline .552). Y1 wins the complete game; M5 loses. Both full student-view trajectories are retained. This is a diagnostic association, not proof that a single exchange caused the eventual result.

A 20-second reference search changes Tracking's choice to immediate Companion but all held-out continuations still lose. Terminal rollout gets only 43 completed horizons across four 400-transition fixtures versus DPW's 222 cutoff horizons. More offline search can assess plans that the fast budget cannot reliably rank; simply adding more branches does not fix a biased response model or cutoff value.

## Search, semantics and ablations

`mcgs_world` reconstructs hypothetical worlds using public information; real course code produces transitions. `mcgs_graph` implements decision/atomic edges, shared DAG statistics, bounded off-path UCD backup, empirical chance frequencies, fixed-width sampling, DPW and damping. `mcgs_search` preserves all legal root actions and Y1's fallback, then evaluates own remainder → full opponent turn → own next turn. Opponent decisions see only the opponent's simulated view. Latent payloads with the same public successor remain separate particles. An incomplete horizon is discarded. Guaranteed lethal remains Y1's proof-based branch; sampled utility never sets it.

| Four fixtures; cap 400 transitions each | Actual transitions | Unique states | Transposition hits | Chance samples | Complete horizons | Cross-turn | Terminal | Root changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| UCT | 1600 | 476 | 0 | 316 | 195 | 195 | 0 | 0 |
| UCD fixed | 1600 | 558 | 15 | 330 | 192 | 192 | 0 | 0 |
| UCD DPW | 1600 | 655 | 14 | 265 | 222 | 222 | 0 | 1 |
| No opponent plays | 1600 | 808 | 23 | 346 | 315 | 315 | 6 | 0 |
| Own turn only | 1094 | 936 | 15 | 660 | 2501 | 0 | 0 | 1 |
| Filtered rollout | 1600 | 839 | 16 | 320 | 266 | 266 | 3 | 0 |
| Terminal rollout | 1600 | 126 | 0 | 45 | 43 | 43 | 39 | 1 |

The own-turn-only variant hit the separate 20-second wall ceiling on cached branches, so its actual transitions are lower. These are matched **caps**, with actual work disclosed, not equal realized work for that row. The earlier horizon-one implementation accidentally advanced the opponent and was corrected before this table was rerun. Its regression test now requires zero opponent actions. Root-change counts here compare with the fixture's cheap ranked anchor; full-game adapters compare with the complete frozen Y1 policy. They must not be conflated.

Full-CLI telemetry also confirms that search changed real actions: UCT changed 26 of 193 invoked searches, fixed UCD 28/191, and DPW 39/207. Their completed cross-turn samples total 3,272 / 3,061 / 3,834; transposition hits total 0 / 39 / 81. All twelve student logs per arm are present and reconstruction failures were zero in this small CLI batch. `search-coverage.json` records states, chance samples, coverage and missing historical log counts. More graph reuse and more root changes did not translate into better wins here.

Twelve mechanism tests pass, including UCD diamond/off-path counts, real commuting attacks, preserved position and mana distinctions, weighted chance sampling, latent particle retention, aura reconstruction, Tracking choice/discard, friendly Coil/Amani lethal, secret ordering/Bow, Misdirection, Juggler/Hounds, random-source independence and the nine-mana Krush route after clearing taunt. Companion sampling is checked against its exact three-way distribution. Unsupported enemy secrets, ambiguous Windfury attack counts and unrepresented deathrattles reject reconstruction and retain Y1. Graph reuse across changed CLI observations is **not implemented**; only within-search sharing and exact-observation supervisor caching exist.

## Actual revisions and retained parents

| Child | Parent / evidence | Change and decision |
| --- | --- | --- |
| M3 UCT/fixed/DPW | M0/M1/M2; Bow test gave 6/5 instead of 4/3 durability | Reconstruct weapon damage from observed durability; retain original 48-game diagnostic, cancel unlaunched tasks, reevaluate on fresh seeds |
| M4 particles | M3 DPW; equal-public-state test kept only Coil | Retain all latent payloads and sample them with empirical frequency; preserve choice/reveal identity; reject incomplete horizons |
| M5 family | M4 / M3 parents; restored entity IDs aliased discarded setup entities | Disjoint setup ID namespace; correct Tracking translation; full-game result does not justify promotion |
| M6 confidence | M5 UCT; actual full-CLI harmed win with two visits per alternative | Require six visits for both compared root actions and increase override margin .06 → .12; new paired batch `confidence-104` |
| G variants | Non-latest archived M5/M6/G parents | Automatically compare preimplemented rollout, response, horizon, graph and budget settings against parent and Y1 on the same fresh block |

The strongest current diagnosis is **response/value ranking with too little evidence**, alongside repaired transition defects. The wolf action was generated but misranked; the Tracking alternative was legal but insufficient; the harmed win overrides a strong anchor on two samples. We have not measured an exhaustive population-wide attribution among missing plans, wrong valuation and wrong simulation, so no unsupported prevalence claim is made. M6 is an experiment, not a validated improvement. The completed result follows.

## Latency, reliability and recovery

| Complete CLI measurements | Decisions/probes | P95 | P99 | Maximum |
| --- | ---: | ---: | ---: | ---: |
| cli-103 Y1 | 323 | .189 s | .389 s | .539 s |
| cli-103 M5 UCT | 347 | 1.560 s | 1.580 s | 1.612 s |
| cli-103 M5 fixed | 351 | 1.566 s | 1.592 s | 1.611 s |
| cli-103 M5 DPW | 341 | 1.556 s | 1.574 s | 1.590 s |
| M5 UCT isolated cold starts | 12 | 1.480 s | 1.480 s | 1.480 s |
| M5 UCT cold + concurrent + injected faults | 28 | 1.839 s | 1.840 s | 1.840 s |

All cli-103 arms have zero illegal actions, timeouts, forfeits, policy errors, ordinary fallbacks and public-input violations. The separate 28-probe suite includes four concurrent calls, crash, hung worker, action published before a hang, four stale-observation repetitions each for Y1 and candidate, and game-over. Injected fault fallback is expected and separated from ordinary fallback. Zero invalid outputs and zero calls above two seconds were observed. The earlier four-arm 76-probe suite and M5 DPW 28-probe suites are retained. These are finite machine-specific measurements, not a hard real-time proof.

The unmodified engine's initialization cost was about 3.21 seconds; equivalent cached metadata reduces it to .626 seconds. Exact card metadata digests match and all 339 installed course files match their frozen audit. The package still loads course effect code. Limits include cold initialization and supervisor overhead.

SIGTERM draining and resume were exercised twice. The later check preserves 528 completed tasks, drains four inflight tasks to 532, and finds **zero duplicate attempt keys**. The lock rejects a second writer with `Another writer owns this run.` Atomic result files are reconciled after restart; incomplete charged attempts remain in the ledger. Abrupt process-tree kill recovery was not separately exercised. The cloud incident leaves an explicit list of unavailable historical trace files; task results in SQLite and exact candidate snapshots were preserved. New full-CLI traces and complete positive/negative examples are present in the stable checkout.

## Ongoing run and release gate

The detached process uses four workers on a 14-logical-CPU machine. The unchanged total caps are **8 effective training hours, 12,000 full-game attempts and 60,000 continuation attempts**; pilot and failed attempts count. A conservative 120 seconds was added for previously untimed analysis overhead; subsequent analyses are explicitly timed. `launch.json`, `checkpoint.json` and `training.log` give current process and progress. The runner already started its next batch automatically after cli-103, and resumed without replaying completed tasks.

Reserved final blocks are 10100000–10100079 for six-core-opponent paired comparison (1,920 games) and 10200000–10200019 for fourteen-opponent guard comparison (1,120 games). Selection uses 10050000 onward. Earlier inherited seed values are below 10,000,000. Selection and final matches now execute the full supervised CLI per action. Once the selected challenger is frozen and final seeds opened, that challenger is not tuned. The runner stops when a cap is exhausted; an incomplete final is not a pass.

Promotion requires primary gain at least +1 pp, complete-seed paired 95% interval strictly above zero, no family regression beyond 2.5 pp, no old-pool regression beyond 2 pp, and reliability gates. The research goal remains +3 pp. Until those conditions are actually measured and met, **Y1 remains the recommended release**. The 721,502-byte M5 UCT research ZIP passes loader, ordered deck, source fingerprint and actual deck-submission checks. It carries no offline labels, external model, C# source or bundled engine.

## Completed confidence revision

`confidence-104` completed **144 warm-Python games on four fresh seed groups**: Y1 **45/48**, M5 UCT **44/48**, M6 **45/48**. M5 UCT has primary gain +2.08 pp with whole-seed 95% interval [−4.17, +8.33] pp; its lower total comes from the other family. M6 exactly matches Y1 on all 40 Astra/Bot2 pairs: primary 93.75% for both, no primary win-to-loss or loss-to-win pairs. The empirical interval [0, 0] reflects this small all-tied sample and does not prove population equivalence. No reliability errors occurred. The seed block is easier for all three policies than pilot-102; rates must not be compared across blocks as gains.

The confidence guard reduced changed root actions from 135/798 searches to 8/858. It is retained as a conservative parent, not promoted. `confidence-result.json` contains the complete family/opponent/seat comparisons. The strongest bottleneck remains making reliable useful overrides, rather than producing additional overrides.
