"""Finish a deterministic trap setup while public observations match the plan."""

import time

from action_validator import legal
import tactical_model as model


FLAGS = ('divine_shield', 'stealth', 'frozen', 'taunt', 'poisonous', 'silenced')


def stable_signature(state):
    # Canonicalize newly summoned entities by board position. Legal actions
    # still use current positive IDs and mismatches invalidate the continuation.
    normalized = dict(state)
    for side in ('you', 'opponent'):
        player = state[side]
        normalized[side] = {**player, 'board': [
            {**minion, 'entity_id': index + 1, **{flag: bool(minion.get(flag)) for flag in FLAGS}}
            for index, minion in enumerate(player['board'])
        ]}
    return repr((
        model.signature(normalized),
        tuple((bool(minion.get('deathrattle')), bool(minion.get('immune')), minion.get('spell_damage', 0))
              for side in ('you', 'opponent') for minion in state[side]['board']),
        tuple(sorted((card['entity_id'], card['card_id']) for card in state['you']['hand'])),
        tuple(bool(state[side]['hero'].get('immune')) for side in ('you', 'opponent')),
        tuple((state[side].get('weapon') or {}).get('card_id') for side in ('you', 'opponent')),
    ))


def take(state, memory):
    if memory.get('identity') != [state.get('game_id'), state['turn']] or not model.supported(state):
        memory.clear()
        return None
    steps = memory.get('trap_steps', [])
    if not steps:
        return None
    step = steps[0]
    if stable_signature(model.prepare(state)) != step['expected'] or not legal(state, step['action']):
        memory.clear()
        return None
    memory['trap_steps'] = steps[1:]
    return step['action']


def remember(state, first, sequence, memory, deadline):
    memory.clear()
    if not sequence or len(sequence) < 2 or sequence[0] != first or not model.supported(state):
        return
    if first['type'] not in ('attack', 'play_card') or first.get('target') is None:
        return
    own = state['you']
    if [secret['card_id'] for secret in own.get('secrets', [])] != ['EX1_610']:
        return
    target = next((m for m in state['opponent']['board'] if m['entity_id'] == first['target']), None)
    if target is None or not target.get('deathrattle') or target.get('silenced'):
        return
    tokens = model.DEATH_TOKENS.get(target['card_id'], ())
    if not tokens or not any(model.TOKENS[token][1] <= 2 for token in tokens):
        return
    current = model.prepare({**state, 'planning_mode': 'response'})
    if (current := model.transition(current, first)) is None:
        return
    if any(minion['entity_id'] == target['entity_id'] for minion in current['opponent']['board']):
        return
    steps = []
    for action in sequence[1:]:
        if time.monotonic() >= deadline:
            return
        if action['type'] not in ('play_card', 'hero_power') or action.get('target') is not None:
            return
        steps.append({'expected': stable_signature(current), 'action': action})
        if (current := model.transition(current, action)) is None:
            return
    memory.update(identity=[state.get('game_id'), state['turn']], trap_steps=steps)
