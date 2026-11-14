"""Public end-turn features for recurring effects, traps and conditional burst."""
from evaluator import minion_value, threat
from state_features import effective_health
from tactical_model import DEATH_TOKENS, TOKENS


def summon_pressure(state):
    """Estimate the impact of repeatable effects given public room and resources."""
    own, enemy = state['you'], state['opponent']
    board = enemy['board']
    room = 7 - len(board)
    if room <= 0:
        return 0.0
    cards = enemy['hand_size'] + int(enemy.get('deck_remaining', 0) > 0)
    mana = max(0, min(10, enemy['max_mana'] + 1) - enemy.get('overload_next_turn', 0))
    next_plays = min(room, cards, mana / 2, 2.5)
    bodies = own['board']
    impact = 1 + sum(m['health'] == 1 and not m.get('divine_shield') for m in bodies) / (len(bodies) + 1)
    knives = sum(m['card_id'] == 'NEW1_019' and not m.get('silenced') for m in board)
    imps = sum(m['card_id'] == 'EX1_597' and not m.get('silenced') for m in board)
    return knives * min(room, next_plays + min(imps, room)) * impact + 0.5 * min(imps, room)


def explosive_credit(state):
    """Measure enemy material exposed to an already active Explosive Trap."""
    own, enemy = state['you'], state['opponent']
    if [c['card_id'] for c in own.get('secrets', ())] != ['EX1_610']:
        return 0.0
    if any(m.get('taunt') and not m.get('stealth') for m in own['board']):
        return 0.0
    credit = 0.0
    for minion in enemy['board']:
        if minion.get('immune'):
            continue
        if minion.get('divine_shield'):
            credit += 1.8
            continue
        if minion['health'] > 2:
            credit += 1.3
            if minion.get('deathrattle') and not minion.get('silenced'):
                # Prioritize breaking a sticky body before the trap fires if
                # its small replacement would be inside the same damage band.
                tokens = DEATH_TOKENS.get(minion['card_id'], ())
                credit -= sum(1.25 * TOKENS[token][0] for token in tokens if TOKENS[token][1] <= 2)
            continue
        removed = minion_value(minion)
        if minion.get('deathrattle') and not minion.get('silenced'):
            card = minion['card_id']
            # This feature prices the immediate replacement. Other deathrattles
            # already have a resource cost in the inherited minion evaluation.
            if card in DEATH_TOKENS:
                removed -= sum(1.25 * TOKENS[token][0] + .65 * TOKENS[token][1]
                               for token in DEATH_TOKENS[card])
            elif card == 'EX1_029':
                removed -= 2
            else:
                removed -= 1.5
        credit += max(0, removed)
    return credit


def enrage_exposure(state):
    """One affordable friendly ping can create lethal in an open attack lane.

    This is a risk feature, conditioned on an unseen playable ping. It is not
    a statement about the opponent's actual hand or a proof of lethal.
    """
    own, enemy = state['you'], state['opponent']
    if enemy['hero']['hero_class'] != 'WARLOCK' or own.get('secrets') or own['hero'].get('immune'):
        return False
    if any(m.get('taunt') and not m.get('stealth') and not m.get('immune') for m in own['board']):
        return False
    if not (enemy.get('hand_size') or enemy.get('deck_remaining')):
        return False
    if min(10, enemy['max_mana'] + 1) <= enemy.get('overload_next_turn', 0):
        return False
    if sum(c['card_id'] == 'EX1_302' for c in enemy.get('graveyard', ())) >= 2:
        return False
    visible = threat(enemy)
    health = effective_health(own['hero'])
    return visible < health <= visible + 3 and any(
        m['card_id'] == 'EX1_393' and m['health'] == m['max_health'] and m['health'] > 1
        and not any(m.get(flag) for flag in ('silenced', 'frozen', 'divine_shield', 'immune'))
        for m in enemy['board']
    )


def value_adjustment(state, cfg, after_response):
    value = 0.0
    if cfg.get('summon_pressure_weight'):
        value -= cfg['summon_pressure_weight'] * summon_pressure(state)
    if cfg.get('explosive_credit_weight'):
        value += cfg['explosive_credit_weight'] * explosive_credit(state)
    if not after_response and cfg.get('enrage_risk_cost') and enrage_exposure(state):
        value -= cfg['enrage_risk_cost']
    return value
