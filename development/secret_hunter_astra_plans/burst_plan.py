"""Compare the cost of covering a conditional burst with a complete defense."""
import time

from action_validator import expand
from chance_model import outcomes
from chance_search import continuation, score_endpoint, UnsupportedResponse
from reply_features import enrage_exposure
import tactical_model as model


def plan(state, baseline, baseline_plan, cfg, outer_deadline):
    if not enrage_exposure(state) or not baseline_plan or baseline_plan[0] != baseline:
        return None
    deadline = min(outer_deadline, time.monotonic() + .12)
    root = model.prepare({**state, 'planning_mode': 'proof'})
    anchor = root
    for action in baseline_plan:
        anchor = model.transition(anchor, action)
        if anchor is None or time.monotonic() >= deadline:
            return None
    hand = {c['entity_id']: c for c in state['you']['hand']}
    bow = next((a for a in expand(state) if hand.get(a.get('card'), {}).get('card_id') == 'EX1_536'), None)
    companion = next((c for c in hand.values() if c['card_id'] == 'NEW1_031'), None)
    if bow is None or companion is None or not root['hero_attack_available']:
        return None
    armed = model.transition(root, bow)
    if armed is None or armed['you']['mana'] < companion['cost']:
        return None

    hero = armed['you']['hero']
    amani = next(m for m in armed['opponent']['board'] if m['card_id'] == 'EX1_393'
                 and m['health'] == m['max_health'] and not m.get('silenced'))
    hit = next((a for a in model.options(armed) if a.get('attacker') == hero['entity_id']
                and a.get('target') == amani['entity_id']), None)
    if hit is None or hero['attack'] < amani['health'] or amani.get('divine_shield'):
        return None
    defended = model.transition(armed, hit)
    if defended is None:
        return None
    summon = {'type': 'play_card', 'card': companion['entity_id']}
    dist = outcomes(defended, summon, deadline, cap=8)
    if not dist['supported'] or not dist['exact']:
        return None

    # Shared endpoint scorer evaluates both plans. Replan the summon outcome
    # after observing it; no synthetic entity ID is sent to the game.
    from chance_search import utility
    stats = {'nodes': dist['nodes']}
    try:
        anchor_score = score_endpoint(anchor, utility(anchor, cfg), cfg, deadline, stats)
        scores = []
        for weight, child in dist['outcomes']:
            before, endpoint = continuation(child, cfg, deadline, stats, cap=40)
            scores.append((weight, score_endpoint(endpoint, before, cfg, deadline, stats)))
    except (TimeoutError, UnsupportedResponse):
        return None
    expected = sum(weight * score for weight, score in scores)
    if expected <= anchor_score + cfg.get('chance_margin', 1.0):
        return None
    return {'action': bow, 'anchor': anchor_score, 'alternative': expected,
            'samples': len(scores), 'nodes': stats['nodes']}
