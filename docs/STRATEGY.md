# Current strategy and known limits

## Shipped policy

The deck contains two copies of each: Argent Squire, Acidic Swamp Ooze, Argent Protector, Faerie Dragon,
Harvest Golem, Shattered Sun Cleric, Aldor Peacekeeper, Chillwind Yeti, Truesilver Champion, Consecration,
Blessing of Kings, Sen'jin Shieldmasta, Silver Hand Knight, Argent Commander and Guardian of Kings.
It has 30 legal cards, mean printed cost 3.6, and no legendary restriction issues.

The policy expands the current legal-action templates, values surviving board material, adjusts face pressure
according to opposing health and own visible danger, scores targeted battlecries/buffs on friendly minions,
values shields and deathrattle resources, and suppresses inefficient early face burn. Mulligan prefers low-cost
minions and keeps a three-drop only with an existing early play. A small hand-packing enumeration considers
up to two additional affordable bodies when choosing a minion. No invented future draw is included.

The evaluation is heuristic and empirically selected, not a solved value function. The same policy did not
improve the new Mage deck reliably; its Paladin synergy was established by the deck-policy ablation.
There is no opponent-name detector, no seed input, no opponent hand/deck access, and no cross-game memory.
The public board and opposing hero class are used; probabilistic hidden-hand modeling was not added without evidence.

`decide.py` reads game/state.json and returns seq/action. Setup validates and submits the bundled recipe.
The model relays actions via wait/act until terminal state. `history` is available for recovery.
Runtime dependencies are stdlib and the provided hs_arena package. A parent Python process kills a policy
worker after 2 seconds (configurable, capped at 5) and returns a legal fallback. The course limit is 180 seconds.
The watchdog bounds Python execution; it cannot prevent a model from ending its own session or stalling before calling Python.

## Search research, deliberately not shipped

`development/candidates/v4-paladin-search` contains a bounded current-turn DFS: up to 700 nodes,
35 ms default, ten actions deep. It models a whitelist of deterministic attacks, taunts, shield removal,
armor, freeze, charge, buffs, spell damage, Sorcerer's Apprentice cost reduction, Mana Wyrm triggers,
selected deathrattle tokens, direct damage and area damage. Unknown secrets/triggers and uncertain draws
cause abstention. Existing Windfury has one conservatively assumed remaining attack. It is incomplete.
Random lethal probability estimation and a full hidden-information Monte Carlo search were not implemented.

Real-engine differential tests found and corrected the mana cap on The Coin. Four replay-flagged lethals were
recreated and won in Fireplace. Search improved training from 323/400 to 330/400, but fresh holdout only from
382/480 to 385/480: paired 95% interval [0, 1.46] percentage points. It failed the preset promotion gate.
The simpler proven Champion remains shipped, with the research candidate retained for future work.

## Weaknesses supported by observations

- A separately tuned control Priest won 32/60 screening games against the Champion. On fresh seeds the
  Champion won only 35/80 against that frozen opponent (43.75%). Long-term resource exhaustion matters.
- Among 77 losses in the 400-game expanded benchmark, public-state screening found 55 with at most one
  card in hand, 39 with a board attack deficit, and 39 with visible lethal pressure. These labels overlap
  and are diagnostic signals, not proof of causation.
- The Champion can miss coordinated taunt removal and Consecration face lethal. Four specific cases were
  verified. This is an accepted limitation of the currently validated policy, not an assertion of perfect play.
- Unknown/generated cards still use approximate generic scoring. Secret inference and sophisticated
  multi-turn resource planning remain limited. Tests do not establish strength against Mystery Bot or Astra.
- A historical Luna run ended early after a message saying it would continue. The relay instructions were
  tightened; final-version results are reported separately. A few successful runs cannot prove zero future risk.
- A subsequent Paladin run timed out while waiting on the model, and some sessions improvised actions
  instead of calling the script. These are transport risks rather than Python latency. An additional minimal
  relay instruction revision is evaluated with per-action fidelity, not just wins and illegal-action counts.

Small deck substitutions were tested: two legendaries, lower curve, extra draw and extra burst. None passed
the preset statistical/regression gate in screening. Expanding complexity without validated benefit was rejected.
