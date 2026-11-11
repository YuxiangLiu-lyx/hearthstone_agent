# Tactical policy and its limits

The fixed 30-card deck is unchanged. All decisions are Python decisions from the
current official public observation and this game's public history. Frozen
candidates and empirical selection are documented separately in REPORT.md.

1. **Lethal first.** An independent bounded exact-effect search runs before ordinary
   ranking. It handles attack order, Taunts, shields, armor, the weapon, hero power,
   Beast-enabled Kill Command, Dire Wolf positions, Hyena growth and Highmane tokens
   where the public transition is supported. Houndmaster and Secretkeeper buff lethals
   are covered by the ordinary turn search with a terminal score; the independent
   lethal entrypoint still uses base coverage (see coverage-boundary.json). Snake
   tokens count as Beasts. Random knives, unknown draws and hidden enemy Secrets do
   not become guaranteed damage. A discovered lethal always overrides material or
   defensive preferences. Finite search can still miss a lethal.
2. **Choose the damage clock.** A small mana-constrained hand knapsack estimates
   next-turn Kill Command plus hero power, including an affordable Beast setup.
   One estimate does not assume a surviving Beast; another is conditional on a
   current Beast surviving. Neither assumes a future draw, Huffer roll, unknown
   opposing heal or removal. When health reserve permits, entering this hand-damage
   range earns a closure bonus. Potential surviving board damage gets a smaller
   bonus. Face value is continuous across 10 health, correcting the old discontinuity.
3. **Check visible defensive responses.** For up to six promising own-turn endpoints,
   a bounded minimizing beam examines existing enemy attacks. It can discover a
   Taunt being removed before another attacker hits face, an efficient removal of
   Juggler/Hyena, or attacks that trigger or avoid own Secrets. A found visible
   lethal is strongly penalized. This is not an opponent-hand simulator and absence
   of a found lethal is not proof of safety. The health buffer is a tunable heuristic.
4. **Trade for a reason.** Static trade value is supplemented by surviving material,
   the opponent's possible attacks, and protection of high-value friendly minions.
   A small Beast can remove a larger threat, feed Hyena and preserve Juggler. Trading
   the last Beast before an affordable Kill Command loses its five-damage condition.
   Attacking with a ready Hyena is discouraged before useful Beast sacrifices.
   Safe face damage that sets up hand burn competes with those concrete trade gains.
5. **Order combos and respect mana/space.** Legal-action hints prioritize Hyena or
   Juggler before an affordable Hounds turn, and Hyena before existing Beast deaths.
   The exact planner can find Hounds -> Taunt trades -> enlarged ready Hyena face
   lethal. Knives are random: after each real summon, the policy observes the result
   and replans. Ordinary search does not compare playing Juggler against alternatives
   while pretending the following summons have no knives. The guarded candidate
   also preserves a ranked Coin that enables such an unmodelled follow-up.
6. **Deploy Secrets conditionally.** Deployment itself removes no enemy minions.
   Explosive checks face attacks and shields; Freezing responds to minion attacks,
   including attacks on friendly minions; Snake needs a friendly minion target and
   board space. Reveals restore Bow durability. The course's ordering matters:
   Explosive before Freezing can reveal both and bounce a pending casualty; Freezing
   first prevents the subsequent Explosive trigger. The response module rejects
   random Misdirection, Snake plus Juggler, unobserved freeze expiry and near-full-hand
   Freezing cases. Partial unsupported comparisons fall back to ordinary ranking.
7. **Opening curve.** The opening candidate prioritizes a supported one/two-drop
   curve, avoids duplicate combo pieces and expensive bricks, keeps one Secret with
   Keeper, and conditionally keeps Explosive or Hounds against pressure-prone classes.
   Hounds requires supporting early cards and mana/coin context. The class is a prior,
   never a claim to know the opponent's archetype or hidden cards. The original
   opening policy remains an explicit ablation and parameter-search option.

Houndmaster, Ooze, Tracking, Bow durability, Secret ordering, board-space and death
triggers retain the existing ranked rules and exact-effect guards. Tracking choices
use the real offered cards; they do not inspect future draws. No new card, online
RAG, LLM evaluator, opponent identity feature, private engine state or cross-game
memory is part of runtime policy.

The search saves a legal ranked action first. Own-turn, reply and lethal searches
have node, beam and monotonic-time caps under a 1.5-second soft deadline. The official
CLI supervises the worker within a 2-second engineering target and emits a saved
legal action after a crash or hang. Only the root action is submitted; subsequent
moves are recomputed from the latest actual observation and sequence.
