# Capability evidence and limits

These are different evidence types, not one combined skill score. Training families
were split from final complete-game confirmation by game and seed. None of the
short exercises enter a full-game win-rate denominator.

| Capability | Implemented behavior | Evidence | Limit |
|---|---|---|---|
| Deterministic lethal | Conservative public-state projection, bounded search, reobserve after each action | Five engine mechanism families; 30/30 known-positive variants recalled in ten actual development-game families; all 48 returned proofs finished as real-engine wins | Selected development cases; beam/node/time limits and unsupported effects yield unknown, not proof of no lethal |
| Probabilistic lethal | Optional Companion branch enumeration | One supported lethal branch among three equiprobable summons; 30 random engine trials recorded separately | Unhandled continuation mass is unproved; no general Juggler/Hounds probability solver |
| Next-turn finish | Conditional mana/burn calculation with Beast/no-Beast cases | Used in candidate summaries; inherited resource DP | No calibrated win probability, hidden-hand model or guarantee that the board survives |
| Face versus trade | Diverse candidate plans, raw hero-combat cost, retaliation warning; Luna chooses | Actual model selection/reason/default-disagreement logs; paired model-authority ablation | Disagreement is not proof of improvement; heuristic incoming attack is not an exact counterlethal search |
| Summon/order/position | Beast/burn preservation, Keeper before Secret, Juggler/Hyena before Hounds, Dire Wolf adjacency | Snake produces three knives; Houndmaster +2/+2; Wolf upper-bound regression and real-engine lethal | Random multi-action combos remain unsupported by deterministic proof; not all legal positions are offered in the top five |
| Secrets and Bow | Public trigger/order rules and contextual deployment; preserve last charge when useful | Explosive then Freezing triggers both and adds two durability; reverse order cancels attack, leaving Explosive and adding one | Opponent can bait/avoid Secrets; no validated equilibrium secret policy or full enemy-secret search |
| Opponent tendencies | Per-game shown cards, attacks, cheap minions and observed weapons; explicit unknown/mixed state | Public-history/no-cross-game-memory regression; model sees the summaries | No labeled hidden-archetype accuracy or calibrated probability claim |
| Mulligan and Tracking | Curve/Secretkeeper conditions, immediate and next-turn card utility, model choice | Course legal templates; Tracking removes three and adds chosen card; real phase logs | Heuristic ranking; no isolated mulligan win-gain claim |
| Hero power | Included alongside development and burn; deterministic lethal can force it | Real-engine lethal families and actual action logs | Long-run opportunity cost is strategic judgment, not an exhaustive two-turn proof |
| Ooze, Highmane, Krush | Contextual weapon/tempo alternatives, sticky-resource and charge-finisher plans | Weapon destroyed; Highmane two tokens; Krush real-engine lethal | Hidden future weapons/removal are unknown; hold-versus-play policy not separately calibrated |
| Runtime reliability | Bounded workers, strict action validation, game/seq binding, current fallback | Local faults, real official CLI integration, full version audits | Model can still bypass helper or end session; no independent rescue for a stalled generation |

The card-text correction with the clearest policy impact is Secretkeeper: the
course implementation buffs it only for its controller's Secrets despite printed
wording about any Secret. Course engine behavior is used. Tracking has the older
discard semantics. No modern card stats or external deck changes were imported.

The broad guide bundle improved the script baseline; C1's structural coverage
change reduced unsupported states without changing the 56-game win count. C2's
public risk summaries changed what the model could compare. C3 reduced workflow
defects but did not eliminate them. C4 repaired a proven search-bound omission;
C5 hardened malformed input and emphasized session lifetime. These changes do not
establish an ability to beat unknown Mystery Bot, Astra or student implementations.
