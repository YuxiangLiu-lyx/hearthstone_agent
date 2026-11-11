# Evidence-driven iteration archive

Exact code/deck/config digests are in candidate_archive.json. Each run also freezes
its candidate fingerprint and opponent manifest before execution. Every candidate
uses the same 30-card multiset. This main development session designed the changes;
the run command is an experiment executor, not an autonomous model proposer.

| Candidate / parent | Hypothesis and actual change | Evidence and decision |
|---|---|---|
| A0-script / fixed-deck-generic | Balanced historical generic tempo policy plus conservative existing Hunter lethal tool, fixed requested deck | 33/56 development wins. Retain independent script baseline. No old class's win rate transfers. |
| B0-guide / fixed-deck-generic | Guide-based Secret/mulligan/Tracking/combo defaults; model chooses among legal alternatives | 43/56 script wins; real Luna 0/1 vs Greedy. B0 model audit: 14 validation bypasses and 16 missing preparations in 34 actions. A single game does not estimate strength; interface needs repair. |
| C1-coverage-interface / B0-guide | Allow deterministic attacks with Keeper/Juggler present while rejecting random summon lines; add Dire Wolf placement; hide raw candidate actions until model validation; clarify loop | 43/56 wins, no incremental outcome gain. Unsupported main states fall from 1154/2074 to 600/2061; proofs rise 64 to 70. Real Luna 1/1 on the same development seed, 20 structured selections, but 10 missing preparations and one changed validated position remain. |
| C2-public-risk / C1 | Replace top-five similar options with distinct plans; add per-action health/mana/damage risks, next-turn burn bounds and public-history tendency counts. Prefer Explosive before Freezing when immediate area damage is the point. | 43/56 script wins; no claimed gain. Changes follow C1 risky-hero-trade/coverage review and actual Secret-order tests. No standalone C2 model win-rate estimate. |
| C3-validated-loop / C2 | Shorten skill to one mandatory prepare/select/act loop; move extended guidance to playbook and summaries. No policy-weight retuning. | Fresh 280-game selection: 242 wins vs A0 196. Real six-game development spans Greedy, aggressive Hunter and frozen Priest, both seats. Consult complete C3 model audit/results rather than extrapolating preliminary wins. |
| C4-frozen / C3 | A behavioral test finds the expanded Dire Wolf solver's old optimistic bound omits the new adjacent attack gain. Add its two points to the bound. | Three ready Hounds + Wolf + power at 4 mana / enemy 7 HP changes unknown to engine-proved lethal. Five lethal families pass real-engine checks. Freeze source/ZIP before final confirmation. No broad claim that this narrow repair increases win rate. |
| C5-strict-validation / C4 | A malformed JSON diagnostic shows bool accepted as integer position; an actual C4 model ends its session before game_over. Reject bool/float IDs, extra action fields and invalid list elements. Put session lifetime instruction first. | Sixteen regression tests pass. C5-plan.json freezes this safety challenger and new seeds before testing, regardless of the win-rate direction. The original C4 confirmation continues unchanged. No scoring, deck or opponent changes. One new model seed cluster cannot support a reliable cluster interval. |

The completed six-game C3 model run won 4/6. It made 146 structured choices in 187
actions, with 31 default disagreements, two actions outside the prepared candidates,
one validation bypass, zero missing preparations and zero changed validated actions.
The remaining bypass is retained; the first four clean games were not extrapolated
to a clean full run. C4 and C5 confirmation reports contain all final outcomes.

## Feedback changed the research method

B0 initially exposed broad unsupported states and workflow deviations, not merely
losses. The diagnostic method changed to sample entire-game families into six
strata: early loss decisions, close wins, ordinary midgame, face/trade disagreement,
unsupported effects, and risky hero trades. The stored C1-training-cases.json contains
public states only; opponent labels are development metadata, never policy inputs.
One risky hero-trade signal was found; it is not labeled a proven loss cause.
These observations motivated C2's candidate consequences and public-evidence
summary instead of increasing a single aggression weight.

Terminal low health/hand is deliberately not treated as causal evidence. For a
stronger check, replay_cases.py reconstructs ten actual allowed development games
and changes enemy health or available mana within each family. Policy calls receive
only the new public view. Of 50 short branches, 30 are known-positive variants and
all are recalled; 48 returned proofs are followed to real engine wins, none left
unresolved. These cases are development diagnostics, not full games or an independent
final tactical test. Final seeds are different, and no score-directed tuning follows
confirmation. Reconstructed private data is used only by the offline engine harness.

## Negative findings retained

The broad guide bundle improved script outcomes, but the two structural tactical
iterations did not change the 56-game development win count. C1's one real model
win does not establish superiority over B0. C2 public tendencies are uncalibrated
evidence counts, not a validated archetype classifier. Full random Juggler/Hounds
search, arbitrary opponent Secrets and general hidden-information planning remain
unsupported. The strict model-stall deadline guarantee is unavailable in this skill
contract, independent of observed fast normal latency.

The first mechanism suite failed because the fixture treated the engine's integer
card_class as an enum; the adapter was fixed and all tests rerun. This is a test
harness repair, not strategy improvement. The optional generic skill-validator
requires PyYAML, absent from both existing interpreters; no installation was made.
The actual course skill validator and independent ZIP/name/dependency checks are
the authoritative package checks and pass.
