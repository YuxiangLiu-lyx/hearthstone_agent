"""Public-information graph search with full engine opponent-turn trajectories.

Opponent decisions use a fixed policy of their own legal view, never root-private
cards or value-search conditioned on a sampled root hand. This avoids the
virtual-opponent information leak acknowledged in the original paper, III-D.
"""
from collections import Counter
import hashlib
import json
import math
import random
import time

from actions import expand
from mcgs_graph import Graph, Chance
from mcgs_world import build, clone, public_projection, Unsupported


def key(state, evidence=None):
    data=public_projection(state)
    # Tracking offers are visible but are not included in Engine.choice.source.
    data['choices']=[a for a in state.get('legal_actions',[]) if a['type']=='choose']
    data['evidence']=evidence or {}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def world_key(world,evidence):
    """Retain revealed plays and attack counts, allowing harmless attack swaps."""
    plays=[];attacks=Counter()
    for ev in world.events:
        v=ev.view(1)
        if not v:continue
        if v.get('event') in ('play_card','secret_revealed','choice_resolved'):
            plays.append(v)
        if v.get('event')=='attack':
            attacks[str(v.get('attacker'))]+=1
    return key(world.view(1),{'root':evidence,'plays':plays,'attacks':dict(attacks)})


def rank(state, cfg):
    """Cheap, perspective-local rollout ranking; retain every legal root action."""
    from secret_policy import rank as hunter_rank
    from base_policy import rank_actions
    if state['you']['hero']['hero_class']=='HUNTER':
        ranked=hunter_rank(state,cfg)
    elif state['phase']=='choice':
        options=expand(state)
        ranked=[(0,a) for a in options]
    else:
        ranked=rank_actions(state,cfg)
    # Category filtering must NOT delete beneficial friendly damage (Amani).
    objects={m['entity_id']:m for m in state['you']['board']}
    hand={c['entity_id']:c for c in state['you'].get('hand',[])}
    values=[]
    for value,a in ranked:
        if a['type']=='play_card' and hand.get(a['card'],{}).get('card_id')=='EX1_302':
            m=objects.get(a.get('target'),{})
            if m.get('card_id')=='EX1_393' and m.get('can_attack') and m['health']==m['max_health'] and m['health']>1:
                value=max(value,12.)
        values.append((value,a))
    return sorted(values,key=lambda x:x[0],reverse=True)


def rollout_action(state,cfg,rng):
    ranked=rank(state,cfg)
    if not cfg.get('opponent_plays',True) and cfg.get('_opponent'):
        ranked=[r for r in ranked if r[1]['type']!='play_card']
    if not ranked:return {'type':'end_turn'}
    if cfg.get('rollout','guided')=='filtered':
        # Champion-inspired categories; keep good friendly-target exceptions,
        # Coin sequences and end-turn. No forced face attack deletion rule.
        cutoff=max(-1.,ranked[0][0]-8)
        plausible=[a for v,a in ranked if v>=cutoff]
        return rng.choice(plausible)
    return ranked[0][1] if rng.random()>.12 else rng.choice(ranked[:min(3,len(ranked))])[1]


def reward(world,cfg):
    if world.over:return 1. if world.winner==1 else 0. if world.winner==2 else .5
    s=world.view(1);y,o=s['you'],s['opponent']
    # Bounded cutoff value; this is NOT a calibrated probability or lethal proof.
    def board(v):
        return sum(m['attack']+min(m['health'],5)*.65+1.3*m['taunt']+.9*m['divine_shield']
                   +1.5*m['deathrattle'] for m in v['board'])
    hp=y['hero']['health']+y['hero']['armor'];ehp=o['hero']['health']+o['hero']['armor']
    pressure=sum(m['attack'] for m in o['board'])
    raw=cfg.get('value_board',1.2)*(board(y)-board(o))+.28*(hp-ehp)
    raw+=.7*(len(y['hand'])-o['hand_size'])
    raw+=.8*len(y.get('secrets',[]))
    if hp<=pressure+3:raw-=cfg.get('value_danger',2.)*(pressure+3-hp)
    raw+=.9*max(0,12-ehp)
    return 1/(1+math.exp(-max(-40,min(40,raw/12))))


