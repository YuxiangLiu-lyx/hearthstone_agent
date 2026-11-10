"""Fixed two-ply combat search opponent, with a deliberately approximate combat model.

It is an opponent policy, not a lethal proof system. Deathrattle material remains in its
valuation and triggers are not simulated; the real engine still executes all actions.
"""
import copy
from hs_arena.agents.greedy_bot import GreedyBot

def value(m):
    return 1.3*m['attack']+.7*m['health']+2*m.get('divine_shield',False)+2*m.get('deathrattle',False)

def hits(s):
    y,o=s['you'],s['opponent']
    targets=[m for m in o['board'] if not m.get('stealth')]
    taunts=[m for m in targets if m.get('taunt')]
    for m in y['board']:
        if m.get('can_attack') and m['attack']>0:
            for t in taunts or targets+[o['hero']]:yield {'type':'attack','attacker':m['entity_id'],'target':t['entity_id']}

def step(s,a):
    n=copy.deepcopy(s);y,o=n['you'],n['opponent']
    at=next(m for m in y['board'] if m['entity_id']==a['attacker'])
    target=next(m for m in o['board']+[o['hero']] if m['entity_id']==a['target'])
    atk,ret=at['attack'],target['attack']
    for m,d in ((target,atk),(at,ret)):
        if m.get('divine_shield') and d:m['divine_shield']=False
        else:m['health']-=d
    at['can_attack']=False
    y['board']=[m for m in y['board'] if m['health']>0]
    o['board']=[m for m in o['board'] if m['health']>0]
    return n

def evaluate(s):
    y,o=s['you'],s['opponent']
    if o['hero']['health']<=0:return 1e5
    return sum(map(value,y['board']))-sum(map(value,o['board']))-.8*o['hero']['health']

def decide(state,expand):
    base=GreedyBot('fixed-search',None).decide(state).action
    if state['phase']!='main':return base
    root=expand(state);start=evaluate(state);best=start;answer=None
    for a in hits(state):
        if a not in root:continue
        n=step(state,a);v=max([evaluate(n)]+[evaluate(step(n,b)) for b in hits(n)])
        if v>best:best,answer=v,a
    if answer and best-start>1:return answer
    return base
