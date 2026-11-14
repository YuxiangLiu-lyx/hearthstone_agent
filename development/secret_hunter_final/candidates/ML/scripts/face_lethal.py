"""Narrow public proof: existing Hunter burn and Steady Shot, no attacks.

Unknown non-Hunter secrets are outside this proof. Hunter course secrets trigger
only on attacks or minion plays, neither of which is in a returned sequence.
Each invocation returns one currently legal action; never commits a future step.
"""
from itertools import combinations
from action_validator import expand, legal
from state_features import direct_damage, effective_health

SAFE = {'EX1_029','EX1_080','EX1_162','EX1_531','EX1_066','NEW1_019',
        'EX1_534','EX1_543','EX1_538t','EX1_554t','EX1_534t',
        'NEW1_032','NEW1_033','NEW1_034'}

def prove(state):
    if state.get('phase')!='main':return None
    y,o=state['you'],state['opponent'];hero=o['hero']
    if y['hero'].get('hero_class')!='HUNTER':return None
    if hero.get('immune') or hero.get('divine_shield'):return None
    if o.get('secrets_count',len(o.get('secrets',[]))) and hero.get('hero_class')!='HUNTER':return None
    target=hero['entity_id'];hp=effective_health(hero)
    if hp<=0 or y['hero']['health']<=0:return None
    actions=expand(state,positions=False);parts=[]
    power=next((a for a in actions if a['type']=='hero_power' and a.get('target',target)==target),None)
    if power:
        power_data=y.get('hero_power') or {}
        # The course Hunter power is exactly two damage. Do not use an upgraded
        # or replaced power merely because the hero class remains Hunter.
        if power_data.get('card_id') in ('DS1h_292','HERO_05bp'):
            parts.append((power,power_data.get('cost',2),2))
    if all(m.get('silenced') or m['card_id'] in SAFE for m in y['board']):
        for c in y['hand']:
            if c['card_id'] not in ('EX1_539','DS1_185'):continue
            a={'type':'play_card','card':c['entity_id'],'target':target}
            if legal(state,a):parts.append((a,c['cost'],direct_damage(c,state)))
    solutions=[]
    for n in range(1,len(parts)+1):
        for group in combinations(parts,n):
            cost=sum(x[1] for x in group);damage=sum(x[2] for x in group)
            if cost<=y['mana'] and damage>=hp:
                solutions.append((cost,n,sum(x[0]['type']=='play_card' for x in group),group,damage))
    if not solutions:return None
    _,_,_,group,damage=min(solutions,key=lambda x:x[:3])
    sequence=[x[0] for x in group]
    return {'guaranteed':True,'first_action':sequence[0],'sequence':sequence,
            'damage':damage,'mana_required':sum(x[1] for x in group),
            'proof':'visible_burn_and_steady_shot_only','nodes':len(solutions)}
