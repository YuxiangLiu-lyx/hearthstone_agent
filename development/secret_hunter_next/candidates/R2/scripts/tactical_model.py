"""Conservative current-turn projection of public observations, not a game engine.

Only explicitly supported effects are projected. Unknown triggers, hidden secrets and
unobserved draws stop a search line. Actual matches always run in official hs-arena.
New tokens use negative planning IDs; only a root legal action is ever executed.
"""
import copy
from state_features import CATALOG, is_beast

WOLF, HYENA, LEOK = "DS1_175", "EX1_531", "NEW1_033"
COMPANIONS = ("NEW1_032", "NEW1_033", "NEW1_034")
TOKENS = {"EX1_538t": (1, 1, True, False), "EX1_534t": (2, 2, False, False),
          "NEW1_032": (4, 4, False, True), "NEW1_033": (2, 4, False, False),
          "NEW1_034": (4, 2, True, False), "skele21": (2, 1, False, False),
          "EX1_598": (1, 1, False, False), "EX1_554t": (1, 1, False, False), "EX1_110t": (4, 5, False, False)}
DEATH_TOKENS = {"EX1_534": ["EX1_534t"] * 2, "EX1_556": ["skele21"], "EX1_110": ["EX1_110t"]}
CHARGE = {"CS2_171", "CS2_173", "CS2_124", "CS2_131", "CS2_213", "EX1_067", "NEW1_011", "EX1_543"}
AURAS = {WOLF, LEOK, "EX1_162", "CS2_122"}
SAFE = {
    "CS2_182", "CS2_200", "CS2_179", "EX1_008", "NEW1_023", "CS2_033", "EX1_556", "EX1_534",
    "EX1_110", "EX1_096", "EX1_012", "EX1_028", "EX1_066", "CS2_120", "CS2_172", "CS2_065",
    "EX1_319", "EX1_362", "EX1_382", "CS2_151", "CS2_196", "CS2_088", "CS2_147", "EX1_015",
    "CS2_117", "EX1_032", "CS2_125", "CS1_069", "CS2_142", "CS2_197", "CS2_155", "EX1_563",
    "EX1_010", "EX1_029", "CS2_231", "CS2_168", "CS1_042", "CS2_226", "CS2_186", "CS2_181",
    "EX1_195", "EX1_623", "EX1_020", "CS2_127", "CS2_152", "CS2_101t", "CS2_tk1", "CS2_050",
    "CS2_022t", "hexfrog", "EX1_017", "EX1_531", "EX1_091", "EX1_019", "EX1_093", "EX1_046",
    "CS2_188", "EX1_586", "DS1_070", "CS2_189", "CS2_141", "CS2_150"
} | CHARGE | AURAS | set(TOKENS)
SAFE |= {"EX1_393", "EX1_597", "CS2_203", "EX1_080", "NEW1_019", "CS2_042", "CS2_064"}
PLAY_MINIONS = {WOLF, HYENA, "EX1_162", "EX1_080", "CS2_172", "CS2_120", "EX1_017", "EX1_534", "EX1_029"} | CHARGE
BASE_PLAY = PLAY_MINIONS.copy()
SECRETS = {"EX1_610", "EX1_611", "EX1_554", "EX1_533"}
PLAY_MINIONS |= {"NEW1_019", "EX1_066", "DS1_070"}
UNSUPPORTED_HISTORY = {"EX1_363", "CS2_038", "CS2_103", "NEW1_036", "CS2_084", "EX1_619", "EX1_549"}


def supported(state):
    if state.get("phase") != "main" or state["you"]["hero"]["hero_class"] != "HUNTER":
        return False
    if state["opponent"].get("secrets_count"):
        return False
    for side in (state["you"], state["opponent"]):
        if any(c["card_id"] in UNSUPPORTED_HISTORY for c in side.get("graveyard", [])):
            return False
        for m in side["board"]:
            if not m.get("silenced") and m["card_id"] not in SAFE and not (side is state["opponent"] and m["card_id"] in {"EX1_608", "NEW1_012"}):
                return False
            if m.get("deathrattle") and m["card_id"] not in set(DEATH_TOKENS) | {"EX1_029", "EX1_096", "EX1_012"}:
                return False
    weapon = state["you"].get("weapon")
    return not weapon or weapon["card_id"] in {"EX1_536", "CS2_106", "CS2_112", "CS2_091", "CS2_082"}


