"""Control Priest: preserve direct lethal, then steal, stabilize and retain resources."""
import base_policy
from evaluator import CATALOG, DEATH_VALUE, damage_value, hand_body, minion_value, threat
from priest_combat import joint_scores, key
from priest_tactics import HEALTH_BUFFS, buff_gain, buff_lethal, heal_gain, temporary_trade_value


def mulligan(state):
    hand = sorted(state["you"]["hand"], key=lambda c: c["cost"])
    fast = state["opponent"]["hero"]["hero_class"] in ("HUNTER", "WARLOCK", "ROGUE")
    keep, costs = [], {}
    for c in hand:
        cid, cost = c["card_id"], c["cost"]
        good = c["type"] == "MINION" and cost <= 2 and costs.get(cost, 0) < (2 if cost == 2 else 1)
        good |= cid == "EX1_556" and bool(keep) and not costs.get(3)
        good |= fast and cid in ("CS2_234", "CS1_130") and not costs.get("removal")
        if good:
            keep.append(c["entity_id"])
            category = cost if c["type"] == "MINION" else "removal"
            costs[category] = costs.get(category, 0)+1
    template = next(t for t in state["legal_actions"] if t["type"] == "mulligan")
    return {"type": "mulligan", "replace": [i for i in template["options"] if i not in keep]}


