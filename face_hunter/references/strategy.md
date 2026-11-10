# Face Hunter policy

V0 uses the fixed Beast Face Hunter deck. It keeps distinct one- and two-mana minions,
develops an inexpensive curve, attacks the opposing hero by default, removes blocking
Taunts, uses direct damage and spends spare mana on Steady Shot. All actions come from
the current legal-action templates. The CLI uses a two-second subprocess watchdog and
a phase-appropriate fallback. No cross-game memory or hidden opponent information is used.

V1 adds bounded beam search over an explicit public-state tactical model. It models
Timber Wolf/Leokk attack auras, Unleash board capacity, Kill Command's current Beast
condition, Hyena death triggers, supported deathrattles, armor, shields, Coin, weapons,
and Steady Shot. The planner returns one legal root action and an explanatory plan;
negative IDs in a plan denote simulated tokens and are never sent to MCP. Existing
Windfury minions receive only one remaining attack when the observation is ambiguous.
Weapon attack availability is inferred only from complete public turn history.

Unknown opposing secrets, unsupported triggers and unobserved draws cause abstention.
This deliberately sacrifices search coverage rather than asserting an unsound lethal.
The analytical model does not access the live engine or its random seed. Real-game
outcomes and tactical differential tests use the official engine outside the skill.

V2 adds a bounded next-turn estimate for hand burn, Beast setup, hero power, board
survival, weapon reach and a held Wolf/Unleash combination. Healing/armor powers and
class-based clear risks reduce its confidence. Remaining-deck burn mass uses the
provided own deck counts. Survival and counterplay numbers are explicit, uncalibrated
heuristics; they are not hidden-hand predictions or measured win probabilities.

V3 evaluates all three uniformly distributed Animal Companion results. A searched
winning branch contributes one third; a missing branch is not assumed to win. Known
randomness and heuristic future confidence are reported separately. A comeback is
selected only when its searched chance exceeds the stable heuristic score plus a
margin and the current survival/continuation estimate is poor. Guaranteed lethal
always takes priority. Outside comeback mode, survival-aware scoring can choose a
necessary trade instead of face damage.

Four principal scoring weights are centralized in strategy.py and configurable through
config.json: next-turn confidence, survival risk reduction, immediate combo enablement,
and the required random-comeback margin. Search budgets have both time and node limits;
the CLI additionally has a hard subprocess watchdog. Frozen configurations and all
experiments are kept outside the submission. Replan after every actual action.
