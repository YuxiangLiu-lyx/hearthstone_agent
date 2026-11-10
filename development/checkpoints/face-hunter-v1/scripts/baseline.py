"""V0: deterministic curve development and face pressure, without multi-action search."""
from action_validator import expand, fallback
from state_features import CATALOG, direct_damage, effective_health, entities, is_beast, minion_value


def mulligan(state):
    keep = []
    seen = set()
    for c in sorted(state["you"]["hand"], key=lambda c: (c["cost"], c["entity_id"])):
        if c["type"] == "MINION" and c["cost"] <= 2 and c["card_id"] not in seen:
            keep.append(c["entity_id"])
            seen.add(c["card_id"])
    return {"type": "mulligan", "replace": [c["entity_id"] for c in state["you"]["hand"] if c["entity_id"] not in keep]}


def score(state, action):
    y, o = state["you"], state["opponent"]
    objects = entities(state)
    kind = action["type"]
    if kind == "end_turn":
        return 0.0
    if kind == "attack":
        source, target = objects[action["attacker"]], objects[action["target"]]
        if source is y["hero"] and target.get("attack", 0) >= effective_health(source):
            return -1000.0
        if target is o["hero"]:
            return 35.0 + source["attack"]
        kills = not target.get("divine_shield") and (source["attack"] >= target["health"] or source.get("poisonous"))
        dies = not source.get("divine_shield") and target["attack"] >= source["health"]
        return (19 if target.get("taunt") else -6) + 5 * kills + minion_value(target) * kills - 3 * dies
    if kind == "hero_power":
        return 8.0
    if kind != "play_card":
        return -1000.0
    c = next(c for c in y["hand"] if c["entity_id"] == action["card"])
    cid = c["card_id"]
    target = objects.get(action.get("target"))
    if c["type"] == "MINION":
        return 15 + c["attack"] + .5 * c["health"] - .4 * c["cost"] + (4 if "CHARGE" in CATALOG.get(cid, {}).get("mechanics", []) else 0)
    damage = direct_damage(c, state)
    if damage:
        if target is o["hero"]:
            return 10 + 2 * damage
        if target in o["board"]:
            return (14 if target.get("taunt") else -10) + (5 + minion_value(target) if damage >= target["health"] and not target.get("divine_shield") else 0)
        return -1000.0
    if cid == "EX1_536":
        return 18 if not y.get("weapon") else -10
    if cid == "NEW1_031":
        return 21.0
    if cid == "EX1_538":
        return 4 * min(len(o["board"]), 7 - len(y["board"]))
    if cid == "EX1_610":
        return 5 + 2 * sum(m["health"] <= 2 and not m.get("divine_shield") for m in o["board"])
    if cid == "GAME_005":
        return 12 if any(d["cost"] == y["mana"] + 1 and d["type"] in ("MINION", "WEAPON") for d in y["hand"]) else -10
    return -1.0


def decide(state):
    if state["phase"] == "mulligan":
        return mulligan(state)
    actions = expand(state, positions=False)
    if state["phase"] == "choice":
        template = next(t for t in state["legal_actions"] if t["type"] == "choose")
        options = {c["entity_id"]: c for c in template["options"]}
        return max(actions, key=lambda a: sum(minion_value(options[i]) - .5 * options[i]["cost"] for i in a.get("options", [])))
    return max(actions, key=lambda a: score(state, a)) if actions else fallback(state)
