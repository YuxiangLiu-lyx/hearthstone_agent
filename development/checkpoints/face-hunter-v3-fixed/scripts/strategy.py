"""Versioned policies with a small number of explicit tactical priorities."""
import copy
from action_validator import expand
from baseline import decide as baseline_decide, score as baseline_score
from state_features import effective_health, entities, is_beast

# Central policy weights; risk and next-turn features are heuristic, not calibrated odds.
DEFAULTS = {"next_turn_weight": 22.0, "survival_weight": 60.0,
            "combo_weight": 3.0, "random_margin": .08}


def projected(state, action):
    from tactical_model import prepare, transition, supported, COMPANIONS
    if not supported(state): return []
    model = prepare(state)
    if action["type"] == "end_turn": return [model]
    card = next((c for c in state["you"]["hand"] if c["entity_id"] == action.get("card")), {})
    if card.get("card_id") == "NEW1_031":
        return [s for cid in COMPANIONS if (s := transition(model, action, companion=cid)) is not None]
    if card.get("card_id") == "EX1_610":
        result = copy.deepcopy(model)
        result["you"]["mana"] -= card["cost"]
        result["you"]["hand"] = [c for c in result["you"]["hand"] if c["entity_id"] != card["entity_id"]]
        result["you"]["secrets"].append(card)
        return [result]
    try:
        successor = transition(model, action)
    except (KeyError, StopIteration):
        return []
    return [successor] if successor is not None else []


def choose_with_info(state, config=None):
    config = config or {}
    if state.get("phase") != "main": return baseline_decide(state), {"mode":"baseline"}
    plan = None
    if config.get("lethal"):
        from lethal_planner import search
        plan = search(state, budget_s=config.get("search_budget_s", .06), max_nodes=config.get("search_nodes", 1600))
        if plan["guaranteed"]: return plan["first_action"], {"mode":"guaranteed_lethal", "lethal":plan}
    fallback = baseline_decide(state)
    if not config.get("two_turn"):
        return fallback, {"mode":"baseline", "lethal":plan}
    from next_turn import features
    weights = {**DEFAULTS, **config.get("weights", {})}
    before = features(state)
    chance = None
    if config.get("risk"):
        from lethal_planner import probabilistic_lethal
        chance = probabilistic_lethal(state)
        if chance["first_action"] and chance["probability"] > before["stable_win_score"] + weights["random_margin"] and (before["survival_risk"] >= .65 or before["stable_win_score"] < .2):
            return chance["first_action"], {"mode":"high_risk_comeback", "random_lethal":chance, "next_turn":before}
    objects = entities(state)
    values = []
    for action in expand(state, positions=False):
        value = baseline_score(state, action)
        predictions = projected(state, action)
        if predictions:
            after = [features(p) for p in predictions]
            expected = lambda field: sum(a[field] for a in after)/len(after)
            value += weights["next_turn_weight"] * (expected("lethal_confidence")-before["lethal_confidence"])
            if config.get("risk"):
                value += weights["survival_weight"] * (before["survival_risk"]-expected("survival_risk"))
            current_reach = sum(m["attack"] for m in state["you"]["board"] if m.get("can_attack"))
            projected_reach = sum(sum(m["attack"] for m in p["you"]["board"] if m.get("can_attack")) for p in predictions)/len(predictions)
            # Reward enabling attack auras without penalizing spending an actual attack.
            if action["type"] == "play_card":
                value += weights["combo_weight"] * max(0, projected_reach-current_reach)
        elif config.get("risk") and action["type"] == "attack":
            source, target = objects[action["attacker"]], objects[action["target"]]
            if target in state["opponent"]["board"] and not target.get("divine_shield") and source["attack"] >= target["health"]:
                reduced = copy.deepcopy(state)
                reduced["opponent"]["board"] = [m for m in reduced["opponent"]["board"] if m["entity_id"] != target["entity_id"]]
                value += weights["survival_weight"] * (before["survival_risk"]-features(reduced)["survival_risk"])
        values.append((value, action))
    action = max(values, key=lambda row:row[0])[1] if values else fallback
    return action, {"mode":"stable_pressure", "next_turn":before, "random_lethal":chance, "lethal":plan}


def decide(state, config=None):
    return choose_with_info(state, config)[0]
