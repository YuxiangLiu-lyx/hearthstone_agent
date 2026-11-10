"""Zoo adjustments over the unchanged champion's public-observation policy.

Immediate lethal is returned BEFORE any Zoo adjustment. No hidden information,
random-outcome prediction, persistent state, or simulator is used here.
"""
from itertools import combinations
import base_policy
from zoo_combat import joint_scores, key as action_key
from evaluator import BUFFS, CATALOG, hand_body, minion_value, damage_value, threat

WOLF = 'EX1_162'
JUGGLER = 'NEW1_019'
SOULFIRE = 'EX1_308'
ARGUS = 'EX1_093'
STICKY = {'EX1_008', 'EX1_020', 'EX1_556', 'EX1_067'}
OPENERS = {'EX1_319', 'CS2_065', 'EX1_008'}
TEMP_BUFF = {'CS2_188', 'EX1_046'}
# Public class/mana warning, NOT an inference that the opponent holds an AoE.
AOE_WINDOW = {'MAGE': (7, 4), 'PALADIN': (4, 2), 'PRIEST': (5, 2),
              'WARLOCK': (4, 3), 'SHAMAN': (3, 3), 'DRUID': (4, 1)}


def mulligan(state):
    hand = state['you']['hand']
    keep = [c for c in hand if c['card_id'] in OPENERS][:2]
    # Abusive is a buff tool, not a good standalone 1/1 opener in this card pool.
    if keep:
        twos = sorted((c for c in hand if c['type'] == 'MINION' and c['cost'] == 2),
                      key=lambda c: (c['card_id'] != JUGGLER, -c.get('attack', 0)))
        keep += twos[:1]
        if twos and state['opponent']['hero']['hero_class'] in ('PRIEST', 'WARRIOR'):
            keep += [c for c in hand if c['card_id'] == 'EX1_556'][:1]
    ids = {c['entity_id'] for c in keep}
    template = next(t for t in state['legal_actions'] if t['type'] == 'mulligan')
    return {'type': 'mulligan', 'replace': [x for x in template['options'] if x not in ids]}


def trade_value(m, enemy, attack=None, health=None):
    """Best immediate legal-type exchange, used only to compare buff targets."""
    if not m.get('can_attack') or m.get('frozen'):
        return 0.
    atk = m['attack'] if attack is None else attack
    hp = m['health'] if health is None else health
    targets = [e for e in enemy if not e.get('stealth') and not e.get('immune')]
    taunts = [e for e in targets if e.get('taunt')]
    if taunts:
        targets = taunts
    best = 0.
    for e in targets:
        kill = not e.get('divine_shield') and (atk >= e['health'] or m.get('poisonous'))
        dies = (e['attack'] > 0 and not m.get('divine_shield') and not m.get('immune')
                and (e['attack'] >= hp or e.get('poisonous')))
        value = damage_value(e, atk) - (minion_value(m) if dies else .4 * e['attack'])
        if kill and not dies:
            value += 1.3
        best = max(best, value)
    return best


def buff_gain(m, da, dh, enemy):
    return max(0., trade_value(m, enemy, m['attack'] + da, m['health'] + dh)
               - trade_value(m, enemy))


def followers(card, bodies, mana, slots):
    others = [c for c in bodies if c['entity_id'] != card['entity_id']]
    return max((len(group) for n in range(min(3, slots, len(others)) + 1)
                for group in combinations(others, n)
                if card['cost'] + sum(c['cost'] for c in group) <= mana), default=0)


def aoe_exposed(you, opponent):
    window = AOE_WINDOW.get(opponent['hero']['hero_class'])
    if not window or opponent.get('max_mana', 0) + 1 < window[0]:
        return False
    board = you['board']
    return (len(board) >= 4 and sum(m['attack'] for m in board) >= 7
            and sum(m['health'] <= window[1] and not m.get('divine_shield')
                    and m['card_id'] not in STICKY for m in board) >= 3)


