"""Deterministic continuations guarded by public state and stable configuration."""
import hashlib
import json
import time
import copy
import tactical_model as model
from action_validator import legal


def stable_config(cfg):
    return {k:v for k,v in cfg.items() if not k.startswith('_')}


def key(state,canonical_entities=False):
    from plan_cache import fingerprint
    normalized=copy.deepcopy(state)
    for side in ('you','opponent'):
        if canonical_entities:
            for index,entity in enumerate(normalized[side]['board']):entity['entity_id']=index+1
        for entity in [normalized[side]['hero'],*normalized[side]['board']]:
            for flag in ('frozen','silenced','stealth','taunt','poisonous','immune','divine_shield','deathrattle'):
                entity[flag]=bool(entity.get(flag,False))
    # Engine observations expose affordability in usable. The deterministic
    # model retains the unused flag after spending mana on another action.
    power=normalized['you']['hero_power']
    power['usable']=bool(power.get('usable')) and normalized['you']['mana']>=power.get('cost',2)
    return fingerprint(normalized)


def take(state, cfg, memory):
    if not memory.get('steps'):
        return None, 'empty'
    if memory.get('identity') != [state.get('game_id'),state.get('turn')]:
        memory.clear(); return None, 'different_turn'
    if memory.get('config') != stable_config(cfg):
        memory.clear(); return None, 'configuration_changed'
    step=memory['steps'][0]
    if not model.supported(state) or key(model.prepare(state),step.get('canonical_entities',False))!=step['expected']:
        memory.clear(); return None, 'public_state_changed'
    if not legal(state,step['action']):
        memory.clear(); return None, 'action_no_longer_legal'
    memory['steps']=memory['steps'][1:]
    return step['action'], 'verified'


def save(state,cfg,sequence,memory,deadline):
    memory.clear()
    if len(sequence)<2 or not model.supported(state):return 0
    current=model.prepare({**state,'planning_mode':'response'});steps=[]
    for index,action in enumerate(sequence):
        if time.monotonic()>=deadline or action['type']=='end_turn':break
        synthetic=any(m['entity_id']<0 for side in ('you','opponent') for m in current[side]['board'])
        # Synthetic deathrattle IDs differ from engine IDs. A continuation can
        # refer only to already known positive entities; legality is checked again.
        canonical=synthetic and all(action.get(k,1)>0 for k in ('card','attacker','target'))
        expected=key(current,canonical)
        successor=model.transition(current,action)
        if successor is None:break
        if index:steps.append({'expected':expected,'action':action,'canonical_entities':canonical})
        current=successor
    if steps:
        memory.update(identity=[state.get('game_id'),state.get('turn')],
                      config=stable_config(cfg),steps=steps)
    return len(steps)
