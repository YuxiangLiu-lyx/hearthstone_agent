"""Bounded public chance branches. Never used as a guaranteed-lethal proof.

Exact enumeration aborts at a finite budget, then restarts with IID samples from a
public-state-derived PRNG. Unsupported outcomes invalidate the whole comparison.
No match seed, RNG state, opponent hand, or private card identity is consulted.
"""
import copy
import hashlib
import json
import random
import time
import tactical_model as model


class NeedChoice(Exception):
    def __init__(self, count, labels=None):
        self.count = count
        self.labels = labels


def choose(s, count, labels=None):
    cursor = s.get('_chance_cursor', 0)
    tape = s['_chance_tape']
    if cursor >= len(tape):
        raise NeedChoice(count, labels)
    result = tape[cursor]
    if result >= count:
        raise ValueError('Invalid public chance tape')
    s['_chance_cursor'] = cursor + 1
    return result


def knives(s, side, summoned_id):
    other = s['opponent'] if side is s['you'] else s['you']
    # Dead targets are excluded before the pending-death sweep.
    for j in side['board']:
        if j['card_id'] != 'NEW1_019' or j.get('silenced') or j['entity_id'] == summoned_id:
            continue
        targets = [m for m in other['board'] + [other['hero']] if m['health'] > 0]
        if targets:
            model.damage(targets[choose(s, len(targets), [m["entity_id"] for m in targets])], 1)


def project(state, action, tape):
    s = copy.deepcopy(state)
    s.update(_chance_tape=tape, _chance_cursor=0, planning_mode='proof')
    companion = None
    c = next((c for c in s['you']['hand'] if c['entity_id'] == action.get('card')), {})
    if c.get('card_id') == 'NEW1_031':
        companion = model.COMPANIONS[choose(s, 3)]
    out = model.transition(s, action, companion=companion)
    if out is not None:
        out.pop('_chance_tape', None)
        out.pop('_chance_cursor', None)
    return out


def outcomes(state, action, deadline, cap=12, samples=8):
    todo = [((), 1.0)]; result = []; attempts = 0
    while todo and attempts < cap * 4:
        if time.monotonic() >= deadline:
            return {'supported':False, 'reason':'deadline', 'nodes':attempts}
        tape, weight = todo.pop(); attempts += 1
        try:
            out = project(state, action, tape)
        except NeedChoice as exc:
            if len(todo) + len(result) + exc.count > cap:
                break
            todo.extend((tape + (i,), weight / exc.count) for i in range(exc.count))
            continue
        if out is None:
            return {'supported':False, 'reason':'unknown_effect', 'nodes':attempts}
        result.append((weight, out))
    else:
        if not todo:
            return {'supported':True, 'exact':True, 'outcomes':result, 'nodes':attempts}
    # Restart without retaining a biased, partially enumerated prefix.
    seed = hashlib.sha256(repr((model.signature(state), action)).encode()).digest()
    rng = random.Random(seed); result = []
    for _ in range(samples):
        tape = ()
        while len(tape) <= 20:
            if time.monotonic() >= deadline:
                return {'supported':False, 'reason':'deadline', 'nodes':attempts}
            attempts += 1
            try:
                out = project(state, action, tape)
                break
            except NeedChoice as exc:
                tape += (rng.randrange(exc.count),)
        else:
            return {'supported':False, 'reason':'trigger_cap', 'nodes':attempts}
        if out is None:
            return {'supported':False, 'reason':'unknown_effect', 'nodes':attempts}
        result.append((1.0 / samples, out))
    return {'supported':True, 'exact':False, 'outcomes':result, 'nodes':attempts}
