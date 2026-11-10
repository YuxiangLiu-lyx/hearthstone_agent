"""Small, observation-only features shared by the Hunter policies."""
from hs_arena.cards import load

CATALOG = load()
BEAST_TOKENS = {"EX1_538t", "EX1_534t", "NEW1_032", "NEW1_033", "NEW1_034", "CS2_boar"}


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
