"""Reject attacks with already-provable lethal damage to our own hero.

Only visible immediate deaths are counted. Unmodeled deathrattle chains may still
exist; a false result is not a guarantee of safety. No hidden information is used.
"""


def dies(target, source):
    return (not target.get("immune") and not target.get("divine_shield") and source["attack"] > 0
            and (source["attack"] >= target["health"] or source.get("poisonous", False)))


def fatal_attack(state, action):
    if action["type"] != "attack" or state["you"]["hero"].get("immune"):
        return False
    y, o = state["you"], state["opponent"]
    entities = {m["entity_id"]: m for side in (y, o) for m in side["board"]+[side["hero"]]}
    source, target = entities[action["attacker"]], entities[action["target"]]
    if target is o["hero"]:
        return False  # Preserve the inherited direct-face lethal branch.
    damage, draws = 0, 0
    if source is y["hero"]:
        damage += target["attack"]
    for minion, killed, friendly in ((source, dies(source, target), True), (target, dies(target, source), False)):
        if not killed or minion.get("silenced") or not minion.get("deathrattle"):
            continue
        cid = minion["card_id"]
        if cid == "EX1_097" or (cid == "EX1_029" and not friendly):
            damage += 2
        if friendly and cid in ("EX1_096", "EX1_012"):
            draws += 1
    if draws > y["deck_remaining"]:
        n = draws-y["deck_remaining"]
        damage += sum(y.get("fatigue", 0)+i for i in range(1, n+1))
    return damage >= y["hero"]["health"]+y["hero"].get("armor", 0)