def rank_actions(state, config=None):
    config = config or {}
    ranked = base_policy.rank_actions(state, config)
    if ranked[0][0] >= 100000 or not config.get("specialist", True):
        return ranked
    lethal = buff_lethal(state, ranked)
    if lethal:
        return [(100000., lethal)] + ranked
    y, o = state["you"], state["opponent"]
    own = {m["entity_id"]: m for m in y["board"]}
    enemy = {m["entity_id"]: m for m in o["board"]}
    hand = {c["entity_id"]: c for c in y["hand"]}
    oh, eh = y["hero"]["entity_id"], o["hero"]["entity_id"]
    health = y["hero"]["health"]+y["hero"].get("armor", 0)
    next_fatigue = y.get("fatigue", 0)+1 if not y["deck_remaining"] else 0
    danger = threat(o)+3 >= health or next_fatigue >= health
    temporary = set(state.get("temporary_control", []))
    combined = joint_scores(state, ranked) if config.get("joint_combat", True) else {}
    result = []
    for score, action in ranked:
        kind, target = action["type"], action.get("target")
        if kind == "attack" and action["attacker"] in temporary and target in enemy:
            m, e = own[action["attacker"]], enemy[target]
            dies = not m.get("divine_shield") and e["attack"] > 0 and (e["attack"] >= m["health"] or e.get("poisonous"))
            score = damage_value(e, m["attack"]) + (minion_value(m) if dies else .35*min(e["attack"], m["health"]))
        elif kind == "hero_power" and target in own and target not in temporary:
            score = heal_gain(own[target], 2, o["board"])-.2
        elif kind == "hero_power" and target == oh:
            score = heal_gain(y["hero"], 2, o["board"], hero=True, danger=danger)-.2
        elif kind == "hero_power" and target in temporary:
            score = -50
        elif kind == "play_card":
            c = hand[action["card"]]; cid = c["card_id"]
            m, e = own.get(target), enemy.get(target)
            if cid == "EX1_091":
                score = hand_body(c)+.15*c["cost"]
                if e:
                    # The Cabal body consumes a slot before the steal resolves.
                    score += 1.8*minion_value(e) if len(own) <= 5 else -50
            elif cid == "CS1_113":
                score = 1.8*minion_value(e)-5 if e else -100
                if e and danger:
                    score += .8*e["attack"]
            elif cid == "EX1_196":
                score = hand_body(c)
                if e:
                    reduced = max(0, e["attack"]-2)
                    score += min(2, e["attack"])*(.9 if danger else .4)
                    for follow in hand.values():
                        if follow["cost"]+c["cost"] > y["mana"]:
                            continue
                        if follow["card_id"] == "EX1_091" and 2 < e["attack"] <= 4 and len(own) <= 4:
                            score = max(score, hand_body(c)+hand_body(follow)+1.8*minion_value({**e, "attack": reduced})-2)
                        if follow["card_id"] == "CS2_234" and 3 < e["attack"] <= 5:
                            score = max(score, hand_body(c)+minion_value(e)-2)
            elif cid == "EX1_334":
                score = temporary_trade_value(e, o["board"])-1.5 if e else -100
                if e and not any(t.get("taunt") for t in o["board"] if t is not e) and e["attack"] >= o["hero"]["health"]+o["hero"].get("armor", 0) and not o.get("secrets_count"):
                    score = 99999  # Execute the random-free steal, then inspect actual attack legality.
            elif cid == "EX1_198":
                score = 10 + .65*(1+e["health"])+minion_value(e) if e else -100
            elif cid == "EX1_564":
                copied = m or e
                score = minion_value(copied)-1 if copied and target not in temporary else -100
            elif cid in HEALTH_BUFFS:
                da, dh = HEALTH_BUFFS[cid]
                gain = buff_gain(m, da, dh, o["board"]) if m and target not in temporary else -30
                if c["type"] == "MINION":
                    score += gain - (da*(1.3 if m and m.get("can_attack") else .8)+.6*dh) if m else 0
                else:
                    score = gain - .45*c["cost"] - .7
            elif cid == "CS1_129":
                score = buff_gain(m, m["health"]-m["attack"], 0, o["board"])-1 if m and target not in temporary else -100
                if e:
                    score = 1.1*(e["attack"]-e["health"])-1
            elif cid == "CS1_112":
                score += sum(heal_gain(m, 2, o["board"]) for m in own.values() if m["entity_id"] not in temporary)
                score += heal_gain(y["hero"], 2, o["board"], hero=True, danger=danger)
            elif cid == "EX1_197":
                body = lambda m: minion_value(m)-DEATH_VALUE.get(m["card_id"], 0)*bool(m.get("deathrattle"))
                score = sum(body(m) for m in enemy.values() if m["attack"] >= 5)-sum(body(m) for m in own.values() if m["attack"] >= 5)-3
            elif cid == "EX1_339":
                copies = min(2, o["deck_remaining"], 11-len(hand))
                score = copies*(2.5 if len(hand) <= 3 else 1.2)-1
                if danger:
                    score -= 4
            elif cid == "EX1_193":
                score += 2.2 if o["deck_remaining"] and len(hand) < 10 else 0
            elif cid == "EX1_626":
                score = sum(2*bool(m.get("taunt"))+DEATH_VALUE.get(m["card_id"], 0)*bool(m.get("deathrattle"))
                            +max(0, m["attack"]-CATALOG.get(m["card_id"], {}).get("attack", m["attack"])) for m in enemy.values() if not m.get("silenced"))-2
                if y["deck_remaining"] and len(hand) < 10:
                    score += 1.5
                if not y["deck_remaining"] and next_fatigue >= health:
                    score = -10000
            elif cid == "CS2_117" and (m or target == oh):
                healed = m or y["hero"]
                score += heal_gain(healed, 3, o["board"], hero=target == oh, danger=danger)-min(3, healed["max_health"]-healed["health"])
            elif cid == "EX1_093":
                pos = action.get("position", len(own)); adjacent = y["board"][max(0, pos-1):pos+1]
                score += sum(buff_gain(m, 1, 1, o["board"])+(.8 if danger and not m.get("taunt") else 0)
                             for m in adjacent if m["entity_id"] not in temporary)
            elif cid == "GAME_005":
                setup = any(f["cost"] == y["mana"]+1 and f["card_id"] in ("CS1_112", "CS1_113", "EX1_197") for f in hand.values())
                if setup and enemy:
                    score = max(score, 2.)
            if c["type"] == "MINION" and len(own) >= 4 and not danger and len(own) >= len(enemy)+2:
                if cid not in ("EX1_091", "EX1_198", "EX1_093", "EX1_623"):
                    score -= 5  # Preserve follow-up bodies while ahead of public board pressure.
        score = max(score, combined.get(key(action), -100000))
        result.append((score, action))
    return sorted(result, key=lambda pair: pair[0], reverse=True)


def decide(state, config=None):
    if state["phase"] == "mulligan":
        return mulligan(state)
    if state["phase"] in ("choice", "game_over"):
        return base_policy.decide(state, config)
    return rank_actions(state, config)[0][1]
