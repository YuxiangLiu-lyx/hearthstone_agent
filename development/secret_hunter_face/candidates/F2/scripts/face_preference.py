"""Public, conditional face preference with explicit removal and survival exceptions."""
from evaluator import THREATS, minion_value, threat
from state_features import effective_health

# These engines can grow or repeatedly generate resources from visible triggers.
ENGINES = set(THREATS) | {'EX1_080', 'EX1_531', 'EX1_597', 'CS2_235'}


def pressure_window(state, cfg, after_response=False):
    """Secrets never certify survival; hidden damage retains the normal reserve."""
    if not cfg.get('face_preference') or state.get('phase') != 'main':
        return False
    own, enemy = state['you'], state['opponent']
    if enemy.get('secrets_count'):
        return False
    if any(m.get('taunt') and not m.get('stealth') for m in enemy['board']):
        return False
    # Preserve the existing high-value removal evaluation while a live engine remains.
    if any(not m.get('silenced') and m['card_id'] in ENGINES for m in enemy['board']):
        return False
    reserve = cfg.get('hidden_burst_buffer', 3)
    incoming = 0 if after_response else threat(enemy)
    return effective_health(own['hero']) > incoming + reserve


def ordinary_small_minion(minion):
    if not minion.get('silenced') and minion['card_id'] in ENGINES:
        return False
    if minion['attack'] > 2 or minion['health'] > 3:
        return False
    return not any(minion.get(flag) for flag in
                   ('taunt', 'divine_shield', 'poisonous', 'windfury', 'deathrattle', 'stealth'))


def endpoint_bonus(state, cfg, after_response=False):
    """Prefer damage already dealt and discount only ordinary small-body removal.

    Existing search still evaluates Secret triggers, visible counterattacks and
    combo growth. These coefficients express a strategy preference, not fitted
    win probabilities or a claim that the opponent must trigger a Secret.
    """
    if not pressure_window(state, cfg, after_response):
        return 0.0
    enemy = state['opponent']
    dealt = max(0, enemy['hero'].get('max_health', 30) - effective_health(enemy['hero']))
    ordinary = sum(minion_value(m) for m in enemy['board'] if ordinary_small_minion(m))
    return (cfg.get('face_damage_bonus', .45) * dealt
            + cfg.get('turn_board', 1.094) * cfg.get('small_body_discount', .25) * ordinary)


def attack_bonus(state, action, cfg, attacker):
    if action.get('target') != state['opponent']['hero']['entity_id']:
        return 0.0
    if not pressure_window(state, cfg):
        return 0.0
    return cfg.get('face_damage_bonus', .45) * min(attacker['attack'],
                                                 effective_health(state['opponent']['hero']))