def aura(board, index):
    m = board[index]
    return sum(1 for j, source in enumerate(board) if j != index and not source.get("silenced")
               and ((source["card_id"] == WOLF and is_beast(m))
                    or source["card_id"] in (LEOK, "CS2_122")
                    or (source["card_id"] == "EX1_162" and abs(j-index) == 1)))


def enrage(m):
    return 3 if m["card_id"] == "EX1_393" and not m.get("silenced") and m["health"] < m.get("max_health", m["health"]) else 0


def refresh(state):
    for side in (state["you"], state["opponent"]):
        for i, m in enumerate(side["board"]):
            m["attack"] = m["base_attack"] + aura(side["board"], i) + enrage(m)
            m["can_attack"] = bool(m.get("remaining_attacks") and m["attack"] > 0 and not m.get("frozen"))


def prepare(state):
    result = {"phase": "main", "turn": state.get("turn", 0), "synthetic_id": -1, "mana_spent": 0, "planning_mode": state.get("planning_mode", "base"), "public_owner": state["you"]["hero"]["entity_id"], "public_opponent_evidence": copy.deepcopy(state.get("public_opponent_evidence", {}))}
    for key in ("you", "opponent"):
        result[key] = copy.deepcopy(state[key])
        for i, m in enumerate(result[key]["board"]):
            m["base_attack"] = m["attack"] - aura(result[key]["board"], i) - enrage(m)
            # The observation does not expose attacks already spent on Windfury.
            m["remaining_attacks"] = int(m.get("can_attack", False))
    hero = result["you"]["hero"]
    hero["remaining_attacks"] = int(hero.get("can_attack", False))
    result["hero_attack_available"] = bool(hero.get("can_attack") or state.get("hero_attack_available", False))
    return result


def damage(target, amount, poison=False):
    if amount <= 0 or target.get("immune"):
        return
    if target.get("divine_shield"):
        target["divine_shield"] = False
        return
    armor = min(target.get("armor", 0), amount)
    if "armor" in target:
        target["armor"] -= armor
    target["health"] -= amount-armor
    if poison and "hero_class" not in target:
        target["health"] = 0


def summon(state, side, cid, entity_id=None, hand_card=None, position=None):
    if len(side["board"]) >= 7:
        return
    if cid in TOKENS:
        attack, health, charge, taunt = TOKENS[cid]
        m = {"card_id": cid, "attack": attack, "health": health, "charge": charge, "taunt": taunt}
    else:
        data = CATALOG[cid]
        m = copy.deepcopy(hand_card or data)
        m["card_id"] = cid
        for flag in ("charge", "taunt", "divine_shield", "deathrattle", "windfury", "stealth", "poisonous"):
            m[flag] = flag.upper() in data.get("mechanics", [])
    if entity_id is None:
        entity_id = state["synthetic_id"]
        state["synthetic_id"] -= 1
    m.update(entity_id=entity_id, max_health=m["health"], base_attack=m["attack"],
             remaining_attacks=int(m.get("charge", False)), can_attack=bool(m.get("charge")))
    side["board"].insert(len(side["board"]) if position is None else position, m)
    refresh(state)


def cleanup(state):
    dead = []
    for key in ("you", "opponent"):
        side = state[key]
        for index, m in enumerate(side["board"]):
            if m["health"] <= 0:
                dead.append((key, index, m))
        side["board"] = [m for m in side["board"] if m["health"] > 0]
    refresh(state)
    for key, index, m in dead:
        side = state[key]
        other = state["opponent" if key == "you" else "you"]
        if is_beast(m):
            for survivor in side["board"]:
                if survivor["card_id"] == HYENA and not survivor.get("silenced"):
                    survivor["base_attack"] += 2
                    survivor["health"] += 1
                    survivor["max_health"] += 1
        if m.get("deathrattle"):
            cid = m["card_id"]
            if cid in ("EX1_096", "EX1_012"):
                if side['hero']['entity_id'] == state.get('public_owner') or side.get('deck_remaining', 0) <= 0 or side.get('hand_size', 0) >= 10:
                    return False
                # No identity is fabricated. Enemy draws do not change current public actions.
                side['hand_size'] = side.get('hand_size', 0) + 1
                side['deck_remaining'] -= 1
            if cid in DEATH_TOKENS and any(j['card_id']=='NEW1_019' and not j.get('silenced') for j in side['board']):
                return False  # Random knives after deathrattle summons are not projected.
            if cid == "EX1_029":
                damage(other["hero"], 2)
            for offset, token in enumerate(DEATH_TOKENS.get(cid, [])):
                summon(state, side, token, position=min(index+offset, len(side["board"])))
    refresh(state)
    return True


