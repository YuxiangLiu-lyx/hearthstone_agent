"""Bounded replies using visible attacks only, with explicit own Secret triggers.

This is a public counterfactual, not a reconstruction of the opponent's hand.
Random Misdirection/knives, unknown draws and unsupported effects reject a branch.
No absence of a found attack lethal proves safety from hidden cards.
"""
import copy,time
import tactical_model as m
from race_plan import value


def prepare_reply(state):
    s=m.end_effects(state, 'you')
    if s is None:return None
    y,o=s['you'],s['opponent']
    # Observation omits exhaustion/attacks spent needed for exact end-turn thaw.
    if any(x.get('frozen') for x in y['board']+[y['hero']]):return None
    if any(c['card_id']=='EX1_533' for c in y.get('secrets',[])):return None
    if y.get('secrets') and any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in y['board']):
        if any(c['card_id']=='EX1_554' for c in y['secrets']):return None
    for x in o['board']:
        x['remaining_attacks']=0 if x.get('frozen') or x.get('hypothetical_fresh') else 2 if x.get('windfury') else 1
        x['can_attack']=bool(x['remaining_attacks'] and x['attack']>0)
    o['hero']['attack']=(o.get('weapon') or {}).get('attack',0)
    o['hero']['remaining_attacks']=int(o['hero']['attack']>0 and not o['hero'].get('frozen'))
    y['hero']['attack']=0
    return s


def attacks(s):
    defenders=[x for x in s['you']['board'] if not x.get('stealth') and not x.get('immune')]
    targets=[x['entity_id'] for x in defenders if x.get('taunt')]
    if not targets:targets=([] if s['you']['hero'].get('immune') else [s['you']['hero']['entity_id']])+[x['entity_id'] for x in defenders]
    for a in s['opponent']['board']+[s['opponent']['hero']]:
        if a.get('remaining_attacks') and a['attack']>0 and not a.get('frozen'):
            for target in targets:yield {'type':'attack','attacker':a['entity_id'],'target':target}


def attack(state,action):
    s=copy.deepcopy(state);y,o=s['you'],s['opponent']
    attacker=next((x for x in o['board']+[o['hero']] if x['entity_id']==action['attacker']),None)
    if attacker is None:return None
    target_hero=action['target']==y['hero']['entity_id'];bounced=False
    before_attack=attacker['attack']
    before_retaliation=next(x['attack'] for x in y['board']+[y['hero']] if x['entity_id']==action['target'])
    for secret in list(y.get('secrets',[])):
        cid=secret['card_id']
        trigger=(cid=='EX1_610' and target_hero and not bounced) or (cid=='EX1_611' and attacker is not o['hero']) or (cid=='EX1_554' and not target_hero and len(y['board'])<7)
        if cid=='EX1_533' and target_hero:return None
        if not trigger:continue
        if cid=='EX1_554' and any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in y['board']):return None
        y['secrets'].remove(secret)
        if (y.get('weapon') or {}).get('card_id')=='EX1_536':y['weapon']['durability']+=1
        if cid=='EX1_610':
            for x in o['board']+[o['hero']]:m.damage(x,2)
            if o['hero']['health']<=0:return s
        elif cid=='EX1_611':
            if o.get('hand_size',0)>=9:return None  # Full hand after the next draw: burn/deathrattle ordering excluded.
            o['board']=[x for x in o['board'] if x['entity_id']!=attacker['entity_id']]
            o['hand_size']=min(10,o.get('hand_size',0)+1);m.refresh(s);bounced=True
        elif cid=='EX1_554':
            for _ in range(min(3,7-len(y['board']))):m.summon(s,y,'EX1_554t')
    # Death processing follows the Secret broadcast; Freezing can remove a pending casualty.
    if not m.cleanup(s):return None
    # Trigger filters are re-evaluated after each Secret (bounced attackers stop Explosive).
    if not any(x['entity_id']==action['attacker'] for x in o['board']+[o['hero']]):return s
    # Reuse the exact combat projector with roles reversed, never exposing a real hidden hand.
    # Secret damage does not refresh attack auras/enrage until combat completes.
    attacker['attack']=before_attack
    defender=next((x for x in y['board']+[y['hero']] if x['entity_id']==action['target']),None)
    if defender is None:return None
    defender['attack']=before_retaliation
    swapped={**s,'you':o,'opponent':y}
    swapped['you'].setdefault('hand',[])
    result=m.transition(swapped,action)
    if result is None:return None
    return {**result,'you':result['opponent'],'opponent':result['you']}