def search(state,cfg,baseline,deadline,*,seed=1978,max_transitions=None,trace=False):
    start=time.monotonic();rng=random.Random(seed);metrics=Counter()
    graph=Graph(cfg.get('graph','ucd'),cfg.get('d1',2),cfg.get('d2',1))
    evidence=state.get('public_opponent_evidence',{})
    root=graph.node(key(state,evidence));start_turn=state['turn']
    root_actions=expand(state)
    # Canonicalize an optional omitted position to the equivalent legal expansion.
    if baseline not in root_actions:
        baseline=next((a for a in root_actions if {k:v for k,v in a.items() if k!='position'}==baseline),root_actions[0])
    ordered=[baseline]+[a for _,a in rank(state,cfg) if a!=baseline]
    ordered += [a for a in root_actions if a not in ordered]
    chance={};particles=[];traces=[];root_totals={};root_visits=Counter()
    cap=max_transitions or cfg.get('max_transitions',1500)
    def alive():return time.monotonic()<deadline and metrics['transitions']<cap
    def step(w,a,trail):
        seat,_=w.pending();before=len(w.events)
        result=w.step(seat,a);metrics['transitions']+=1
        if not result.accepted:raise Unsupported('simulation_illegal:'+str(a))
        if trace:trail.append({'seat':seat,'turn':w.turn,'action':a,
            'events':[v for ev in w.events[before:] if (v:=ev.view(1)) is not None]})
    def advance(w,a,trail):
        step(w,a,trail)
        # End-turn is the paper's complete opponent-response chance branch.
        while not w.over and w.pending()[0]!=1 and alive() and (cfg.get('terminal') or cfg.get('horizon',3)>1):
            s=w.view(2)
            action=rollout_action(s,{**cfg,'_opponent':True},rng)
            step(w,action,trail);metrics['opponent_actions']+=1
        return w
    failure=None
    while alive() and metrics['iterations']<cfg.get('iterations',200):
        path=[];trail=[];first=None
        try:
            # Root latent particles have independent RNG, class/copy/hand constraints.
            target=min(cfg.get('particles',4),1+metrics['iterations']//4)
            if len(particles)<target:
                particles.append(build(state,rng.getrandbits(48)))
            world=clone(rng.choice(particles),rng.getrandbits(48))
            node=root;large=0
            for depth in range(cfg.get('tree_depth',40)):
                if not alive() or world.over or world.turn>=start_turn+cfg.get('horizon',3):break
                if world.pending()[0]!=1:break
                s=world.view(1);actions=ordered if node is root else [a for _,a in rank(s,cfg)]
                if not actions:break
                stats=[]
                for a in actions:
                    ak=json.dumps(a,sort_keys=True);ck=(node.key,ak)
                    ch=chance.setdefault(ck,Chance())
                    # Decision edge points to a distinct chance node; UCD payoff
                    # is shared at each public successor, not at hidden worlds.
                    cn=graph.node('chance:'+node.key+':'+ak)
                    edge=graph.connect(node,cn,a)
                    stats.append((edge.value(cfg.get('exploration',.35)),a,edge,ch))
                _,action,edge,ch=max(stats,key=lambda x:x[0])
                if first is None:first=json.dumps(action,sort_keys=True)
                ch.visits+=1;path.append(edge)
                expand_new=ch.count<ch.width(cfg,large)
                if expand_new:
                    world=advance(world,action,trail)
                    successor=world_key(world,evidence)
                    if cfg.get('graph')=='uct':successor=edge.child.key+'/'+successor
                    # Store full particles only at chance nodes, never in state keys.
                    ch.add(successor,clone(world,rng.getrandbits(48)))
                    metrics['chance_samples']+=1
                else:
                    successor,cached=ch.sample(rng);world=clone(cached,rng.getrandbits(48))
                    metrics['chance_reuses']+=1
                child=graph.node(successor)
                out=graph.connect(edge.child,child,{'outcome':successor})
                out.samples=ch.outcomes[successor]['count'];path.append(out);node=child
                if len(ch.outcomes)>cfg.get('damping_threshold',5):large+=1
                # After one newly discovered decision, use the same rollout in
                # every ablation. Full tree descent resumes on subsequent visits.
                if node.visits==0:break
            rollout_steps=0
            while alive() and not world.over and rollout_steps<cfg.get('rollout_steps',160):
                if cfg.get('terminal',False):
                    if world.turn>=start_turn+40:break
                elif world.turn>=start_turn+cfg.get('horizon',3):break
                seat,_=world.pending();s=world.view(seat)
                a=rollout_action(s,{**cfg,'_opponent':seat==2},rng)
                step(world,a,trail);rollout_steps+=1
                if seat==2:metrics['opponent_actions']+=1
            if not world.over and world.turn<start_turn+cfg.get('horizon',3):
                metrics['incomplete_discarded']+=1
                break
            r=reward(world,cfg)
            graph.backup(path,r)
            if first:
                root_totals[first]=root_totals.get(first,0.)+r;root_visits[first]+=1
            metrics['iterations']+=1
            metrics['cross_turn']+=int(world.turn>=start_turn+2)
            metrics['terminal']+=int(world.over)
            if trace:traces.append({'first':json.loads(first) if first else None,'reward':r,'terminal':world.over,
                                   'trajectory':trail,'end_state':world.view(1)})
        except Unsupported as exc:
            failure=str(exc);metrics['unsupported']+=1;break
        except Exception as exc:
            failure=type(exc).__name__+': '+str(exc);metrics['simulation_errors']+=1;break
    choices=[{'action':json.loads(a),'mean':root_totals[a]/n,'n':n} for a,n in root_visits.items()]
    choices.sort(key=lambda x:x['mean'],reverse=True)
    selected=baseline
    b=next((r for r in choices if r['action']==baseline),None)
    if b and choices and choices[0]['n']>=cfg.get('min_visits',2) and b['n']>=cfg.get('min_visits',2):
        if choices[0]['mean']>b['mean']+cfg.get('margin',.06):selected=choices[0]['action']
    return {'action':selected,'changed':selected!=baseline,'root_values':choices,
            'metrics':dict(metrics),'unique_states':len(graph.nodes),
            'transpositions':graph.transpositions,'offpath_updates':graph.offpath_updates,
            'failure':failure,'elapsed_s':time.monotonic()-start,'traces':traces,
            'scope':'Sampled hypothetical worlds; cutoff scores are not calibrated win probabilities.',
            'guaranteed':False}
