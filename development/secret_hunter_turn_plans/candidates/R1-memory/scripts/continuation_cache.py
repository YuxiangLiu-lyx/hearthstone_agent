"""Deterministic continuations guarded by public state and stable configuration."""
import hashlib
import json
import time
import tactical_model as model
from action_validator import legal


def stable_config(cfg):
    return {k:v for k,v in cfg.items() if not k.startswith('_')}


def key(state):
    from plan_cache import fingerprint
    return fingerprint(state)


def take(state, cfg, memory):
    if not memory.get('steps'):
        return None, 'empty'
    if memory.get('identity') != [state.get('game_id'),state.get('turn')]:
        memory.clear(); return None, 'different_turn'
    if memory.get('config') != stable_config(cfg):
        memory.clear(); return None, 'configuration_changed'
    step=memory['steps'][0]
    if not model.supported(state) or key(model.prepare(state))!=step['expected']:
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
        expected=key(current)
        successor=model.transition(current,action)
        if successor is None:break
        if index:steps.append({'expected':expected,'action':action})
        current=successor
    if steps:
        memory.update(identity=[state.get('game_id'),state.get('turn')],
                      config=stable_config(cfg),steps=steps)
    return len(steps)