def visible_reply(state,cfg,deadline,max_nodes=64):
    initial=prepare_reply(state)
    if initial is None:return {'supported':False,'nodes':0,'reason':'random_or_unobserved_response_effect'}
    best=initial;best_v=value(initial,cfg,after_response=True);nodes=0;frontier=[initial];seen=set();bounded=False
    for depth in range(9):
        following=[]
        for s in frontier:
            for a in attacks(s):
                if nodes>=max_nodes or time.monotonic()>=deadline:bounded=True;break
                r=attack(s,a);nodes+=1
                if r is None:return {'supported':False,'nodes':nodes,'reason':'unsupported_response_trigger'}
                key=m.signature(r)
                if key in seen:continue
                seen.add(key);v=value(r,cfg,after_response=True)
                if v<best_v:best,best_v=r,v
                if r['you']['hero']['health']>0 and r['opponent']['hero']['health']>0:following.append((v,r))
            if bounded:break
        if bounded or not following:break
        following.sort(key=lambda x:x[0]);frontier=[r for _,r in following[:cfg.get('reply_width',4)]]
    return {'supported':True,'nodes':nodes,'value':best_v,'state':best,'bounded':bounded,
            'visible_lethal_found':best['you']['hero']['health']<=0,
            'scope':'Bounded visible attacks and supported own Secrets only; hidden hand/draws excluded.'}


def worst_reply(state, cfg, deadline, max_nodes=64):
    base = visible_reply(state, cfg, deadline, max_nodes)
    if not base['supported'] or not cfg.get('hidden_scenarios'):
        return base
    o = state['opponent']
    if o['hero']['hero_class'] != 'WARLOCK' or o.get('hand_size', 0) == 0:
        return base
    mana = min(10, o.get('max_mana', o.get('mana', 0)) + 1)
    evidence = state.get('public_opponent_evidence', {})
    shown = evidence.get('shown_counts', {})
    hand = o.get('hand_size', 0) + 1
    deck = max(10, o.get('deck_remaining', 20) + hand)
    scenarios = []
    # Subjective class priors, explicitly bounded by the two-copy rule and public plays.
    for cid, cost, kind in [('EX1_308', 1, 'burn'), ('CS2_188', 1, 'buff'), ('EX1_093', 4, 'taunts')]:
        remaining = max(0, 2 - shown.get(cid, 0))
        if mana < cost or not remaining:
            continue
        weight = min(.18, remaining * hand / deck * (.7 if cid in shown else .35))
        s = copy.deepcopy(state)
        y, enemy = s['you'], s['opponent']
        if kind == 'burn':
            m.damage(y['hero'], 4)
        elif kind == 'buff':
            targets = [x for x in enemy['board'] if not x.get('frozen')]
            if not targets or len(enemy['board']) >= 7:
                continue
            target = max(targets, key=lambda x: x['attack'])
            target['base_attack'] += 2
            m.refresh(s)
        else:
            if not enemy['board'] or len(enemy['board']) >= 7:
                continue
            for target in sorted(enemy['board'], key=lambda x: x['health'], reverse=True)[:2]:
                target['base_attack'] += 1
                target['health'] += 1
                target['max_health'] += 1
                target['taunt'] = True
            m.summon(s, enemy, 'EX1_093')
            enemy['board'][-1]['hypothetical_fresh'] = True
            m.refresh(s)
        reply = visible_reply(s, cfg, deadline, max(12, max_nodes // 2))
        if not reply['supported'] or time.monotonic() >= deadline:
            continue
        # A hidden-card scenario can express risk, never a proven visible lethal.
        delta = max(-80., min(0., reply['value'] - base['value']))
        scenarios.append({'card': cid, 'weight': weight, 'value_delta': delta,
                          'lethal_under_hypothesis': reply['visible_lethal_found']})
        base['nodes'] += reply['nodes']
    base['value'] += sum(x['weight'] * x['value_delta'] for x in scenarios)
    base['scenarios'] = scenarios
    base['scope'] = 'Visible attacks plus finite subjective Warlock hand scenarios; no hidden card is asserted present.'
    return base