def rank_actions(state, config=None):
    ranked = base_policy.rank_actions(state, config)
    if ranked[0][0] >= 100000:
        return ranked  # Preserve the champion's immediate lethal branch exactly.
    you, opp = state['you'], state['opponent']
    board, enemy = you['board'], opp['board']
    own = {m['entity_id']: m for m in board}
    foes = {m['entity_id']: m for m in enemy}
    hand = {c['entity_id']: c for c in you['hand']}
    bodies = [c for c in hand.values() if c['type'] == 'MINION' and c.get('playable')]
    hp = you['hero']['health'] + you['hero'].get('armor', 0)
    eh = opp['hero']['entity_id']
    enemy_hp = opp['hero']['health'] + opp['hero'].get('armor', 0)
    danger = threat(opp) + 3 >= hp
    reserve = aoe_exposed(you, opp) and not danger and enemy_hp > 8
    juggler = next((c for c in bodies if c['card_id'] == JUGGLER), None)
    scores = []
    for score, action in ranked:
        kind = action['type']
        target = action.get('target')
        if kind == 'hero_power':
            # Never burn a draw, tap into fatigue, or spend the visible survival margin.
            safe = (len(hand) < 9 and you['deck_remaining'] > 0
                    and hp > max(8, threat(opp) + 5))
            if not safe:
                score = -100
            else:
                cost = you['hero_power']['cost']
                affordable_after = any(c['cost'] <= you['mana'] - cost for c in bodies)
                score = 2.5 + 1.5 * (len(hand) <= 2) + 3 * reserve
                if bodies and not affordable_after and not reserve:
                    score -= 5
                # If Soulfire already has a useful target, resolve its empty-hand
                # discard first; drawing an unknown card before it is avoidable loss.
                if len(hand) == 1 and next(iter(hand.values()))['card_id'] == SOULFIRE:
                    if any((a['type'] == 'play_card' and s > 0) for s, a in ranked):
                        score -= 8
        elif kind == 'attack' and target in foes:
            m = own.get(action['attacker'])
            e = foes[target]
            if m and m['attack'] >= e['health'] and not e.get('divine_shield'):
                survives = m.get('divine_shield') or (m['health'] > e['attack'] and not e.get('poisonous'))
                score += .7 if survives else 0
        elif kind == 'play_card':
            c = hand[action['card']]
            cid, cost = c['card_id'], c['cost']
            if cid == SOULFIRE:
                rest = [d for d in hand.values() if d is not c]
                if rest:
                    values = [hand_body(d) if d['type'] == 'MINION' else 3 for d in rest]
                    score -= .35 * sum(values) / len(values)
                if danger and target in foes and foes[target]['health'] <= 4 and not foes[target].get('divine_shield'):
                    score += 2
            elif cid == 'GAME_005':
                # Coin for two one-drops is missed by the generic single-card curve rule.
                cheap = [d for d in hand.values() if d['type'] == 'MINION' and d['cost'] == 1]
                if you['mana'] == 1 and len(cheap) >= 2 and len(board) <= 4:
                    score = max(score, 2)
            if c['type'] == 'MINION':
                pos = action.get('position', len(board))
                adj = board[max(0, pos-1):pos+1]
                if cid == JUGGLER:
                    score += 3 * followers(c, bodies, you['mana'], max(0, 6-len(board)))
                elif juggler and len(board) < 6 and cost + juggler['cost'] <= you['mana']:
                    score -= 3
                if cid in BUFFS and target in own:
                    da, dh = BUFFS[cid]
                    score += 1.1 * buff_gain(own[target], da, dh, enemy)
                    if cid in TEMP_BUFF and not own[target].get('can_attack'):
                        score -= 2
                if cid == WOLF:
                    score += sum(1.1 * buff_gain(m, 1, 0, enemy) for m in adj)
                elif cid == ARGUS:
                    score += sum(buff_gain(m, 1, 1, enemy) + (.9 if danger and not m.get('taunt') else 0) for m in adj)
                else:
                    # Avoid inserting a summoning-sick body between Wolf and a ready
                    # attacker: observation attack already includes the existing aura.
                    for index, m in enumerate(board):
                        if m['card_id'] != WOLF or m.get('silenced'):
                            continue
                        displaced = board[index-1] if pos == index and index else (
                            board[index+1] if pos == index+1 and index+1 < len(board) else None)
                        if displaced and displaced.get('can_attack'):
                            loss = trade_value(displaced, enemy) - trade_value(displaced, enemy, max(0, displaced['attack']-1))
                            score -= 1.2 + max(0, loss)
                    if cid in STICKY and pos in (0, len(board)):
                        score += .35
                if cid == 'EX1_066' and opp.get('weapon'):
                    score += 1.2 * opp['weapon']['attack'] * opp['weapon']['durability']
                if cid == 'EX1_319':
                    if hp <= 3:
                        score = -1000
                    elif hp <= threat(opp) + 6:
                        score -= 6
                if reserve and cid not in STICKY and cid != ARGUS:
                    score -= 5
                # Play affordable bodies before paying a random discard, only when
                # the same Soulfire remains affordable afterwards.
                if len(board) < 6 and any(d['card_id'] == SOULFIRE and d['cost'] + cost <= you['mana'] for d in hand.values()):
                    if any(a['type'] == 'play_card' and hand[a['card']]['card_id'] == SOULFIRE and s > 0 for s, a in ranked):
                        score += 1.5
        scores.append((score, action))
    if (config or {}).get('joint_combat', True):
        joint = joint_scores(state, scores)
        scores = [(max(score, joint.get(action_key(action), -1000)), action) for score, action in scores]
    return sorted(scores, key=lambda pair: pair[0], reverse=True)


def decide(state, config=None):
    # Non-Warlock observations retain the generic policy (e.g. generated fixtures).
    if state['phase'] in ('game_over', 'choice') or state['you']['hero']['hero_class'] != 'WARLOCK':
        return base_policy.decide(state, config)
    if state['phase'] == 'mulligan':
        return mulligan(state)
    return rank_actions(state, config)[0][1]
