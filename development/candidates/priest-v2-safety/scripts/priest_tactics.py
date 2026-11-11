"""Priest-specific public-state features; no hidden state or engine access."""
from itertools import permutations
from evaluator import CATALOG, DEATH_VALUE, damage_value, minion_value

HEALTH_BUFFS = {"CS2_004": (0, 2), "EX1_194": (2, 2), "EX1_195": (0, 2), "EX1_623": (0, 3)}


def with_history(state, history):
    """Track temporary theft from own public turn history, never opponent private data."""
    turn = next((i for i in range(len(history)-1, -1, -1)
                 if history[i].get("event") == "turn_start"), len(history))
    temporary = []
    for event in history[turn:]:
        if event.get("event") == "play_card" and event.get("card_id") == "EX1_334" and event.get("player") == state.get("player"):
            target = event.get("target") or {}
            if isinstance(target, dict) and target.get("entity_id"):
                temporary.append(target["entity_id"])
    return {**state, "temporary_control": temporary}


def trade_value(m, enemies, attack=None, health=None):
    if not m.get("can_attack") or m.get("frozen"):
        return 0.
    attack = m["attack"] if attack is None else attack
    health = m["health"] if health is None else health
    visible = [e for e in enemies if not e.get("stealth") and not e.get("immune")]
    targets = [e for e in visible if e.get("taunt")] or visible
    best = 0.
    for target in targets:
        dies = target["attack"] > 0 and not m.get("divine_shield") and (target["attack"] >= health or target.get("poisonous"))
        kills = not target.get("divine_shield") and (attack >= target["health"] or m.get("poisonous"))
        value = damage_value(target, attack) - (minion_value(m) if dies else .4*min(target["attack"], health))
        if kills and not dies:
            value += 1.3
        best = max(best, value)
    return best


def buff_gain(m, da, dh, enemies):
    attack = m["attack"]+da
    if m["card_id"] == "EX1_335" and not m.get("silenced"):
        attack = m["health"]+dh
    gain = trade_value(m, enemies, attack, m["health"]+dh)-trade_value(m, enemies)
    survival = max((e["attack"] for e in enemies if m["health"] <= e["attack"] < m["health"]+dh
                    and not e.get("poisonous")), default=0)
    return .8*da + .35*dh + max(0, gain) + .45*survival


def heal_gain(m, amount, enemies, hero=False, danger=False):
    healed = max(0, min(amount, m["max_health"]-m["health"]))
    if hero:
        return healed*(1.6 if danger else .45)
    return buff_gain(m, 0, healed, enemies)


def temporary_trade_value(minion, enemies):
    """Value a temporary stolen attacker only for what can be spent this turn."""
    if minion.get("frozen") or "CANT_ATTACK" in CATALOG.get(minion["card_id"], {}).get("mechanics", []):
        return 0.
    other = [e for e in enemies if e["entity_id"] != minion["entity_id"] and not e.get("stealth")]
    targets = [e for e in other if e.get("taunt")] or other
    best = 0.
    for target in targets:
        dies = target["attack"] > 0 and not minion.get("divine_shield") and (target["attack"] >= minion["health"] or target.get("poisonous"))
        value = damage_value(target, minion["attack"])
        if dies:
            # A stolen deathrattle belongs to us when it dies, so stealing it is especially useful.
            value += minion_value(minion)
        else:
            value += .35*min(target["attack"], minion["health"])
        best = max(best, value)
    return best


def buff_lethal(state, ranked):
    """Conservative face-attack/buff lethal, with at most three spell plays.

Requires no enemy secrets and currently legal face attacks. Unknown own triggers
are excluded. Only one legal first action is returned; observe again after it.
"""
    y, o = state["you"], state["opponent"]
    if o.get("secrets_count") or o["hero"].get("immune"):
        return None
    if any(not m.get("silenced") and set(CATALOG.get(m["card_id"], {}).get("mechanics", [])) & {"TRIGGER", "AURA"}
           for m in y["board"]):
        return None
    hero_id = o["hero"]["entity_id"]
    face_actions = [a for _, a in ranked if a["type"] == "attack" and a["target"] == hero_id]
    objects = {m["entity_id"]: m for m in y["board"]+[y["hero"]]}
    # Hero attacks can kill us through retaliation; leave those to the inherited policy.
    face_actions = [a for a in face_actions if a["attacker"] != y["hero"]["entity_id"]]
    damage = sum(objects[a["attacker"]]["attack"] for a in face_actions)
    hp = o["hero"]["health"]+o["hero"].get("armor", 0)
    if face_actions and damage >= hp:
        return face_actions[0]
    cards = [c for c in y["hand"] if c["card_id"] in ("CS2_004", "EX1_194", "CS1_129")]
    root = {(a.get("card"), a.get("target")): a for _, a in ranked if a["type"] == "play_card"}
    for action in face_actions:
        m = objects[action["attacker"]]
        if m["entity_id"] in state.get("temporary_control", []):
            continue
        if m["card_id"] == "EX1_335" and not m.get("silenced"):
            continue  # Its dynamic attack aura is excluded from this small proof.
        for n in range(1, min(3, len(cards))+1):
            for group in permutations(cards, n):
                if sum(c["cost"] for c in group) > y["mana"]:
                    continue
                first = root.get((group[0]["entity_id"], m["entity_id"]))
                if first is None:
                    continue
                attack, health = m["attack"], m["health"]
                for c in group:
                    if c["card_id"] == "CS1_129":
                        attack = health
                    else:
                        da, dh = HEALTH_BUFFS[c["card_id"]]
                        attack += da; health += dh
                if damage-m["attack"]+attack >= hp:
                    return first
    return None
