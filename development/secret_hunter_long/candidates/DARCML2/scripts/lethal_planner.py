"""Bounded beam search and explicit Animal Companion chance branches."""
import time
from action_validator import legal
from state_features import effective_health, is_beast
from tactical_model import COMPANIONS, options, prepare, signature, supported, transition


def damage_upper_bound(state):
    """Ignore costs and Taunts; this overestimate can reject only impossible races."""
    y, o = state["you"], state["opponent"]
    ready = [m for m in y["board"] if m.get("can_attack")]
    wolves = sum(c["card_id"] == "DS1_175" for c in y["hand"])
    auras = wolves + sum(not m.get("silenced") and m["card_id"] in ("DS1_175", "NEW1_033", "CS2_122", "EX1_162") for m in y["board"])
    spell_damage = sum(m.get("spell_damage", 0) for m in y["board"])
    bound = sum(m["attack"] for m in ready) + y["hero"].get("attack", 0) + 2
    bound += wolves * sum(is_beast(m) for m in ready)
    hounds = 0
    from tactical_model import CHARGE
    for c in y["hand"]:
        cid = c["card_id"]
        if cid in ("DS1_185", "EX1_539"):
            bound += (2 if cid == "DS1_185" else 5) + spell_damage
        if cid in CHARGE:
            bound += c["attack"] + auras
        if cid == "EX1_536": bound += c["attack"]
        if cid == "EX1_538":
            hounds += len(o["board"])
            bound += len(o["board"]) * (1 + auras)
        if cid == "EX1_029": bound += 2
    bound += 2 * sum(m["card_id"] == "EX1_029" for m in y["board"])
    bound += 2 * sum(c['card_id']=='EX1_162' for c in y['hand'])
    bound += 2 * sum(m["card_id"] == "EX1_531" and not m.get("silenced") for m in ready) * (len(y["board"]) + len(y["hand"]) + hounds + 4)
    # Generous bounds for exact deterministic buff lines; never prune a possible buff lethal.
    bound += 2*sum(c['card_id']=='DS1_070' for c in y['hand'])*max(1,len(ready))
    bound += sum(c['card_id'] in ('EX1_610','EX1_611','EX1_554','EX1_533') for c in y['hand'])*sum(m['card_id']=='EX1_080' for m in ready)
    return bound


def potential(state):
    y = state["you"]
    attack = sum(m["attack"] for m in y["board"] if m.get("can_attack"))
    return -3 * effective_health(state["opponent"]["hero"]) + attack + .2 * y["mana"] + .1 * len(y["hand"])


def _search(initial, deadline, max_nodes, beam_width, max_depth, root_state=None):
    frontier = [(initial, [])]
    seen = set()
    nodes = 0
    for _ in range(max_depth):
        next_frontier = []
        for state, sequence in frontier:
            for action in options(state):
                if nodes >= max_nodes or time.perf_counter() >= deadline:
                    return None, nodes, True
                if not sequence and root_state is not None and not legal(root_state, action):
                    continue
                successor = transition(state, action)
                nodes += 1
                if successor is None:
                    continue
                line = sequence + [action]
                if successor["opponent"]["hero"]["health"] <= 0:
                    return (successor, line), nodes, False
                key = signature(successor)
                if key not in seen:
                    seen.add(key)
                    next_frontier.append((successor, line))
        if not next_frontier:
            return None, nodes, False
        next_frontier.sort(key=lambda item: potential(item[0]), reverse=True)
        frontier = next_frontier[:beam_width]
    return None, nodes, True


def search(state, budget_s=.05, max_nodes=1200, beam_width=32, max_depth=14):
    start = time.perf_counter()
    result = {"guaranteed": False, "first_action": None, "sequence": [], "mana_required": None,
              "damage": None, "depends_on_random": False, "nodes": 0, "bounded_out": False,
              "supported": supported(state)}
    if not result["supported"]:
        return result
    if damage_upper_bound(state) < effective_health(state["opponent"]["hero"]):
        result["pruned_by_upper_bound"] = True
        return result
    plan, nodes, bounded_out = _search(prepare(state), start+budget_s, max_nodes, beam_width, max_depth, state)
    result.update(nodes=nodes, bounded_out=bounded_out, elapsed_s=time.perf_counter()-start)
    if plan:
        final, line = plan
        result.update(guaranteed=True, first_action=line[0], sequence=line,
                      mana_required=final["mana_spent"], damage=effective_health(state["opponent"]["hero"])-effective_health(final["opponent"]["hero"]))
    return result


def probabilistic_lethal(state, budget_s=.05, max_nodes=900):
    result = {"first_action": None, "probability": 0.0, "depends_on_random": False,
              "branches": [], "probability_kind": "Exact uniform Companion probabilities, conservative searched continuation coverage."}
    if not supported(state):
        return result
    model = prepare(state)
    companion_ids = {c["entity_id"] for c in model["you"]["hand"] if c["card_id"] == "NEW1_031"}
    actions = [a for a in options(model, random=True) if a.get("card") in companion_ids and legal(state, a)]
    if not actions:
        return result
    action = actions[0]
    deadline = time.perf_counter()+budget_s
    branches = []
    for cid in COMPANIONS:
        successor = transition(model, action, companion=cid)
        branch_deadline = min(deadline, time.perf_counter()+budget_s/3)
        plan, nodes, bounded = _search(successor, branch_deadline, max_nodes//3, 24, 12)
        branches.append({"companion": cid, "probability": 1/3, "lethal_found": plan is not None,
                         "sequence": plan[1] if plan else [], "nodes": nodes, "bounded_out": bounded})
    probability = sum(b["probability"] for b in branches if b["lethal_found"])
    result.update(first_action=action if probability else None, probability=probability,
                  depends_on_random=0 < probability < 1, branches=branches)
    return result