def spell_target(m):
    return not m.get("stealth") and not m.get("immune") and (m.get("silenced") or m["card_id"] != "NEW1_023")


def options(state, random=False):
    y, o = state["you"], state["opponent"]
    extended=state.get("planning_mode") in ("proof","response")
    visible = [m for m in o["board"] if not m.get("stealth") and not m.get("immune")]
    taunts = [m["entity_id"] for m in visible if m.get("taunt")]
    targets = taunts or ([] if o["hero"].get("immune") else [o["hero"]["entity_id"]]) + [m["entity_id"] for m in visible]
    for source in y["board"] + [y["hero"]]:
        if source.get("remaining_attacks") and source["attack"] > 0 and not source.get("frozen"):
            for target in targets:
                yield {"type": "attack", "attacker": source["entity_id"], "target": target}
    if y["hero_power"].get("usable") and y["hero_power"]["cost"] <= y["mana"]:
        yield {"type": "hero_power"}
    for c in y["hand"]:
        if c["cost"] > y["mana"]:
            continue
        cid = c["card_id"]
        if not extended and cid in (PLAY_MINIONS-BASE_PLAY)|SECRETS|{'EX1_617'}:continue
        if state.get('planning_mode')=='response' and cid=='NEW1_019':continue
        action = {"type": "play_card", "card": c["entity_id"]}
        if cid in ("DS1_185", "EX1_539"):
            for target in [o["hero"]] + o["board"]:
                if spell_target(target):
                    yield {**action, "target": target["entity_id"]}
        elif cid == "DS1_070" and len(y["board"]) < 7:
            beasts = [m for m in y['board'] if is_beast(m)]
            for target in beasts or [None]:
                yield {**action, 'position':len(y['board']), **({'target':target['entity_id']} if target else {})}
        elif cid in PLAY_MINIONS and len(y["board"]) < 7:
            for position in range(len(y['board'])+1) if cid=='EX1_162' else [len(y['board'])]:
                yield {**action, "position": position}
        elif cid in SECRETS and len(y.get('secrets', [])) < 5 and cid not in {x['card_id'] for x in y.get('secrets', [])}:
            yield action
        elif cid == 'EX1_617' and len(o['board']) == 1:
            yield action
        elif cid == "EX1_538" and o["board"] and len(y["board"]) < 7:
            yield action
        elif cid in ("GAME_005", "EX1_536"):
            yield action
        elif random and cid == "NEW1_031" and len(y["board"]) < 7:
            yield action


