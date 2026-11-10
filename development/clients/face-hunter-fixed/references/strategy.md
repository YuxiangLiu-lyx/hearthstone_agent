# Face Hunter policy

V0 uses the fixed Beast Face Hunter deck. It keeps distinct one- and two-mana minions,
develops an inexpensive curve, attacks the opposing hero by default, removes blocking
Taunts, uses direct damage and spends spare mana on Steady Shot. All actions come from
the current legal-action templates. The CLI uses a two-second subprocess watchdog and
a phase-appropriate fallback. No cross-game memory or hidden opponent information is used.

Multi-action lethal search is added only after the baseline passes complete real games.
Later versions retain this baseline as a safe fallback. Random effects must never be
reported as deterministic wins. Replan after every actual action.
