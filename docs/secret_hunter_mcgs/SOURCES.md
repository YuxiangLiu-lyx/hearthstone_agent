# Source and implementation audit

This is an independent Python implementation by this repository, informed by Jean Seong Bjorn Choe and Jong-Kook Kim's 2019 MCGS work. No external C# code, SabberStone engine, checkpoint, binary, or learned response weights enter the candidate. The original ordered Krush deck remains fixed.

## Primary algorithm

The [official competition archive](https://hearthstoneai.github.io/botdownloads.html) identifies Jean Seong Bjorn Choe as the 2019 user-created-deck winner. The [results slides](https://hearthstoneai.github.io/files/slides/2019-Results-Hearthstone-AI-Competition.pdf) identify Odd Paladin. The reference [source ZIP](https://hearthstoneai.github.io/files/bots/UserCreatedDeckPlaying2019/2019_UCDP_MCGS.zip) has SHA-256 `f00a54f310a8f868deb59964c17e71357d67ecfcedba01c0245053dcc5aa920a`. It contains 31 C# files and no standalone license grant. The archive invites study and author attribution; this is not treated as a permissive redistribution license. The archive is not bundled.

The [paper](https://ieee-cog.org/2019/papers/paper_257.pdf), DOI 10.1109/CIG.2019.8848034, was read in sections III-B–F, Algorithm 1, IV, V-A–D and Tables II/III. Its graph, confidence-bound and chance-sampling mechanisms inform the implementation. Its Hunter experiments use Deathrattle Hunter, and some experiments assume an opponent deck. Neither that deck nor privileged opponent knowledge transfers here. Results in this repository are new course-engine measurements.

| Reference file/function or passage inspected | Local realization | Executed evidence and adaptation |
| --- | --- | --- |
| `Agent.cs`, `AgentUtils.cs`, `src/MCGS.cs`: search and act | `adapter.py`, `mcgs_search.search` | Course engine own remainder, full opponent turn, own next turn; one legal action returned |
| `src/Node.Expand.cs`, `src/Node.cs`, `src/Edge.cs`: expansion, visits, sampled children | `mcgs_graph.Graph`, `Chance`, `mcgs_search.search` | Diamond graph, real commuting attacks, empirical 2:1 sampling over 12,000 draws |
| `src/Algorithms/UCD.cs`, Eq. (3), Algorithm 1 | `Edge.value`, `Graph.backup` | Separate edge visits and node totals; bounded off-path updates, UCT ablation |
| `src/Abstraction/StateAbstraction.cs`, `ActionAbstraction.cs` | `key`, `world_key`, legal atomic action dictionaries | Retain entity identities, order, attacks, choices, secrets, mana and public revealed history; conservative equality |
| `DoubleProgressiveWidening.cs`, `DampedSamping.cs`, Eq. (4) | `Chance.width` | Fixed width / DPW / damped sampling; exact rounding tests; 400-transition-cap ablations |
| `UniformRandomRollout` and filter implementation | `rollout_action`, `rank` | Filtered vs Y1-guided rollout; friendly Mortal Coil on Amani retained |
| III-F, `SearchConfig.cs`, `Agent.cs` | Supervised Y1 CLI and 1.3-second search allowance | Cold CLI includes initialization; offline reference receives 20 seconds |

Two discrepancies matter. The task describes Eq. (4) as floor, but the actual rendered formula is **ceil**: see [the formula crop](equation4.png). The paper takes an overall ceiling after damping; source DPW first takes a ceiling, followed by damping and C# default midpoint-to-even rounding. For an undamped value 4.1 and divisor 2, those yield 3 and 2. The default follows source order; `paper` and `floor_ablation` are separately tested. Historical matches all used the source default. The original unused `paper` option was incorrectly implemented as floor and corrected before the reported transition ablation rerun. Paper III-F decreases the time allowance; public code uses first 15 seconds and later 10 seconds. Neither fits this task's 2-second CLI envelope.

This implementation is deliberately conservative about state merging. It shares a DAG **within one search**. It rebuilds for a changed observation; it does not persist and relocate the graph across CLI invocations. The inherited supervisor caches only an identical validated observation. This leaves performance potential unrealized. Incomplete search horizons are discarded. A sampled utility is not a guaranteed lethal or a calibrated win probability.

## Offline evolution

[García-Sánchez et al., arXiv:2410.19681v1](https://arxiv.org/html/2410.19681v1), section 3.2, Algorithm 2 and section 4.2, informed joint parent/offspring evaluation on the same fresh batch. `train.propose`, `reserve` and `analyze` implement this with fixed existing opponents, not co-evolved opponent decks. Fixed original-deck legality is checked at construction and submission.

[DGM, arXiv:2505.22954v1](https://arxiv.org/html/2505.22954v1), section 3 and appendices A.2–A.4, informed the parent archive, failure-driven code revisions and branching from non-latest parents. The actual Bow, latent-particle and entity-identity revisions are recorded in lineage files and measured games. The unattended runner explores preimplemented configurations cyclically; it does not implement DGM's exact parent sampling distribution or generate new source code itself.

Noninteractive Codex CLI was inspected using `--version`, `exec --help`, and `login status`. All failed with ENOENT for `/opt/homebrew/lib/node_modules/@openai/codex/vendor/aarch64-apple-darwin/codex/codex`. No external proposal agent was launched. The optional platform capability was checked against [OpenAI's official Codex platform documentation](https://developers.openai.com/blog/codex-as-a-platform). The Python configuration loop continues independently and leaves the next code proposal in its checkpoint.

## Course, public data and installation

The [HW2 assignment](https://bu-agenticai-class-fall26.vercel.app/materials/assignments/hw2.md) was fetched and read locally (SHA-256 in `source-fetch.json`). The online package uses Python and installed `hs_arena` 0.2.2, legal observations and public history. It uses no network, external model, private evaluator identity, seed or actual opponent hand. All 339 audited installed course files match the previous frozen hashes. A 667,399-byte compressed cache contains English metadata for all 9,344 installed card definitions, not model weights. Exact cache/original metadata digest equality is checked by `audit.py`; effects still come from the installed course engine. No installer or bundled engine is included.

The requested original training ZIP was not found. Existing Y1 public-response data (2,962 rows, 480 games, 40 source-seed groups) and its README/manifest were reused without refitting on the submitted games. The existing external Bigram feature ablation is an offline comparison only. C2's 14 submitted games and all their derived states are development data; their dual-Arcane-Shot deck differs from the fixed deck here. Hidden hypotheses used for labels are never policy inputs. Full trajectories may contain the opponent's simulated own perspective for auditing; those files are offline only.

## Storage recovery

During the first detached run, macOS cloud placeholders returned empty bytes despite nonzero file sizes and caused Git SIGBUS. Apple's [dataless-file note](https://developer.apple.com/documentation/technotes/tn3150-getting-ready-for-data-less-files.md) describes these placeholders. `brctl download`, Foundation downloading and POSIX materialization requests did not recover all bytes. A fresh checkout outside Documents, exact candidate reconstruction and course-wheel extraction restored every candidate fingerprint and all audited engine hashes. Missing historical trace files are explicitly listed in `storage-recovery.json`; no missing observations were invented. The failed batch remains charged and excluded from strategy selection.