def transition(state, action, companion=None):
    result = copy.deepcopy(state)
    y, o = result["you"], result["opponent"]
    objects = {m["entity_id"]: m for side in (y, o) for m in side["board"] + [side["hero"]]}
    target = objects.get(action.get("target"))
    kind = action["type"]
    if kind == "attack":
        attacker = objects[action["attacker"]]
        attack, retaliation = attacker["attack"], target["attack"]
        a_shield, t_shield = attacker.get("divine_shield"), target.get("divine_shield")
        damage(target, attack, attacker.get("poisonous", False))
        damage(attacker, retaliation, target.get("poisonous", False))
        attacker["remaining_attacks"] -= 1
        attacker["stealth"] = False
        if attacker is y["hero"]:
            result["hero_attack_available"] = False
            if y.get("weapon"):
                y["weapon"]["durability"] -= 1
                if y["weapon"]["durability"] <= 0:
                    attacker["attack"] -= y["weapon"]["attack"]
                    y["weapon"] = None
        if attacker["card_id"] == "CS2_033" and not attacker.get("silenced") and attack > 0 and not t_shield:
            target["frozen"] = True
        if target["card_id"] == "CS2_033" and not target.get("silenced") and retaliation > 0 and not a_shield:
            attacker["frozen"] = True
    elif kind == "hero_power":
        cost = y["hero_power"]["cost"]
        y["mana"] -= cost; result["mana_spent"] += cost
        y["hero_power"]["usable"] = False
        damage(o["hero"], 2)
    elif kind == "play_card":
        c = next(c for c in y["hand"] if c["entity_id"] == action["card"])
        y["hand"].remove(c)
        y["mana"] -= c["cost"]; result["mana_spent"] += c["cost"]
        cid = c["card_id"]
        extended=result.get('planning_mode') in ('proof','response')
        if not extended and cid in (PLAY_MINIONS-BASE_PLAY)|SECRETS|{'EX1_617'}:return None
        if result.get('planning_mode')=='response' and cid=='NEW1_019':return None
        if cid in PLAY_MINIONS | {'EX1_538','NEW1_031'} and any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in y['board']):
            return None  # Keep deterministic attacks available without assuming random summon damage.
        spell_damage = sum(m.get("spell_damage", 0) for m in y["board"])
        if cid in PLAY_MINIONS:
            summon(result, y, cid, c["entity_id"], c, action.get("position"))
            if cid == 'DS1_070' and target is not None:
                if target not in y['board'] or not is_beast(target):return None
                target['base_attack'] += 2; target['health'] += 2; target['max_health'] += 2
                target['taunt'] = True
            if cid == 'EX1_066':
                o['weapon'] = None
                # Enemy hero attack in the observation is zero outside its turn.
        elif cid in SECRETS:
            if len(y.get('secrets', [])) >= 5 or cid in {x['card_id'] for x in y.get('secrets', [])}:return None
            y.setdefault('secrets', []).append(c)
            # Course Secretkeeper triggers only for its controller's Secrets.
            for keeper in y['board']:
                if keeper['card_id']=='EX1_080' and not keeper.get('silenced'):
                    keeper['base_attack'] += 1; keeper['health'] += 1; keeper['max_health'] += 1
        elif cid == 'EX1_617' and len(o['board']) == 1:
            o['board'][0]['health'] = 0
        elif cid == "DS1_185":
            damage(target, 2+spell_damage)
        elif cid == "EX1_539":
            damage(target, (5 if any(is_beast(m) for m in y["board"]) else 3)+spell_damage)
        elif cid == "EX1_538":
            for _ in range(min(len(o["board"]), 7-len(y["board"]))):
                summon(result, y, "EX1_538t")
        elif cid == "GAME_005":
            y["mana"] = min(10, y["mana"]+1)
        elif cid == "EX1_536":
            extra = y["hero"]["attack"] - (y.get("weapon") or {}).get("attack", 0)
            y["weapon"] = dict(c)
            y["hero"]["attack"] = extra+c["attack"]
            y["hero"]["remaining_attacks"] = int(result["hero_attack_available"] and not y["hero"].get("frozen"))
        elif cid == "NEW1_031" and companion in COMPANIONS:
            summon(result, y, companion)
        else:
            return None
    else:
        return None
    if not cleanup(result) or y["hero"]["health"] <= 0:
        return None
    return result


def signature(state):
    values = [state["you"]["mana"], state["you"]["hero_power"].get("usable"), state["hero_attack_available"]]
    for key in ("you", "opponent"):
        side = state[key]
        hero = side["hero"]
        values.extend((hero["health"], hero.get("armor", 0), hero["attack"], hero.get("remaining_attacks", 0), hero.get("frozen")))
        values.append(tuple((m["card_id"], m["entity_id"] if m["entity_id"] > 0 else 0, m["attack"], m["health"],
                             m["max_health"], m.get("remaining_attacks", 0), m.get("divine_shield"), m.get("stealth"), m.get("frozen"), m.get("taunt"), m.get("poisonous"), m.get("silenced")) for m in side["board"]))
    values.append((state['opponent'].get('hand_size',0), state['opponent'].get('deck_remaining',0)))
    values.append(tuple(c['card_id'] for c in state['you'].get('secrets', [])))
    values.append(tuple((state['opponent'].get('weapon') or {}).get(k, 0) for k in ('attack','durability')))
    values.append(tuple(sorted((c["entity_id"], c["cost"]) for c in state["you"]["hand"])))
    values.append(tuple((state["you"].get("weapon") or {}).get(k, 0) for k in ("attack", "durability")))
    return tuple(values)


def end_effects(state, side_key):
    """Project Imp Master end triggers, rejecting random summon interactions."""
    s = copy.deepcopy(state)
    side = s[side_key]
    masters = [m for m in side['board'] if m['card_id'] == 'EX1_597' and not m.get('silenced')]
    if masters and any(m['card_id'] == 'NEW1_019' and not m.get('silenced') for m in side['board']):
        return None
    for master in masters:
        if master not in side['board']:
            continue
        damage(master, 1)
        # The trigger batch summons before its pending deaths are swept.
        summon(s, side, 'EX1_598')
    if not cleanup(s):
        return None
    refresh(s)
    return s
