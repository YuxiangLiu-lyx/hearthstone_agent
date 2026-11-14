"""Concrete legal actions from the host's public templates. No game engine access."""
from itertools import combinations


def expand(state, positions=True):
    result = []
    for t in state.get("legal_actions", []):
        kind = t["type"]
        if kind in ("concede", "submit_deck"):
            continue
        if kind == "mulligan":
            result.append({"type": kind, "replace": []})
        elif kind == "choose":
            ids = [o["entity_id"] if isinstance(o, dict) else o for o in t["options"]]
            for chosen in combinations(ids, t.get("min", 1)):
                result.append({"type": kind, "options": list(chosen)})
        elif kind == "end_turn":
            result.append({"type": kind})
        elif kind == "attack":
            result.extend({"type": kind, "attacker": t["attacker"], "target": x} for x in t["targets"])
        elif kind in ("play_card", "hero_power"):
            base = {"type": kind}
            if kind == "play_card":
                base["card"] = t["card"]
            for option in t.get("choose") or [None]:
                a = dict(base)
                if option:
                    a["choose"] = option["entity_id"]
                targets = (option if option else t).get("targets")
                pos = t.get("positions") or [None]
                if not positions:
                    pos = pos[:1]
                for target in targets or [None]:
                    for position in pos:
                        b = dict(a)
                        if target is not None:
                            b["target"] = target
                        if position is not None:
                            b["position"] = position
                        result.append(b)
    return result


def legal(state, action):
    """Accept optional omitted positions; validate mulligan subsets separately."""
    if not isinstance(action, dict):
        return False
    if not isinstance(action.get('type'),str):return False
    for key in ('card','target','attacker','position','choose'):
        if key in action and type(action[key]) is not int:return False
    for key in ('replace','options'):
        if key in action and (not isinstance(action[key],list) or any(type(x) is not int for x in action[key])):return False
    if action.get("type") == "mulligan":
        if set(action)!={'type','replace'}:return False
        t = next((t for t in state["legal_actions"] if t["type"] == "mulligan"), None)
        r = action.get("replace", [])
        return bool(t and isinstance(r, list) and len(r) == len(set(r))
                    and t.get("min", 0) <= len(r) <= t.get("max", len(t["options"]))
                    and all(type(x) is int and x in t["options"] for x in r))
    for candidate in expand(state):
        if "position" not in action:
            candidate.pop("position", None)
        if candidate == action:
            return True
    return False


def fallback(state):
    actions = expand(state, positions=False)
    return next((a for a in actions if a["type"] == "end_turn"), actions[0] if actions else None)
