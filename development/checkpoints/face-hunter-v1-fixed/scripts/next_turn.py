"""Explainable two-turn estimates; counterplay/survival numbers are heuristics."""
import math
from state_features import CATALOG, effective_health, is_beast


def burn_reach(hand, mana, beast=False, power_cost=2, slots=7):
    """Exact small hand DP for burn plus optional Beast setup; no future draw assumed."""
    states = {(0, beast): 0}
    for c in sorted(hand, key=lambda c:not (c["type"] == "MINION" and is_beast(c))):
        cid, cost = c["card_id"], c["cost"]
        if cid not in ("DS1_185", "EX1_539") and not (c["type"] == "MINION" and is_beast(c)):
            continue
        updated = dict(states)
        for (spent, active), damage in states.items():
            if spent+cost > mana: continue
            if cid == "DS1_185": extra, next_beast = 2, active
            elif cid == "EX1_539": extra, next_beast = 5 if active else 3, active
            else:
                if active or slots <= 0: continue
                extra, next_beast = 0, True
            key = (spent+cost, next_beast)
            updated[key] = max(updated.get(key, -1), damage+extra)
        states = updated
    return max((damage + (2 if spent+power_cost <= mana else 0) for (spent, _), damage in states.items()), default=0)


def features(state):
    y, o = state["you"], state["opponent"]
    next_mana = max(0, min(10, y["max_mana"]+1)-y.get("overload_next_turn", 0))
    enemy_mana = min(10, o["max_mana"]+1)
    enemy_class = o["hero"]["hero_class"]
    enemy_board = sum(m["attack"] * (2 if m.get("windfury") else 1) for m in o["board"] if not m.get("frozen"))
    enemy_weapon = (o.get("weapon") or {}).get("attack", 0)
    power_threat = 2 if enemy_class == "HUNTER" else 1 if enemy_class in ("MAGE", "DRUID") else 0
    taunt_buffer = sum(m["health"] + (2 if m.get("divine_shield") else 0) for m in y["board"] if m.get("taunt"))
    has_trap = any(s["card_id"] == "EX1_610" for s in y.get("secrets", []))
    trap_buffer = .7 * sum(m["attack"] for m in o["board"] if m["health"] <= 2 and not m.get("divine_shield")) if has_trap else 0
    visible_incoming = max(0, enemy_board+enemy_weapon+power_threat-taunt_buffer-trap_buffer)
    # This allowance is a conservative policy parameter, not knowledge of hidden cards.
    hidden_burn_allowance = min(4, enemy_mana) if o.get("hand_size", 0) and enemy_class in ("MAGE", "HUNTER", "ROGUE") else min(2, enemy_mana) if o.get("hand_size", 0) else 0
    risk = 1/(1+math.exp(max(-30, min(30, (effective_health(y["hero"])-visible_incoming-hidden_burn_allowance)/3))))
    if visible_incoming >= effective_health(y["hero"]): risk = max(risk, .95)
    counterplay = .1 + (.15 if o.get("hand_size", 0) >= 3 else 0)
    aoe_possible = enemy_mana >= (7 if enemy_class == "MAGE" else 4) and enemy_class in ("MAGE", "PRIEST", "PALADIN") and o.get("hand_size", 0) > 0
    expected_board = 0.0
    for m in y["board"]:
        survival = .75 if m.get("stealth") else .6
        if m["health"] <= 2 and aoe_possible: survival *= .5
        if enemy_board >= m["health"] and not m.get("stealth"): survival *= .75
        expected_board += m["attack"] * survival * (0 if m.get("frozen") else 1)
    if any(m.get("taunt") for m in o["board"]): expected_board *= .25
    has_beast = any(is_beast(m) for m in y["board"])
    # Try both orderings because a Beast can precede a burn card regardless of hand order.
    hand = sorted(y["hand"], key=lambda c: not (c["type"] == "MINION" and is_beast(c)))
    slots = 7-len(y["board"])
    floor = burn_reach(hand, next_mana, False, y["hero_power"]["cost"], slots)
    ceiling = burn_reach(hand, next_mana, has_beast, y["hero_power"]["cost"], slots)
    expected_burn = floor + .65 * (ceiling-floor)
    combo_reach = 0.0
    unleashes = [c for c in hand if c["card_id"] == "EX1_538"]
    saved_wolves = [c for c in hand if c["card_id"] == "DS1_175"]
    existing_wolves = sum(m["card_id"] == "DS1_175" and not m.get("silenced") for m in y["board"])
    if unleashes:
        for new_wolves in range(len(saved_wolves)+1):
            cost = unleashes[0]["cost"] + sum(c["cost"] for c in saved_wolves[:new_wolves])
            count = min(len(o["board"]), max(0, slots-new_wolves))
            if cost <= next_mana and count:
                excluded = {c["entity_id"] for c in [unleashes[0], *saved_wolves[:new_wolves]]}
                rest = [c for c in hand if c["entity_id"] not in excluded]
                damage = count*(1+.65*existing_wolves+new_wolves)
                if any(m.get("taunt") for m in o["board"]): damage *= .25
                combo_reach = max(combo_reach, damage+burn_reach(rest,next_mana-cost,True,y["hero_power"]["cost"],slots-new_wolves-count))
    weapon = y.get("weapon")
    weapon_reach = weapon["attack"] if weapon and weapon["durability"] > 0 and not any(m.get("taunt") for m in o["board"]) else 0
    counts = y.get("deck_remaining_counts", {})
    total = sum(counts.values())
    draw_burn_mass = sum(n for cid,n in counts.items() if cid in ("DS1_185", "EX1_539") and CATALOG[cid]["cost"] <= next_mana) / total if total else 0
    heal_buffer = 2 if enemy_class in ("PRIEST", "WARRIOR") and enemy_mana >= 2 else 0
    target = effective_health(o["hero"]) + heal_buffer
    reach = max(expected_burn, .8*combo_reach) + expected_board + .6*weapon_reach
    confidence = max(0, min(1, (reach-target+3)/6))
    if floor >= target: confidence = max(confidence, .95)
    stable_score = confidence * (1-risk) * (1-counterplay)
    return {"next_mana":next_mana, "burn_without_existing_beast":floor, "burn_with_existing_beast":ceiling,
            "expected_board_damage":expected_board, "expected_reach":reach, "draw_burn_mass":draw_burn_mass,
            "hound_combo_reach":combo_reach,
            "visible_incoming":visible_incoming, "hidden_burn_allowance":hidden_burn_allowance,
            "survival_risk":risk, "counterplay_risk":counterplay, "lethal_confidence":confidence,
            "stable_win_score":stable_score, "probability_kind":"Uncalibrated heuristic scores; draw_burn_mass is the remaining-deck card-category fraction."}
