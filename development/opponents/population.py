"""Different decision procedures, not renamed Greedy coefficients."""
import itertools
from hs_arena.agents.greedy_bot import GreedyBot
from hs_arena.cards import load

CATALOG = load()


def value(m):
    return m.get("attack", 0) * 1.2 + m.get("health", 0) * .7 + 2 * bool(m.get("divine_shield")) + 1.5 * bool(m.get("taunt"))


def decide(state, mode, expand):
    greedy = GreedyBot("fixed", None)
    if state["phase"] != "main" or mode == "official":
        return greedy.decide(state).action
    ctx = greedy._ctx(state)
    lethal = greedy._lethal(state, state["legal_actions"], ctx)
    if lethal:
        return lethal
    actions = expand(state)
    hand, own, enemy = ctx["hand"], ctx["own"], ctx["enemy"]
    face = ctx["enemy_hero"]
    attacks = [a for a in actions if a["type"] == "attack"]
    plays = [a for a in actions if a["type"] == "play_card"]
    # Aggro: face-first lexicographic race, kill only blockers; little regard for attrition.
    if mode == "aggressive":
        face_hits = [a for a in attacks if a["target"] == face]
        if face_hits:
            return max(face_hits, key=lambda a: own.get(a["attacker"], state["you"]["hero"])["attack"])
        burns = [a for a in plays if a.get("target") == face and hand[a["card"]]["card_id"] in
                 ("CS2_029", "CS2_024", "DS1_185", "EX1_539", "EX1_308")]
        if burns and state["opponent"]["hero"]["health"] <= 12:
            return burns[0]
        bodies = [a for a in plays if hand[a["card"]]["type"] in ("MINION", "WEAPON")
                  and a.get("target") not in enemy]
        if bodies:
            return max(bodies, key=lambda a: (hand[a["card"]].get("attack", 0) / max(1, hand[a["card"]]["cost"]),
                                               hand[a["card"]].get("attack", 0)))
        power = next((a for a in actions if a["type"] == "hero_power" and
                      (a.get("target") == face or ctx["hero_class"] == "HUNTER")), None)
        if power:
            return power
    # Tempo: solve a small hand-packing problem; favor multiple efficient bodies in a turn.
    elif mode == "tempo":
        candidates = {}
        for a in plays:
            c = hand[a["card"]]
            if c["type"] == "MINION" and a.get("target") not in enemy:
                candidates.setdefault(c["entity_id"], a)
        best, score = [], -1
        items = list(candidates)
        for n in range(1, min(7 - len(own), len(items)) + 1):
            for group in itertools.combinations(items, n):
                cost = sum(hand[x]["cost"] for x in group)
                if cost <= ctx["you"]["mana"]:
                    s = sum(value(hand[x]) for x in group) + .8 * cost
                    if s > score:
                        best, score = group, s
        if best:
            return candidates[max(best, key=lambda x: (hand[x]["card_id"] == "EX1_608", hand[x]["cost"]))]
    # Control: explicit survivor-first trading, remove largest threats, withhold early face burn.
    elif mode == "control":
        trades = []
        for a in attacks:
            m, target = own.get(a["attacker"], ctx["you"]["hero"]), enemy.get(a["target"])
            if target and m["attack"] >= target["health"] and not target.get("divine_shield"):
                survives = m["health"] > target["attack"] or m.get("divine_shield")
                trades.append((value(target) - (0 if survives else value(m)), a))
        if trades and max(s for s, _ in trades) >= -1:
            return max(trades, key=lambda x: x[0])[1]
        scored = list(greedy._candidates(state, state["legal_actions"]))
        scored = [(s if a.get("target") != face or a["type"] == "attack" else -.1, a) for s, a in scored]
        if scored and max(x[0] for x in scored) > 0:
            return max(scored, key=lambda x: x[0])[1]
        return {"type": "end_turn"}
    # Value: resource engine priority; draw and deathrattles before efficient tempo.
    elif mode == "value":
        if len(hand) <= 4 and ctx["you"]["hero"]["health"] >= 16:
            draw = [a for a in plays if "Draw" in hand[a["card"]].get("text", "") and "Discard" not in hand[a["card"]].get("text", "")]
            if draw:
                return min(draw, key=lambda a: hand[a["card"]]["cost"])
            if ctx["hero_class"] == "WARLOCK":
                hp = next((a for a in actions if a["type"] == "hero_power"), None)
                if hp:
                    return hp
        bodies = [a for a in plays if hand[a["card"]]["type"] == "MINION" and a.get("target") not in enemy]
        if bodies:
            return max(bodies, key=lambda a: value(hand[a["card"]]) + 4 * ("Deathrattle" in hand[a["card"]].get("text", "")))
    return greedy.decide(state).action
