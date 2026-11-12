"""Small, observation-only features shared by the Hunter policies."""
from hs_arena.cards import load

CATALOG = load()
BEAST_TOKENS = {"EX1_554t", "EX1_538t", "EX1_534t", "NEW1_032", "NEW1_033", "NEW1_034", "CS2_boar"}


def is_beast(card):
    return CATALOG.get(card["card_id"], {}).get("race") == "BEAST" or card["card_id"] in BEAST_TOKENS


def effective_health(hero):
    return hero["health"] + hero.get("armor", 0)


def entities(state):
    return {c["entity_id"]: c for side in ("you", "opponent")
            for c in state[side]["board"] + [state[side]["hero"]]}


def direct_damage(card, state):
    cid = card["card_id"]
    base = 2 if cid == "DS1_185" else (5 if any(is_beast(m) for m in state["you"]["board"]) else 3) if cid == "EX1_539" else 0
    return base + sum(m.get("spell_damage", 0) for m in state["you"]["board"]) if base else 0


def minion_value(m):
    return m.get("attack", 0) + .5 * m.get("health", 0) + int(m.get("divine_shield", False))


def with_public_history(state, history):
    """Infer unused hero attacks only when this turn's public history is complete."""
    if state.get("phase") != "main":
        return state
    opponent=3-state['player']
    shown=[e for e in history if e.get('player')==opponent and e.get('event')=='play_card']
    attacks=[e for e in history if e.get('player')==opponent and e.get('event')=='attack']
    face=sum((e.get('target') or {}).get('entity_id')==state['you']['hero']['entity_id'] for e in attacks)
    cheap=sum(e.get('cost',99)<=2 and CATALOG.get(e.get('card_id'),{}).get('type')=='MINION' for e in shown)
    weapons=[e.get('card_id') for e in history if e.get('player')==opponent and e.get('event')=='weapon_equipped']
    state={**state,'public_opponent_evidence':{'shown_cards':list(dict.fromkeys(e['card_id'] for e in shown)),
           'shown_card_counts':{cid:sum(e.get('card_id')==cid for e in shown) for cid in {e['card_id'] for e in shown}},
           'face_attacks':face,'other_attacks':len(attacks)-face,'cheap_minions_played':cheap,
           'weapons_seen':weapons,'tendency':'fast_pressure_evidence' if cheap>=2 or face>=3 else 'insufficient_or_mixed',
           'uncertainty':'Public evidence only; hidden hand and complete archetype remain unknown.'}}
    starts = [i for i, e in enumerate(history) if e.get("event") == "turn_start" and e.get("turn") == state["turn"]]
    if not starts:
        return state
    hero = state["you"]["hero"]
    attacked = any(e.get("event") == "attack" and (e.get("attacker") or {}).get("entity_id") == hero["entity_id"]
                   for e in history[starts[-1]:])
    return {**state, "hero_attack_available": not attacked and not hero.get("frozen", False)}
