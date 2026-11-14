"""Public, no-draw own recovery projection after a bounded visible reply.

Independent Python mechanism inspired by PredatorMCTS; no copied source or
historical deck priors. The projection is a heuristic, never a lethal proof.
"""
import copy
import time
import tactical_model as model
from race_plan import value

def prepare_recovery(state):
    s=model.end_effects(state,'opponent')
    if s is None:return None
    s=copy.deepcopy(s);y,o=s['you'],s['opponent']
    if any(m.get('frozen') for side in (y,o) for m in side['board']+[side['hero']]):
        return None
    y['max_mana']=min(10,y['max_mana']+1);y['mana']=max(0,y['max_mana']-y.get('overload_next_turn',0))
    y['overloaded']=y.get('overload_next_turn',0);y['overload_next_turn']=0
    y['hero_power']['usable']=y['mana']>=y['hero_power']['cost']
    for m in y['board']:
        m['remaining_attacks']=2 if m.get('windfury') else 1;m['can_attack']=m['attack']>0
    y['hero']['attack']=(y.get('weapon') or {}).get('attack',0)
    y['hero']['remaining_attacks']=int(y['hero']['attack']>0);y['hero']['can_attack']=y['hero']['attack']>0
    o['hero']['attack']=0
    # A new own turn refreshes attack entitlement even if the prior
    # turn spent an attack or no weapon existed. No hypothetical draw is added.
    s['hero_attack_available']=True
    s['mana_spent']=0
    s['turn']=s.get('turn',0)+2
    return s

def recovery(state,cfg,deadline,max_nodes=16):
    s=prepare_recovery(state)
    if s is None:return {'supported':False,'nodes':0}
    if min(s['you']['hero']['health'],s['opponent']['hero']['health'])<=0:
        return {'supported':True,'nodes':0,'gain':0,'terminal':True}
    initial=value(s,cfg);best=initial;nodes=0;frontier=[s];seen=set()
    for depth in range(3):
        following=[]
        for current in frontier:
            for action in model.options(current):
                if nodes>=max_nodes or time.monotonic()>=deadline:
                    return {'supported':True,'nodes':nodes,'gain':best-initial,'bounded':True}
                nxt=model.transition(current,action);nodes+=1
                if nxt is None:continue
                key=model.signature(nxt)
                if key in seen:continue
                seen.add(key);v=value(nxt,cfg);best=max(best,v);following.append((v,nxt))
        if not following:break
        following.sort(key=lambda p:p[0],reverse=True);frontier=[p[1] for p in following[:4]]
    return {'supported':True,'nodes':nodes,'gain':best-initial,'bounded':False}
