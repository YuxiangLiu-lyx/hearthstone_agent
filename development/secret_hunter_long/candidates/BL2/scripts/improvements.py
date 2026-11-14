"""Explicit survival, resource and conditional secret hypotheses."""
import time
from state_features import effective_health,entities,is_beast
from evaluator import threat,minion_value
from secret_policy import SECRETS


def rerank(state, ranked, cfg, deadline):
    if state['phase']!='main':return ranked
    y,o=state['you'],state['opponent'];obj=entities(state);hand={c['entity_id']:c for c in y['hand']}
    hp=effective_health(y['hero']);ehp=effective_health(o['hero']);incoming=threat(o)
    danger=incoming+cfg.get('risk_buffer',3)>=hp
    # This is a threat signal, not a claim about a hidden hand or a forced kill.
    survival=cfg.get('survival_weight',2.0);resource=cfg.get('resource_weight',1.0)
    combo=cfg.get('combo_weight',1.0);secret=cfg.get('secret_weight',1.0)
    out=[]
    for score,a in ranked:
        if time.monotonic()>=deadline:break
        if score>=100000:out.append((score,a));continue
        if cfg.get('scoring'):
            if a['type']=='attack':
                at,t=obj[a['attacker']],obj[a['target']]
                if a['target']!=o['hero']['entity_id']:
                    kills=not t.get('divine_shield') and (at['attack']>=t['health'] or at.get('poisonous'))
                    if danger and kills:score+=survival*t['attack']
                    if a['attacker']==y['hero']['entity_id']:
                        after_hp=hp-t['attack'];after_incoming=incoming-(t['attack'] if kills else 0)
                        if after_hp<=after_incoming and not any(m.get('taunt') for m in y['board']):score-=survival*max(0,t['attack'])*2
                elif danger:score-=survival*at['attack']*.35
            elif a['type']=='play_card':
                c=hand[a['card']];cid=c['card_id'];t=obj.get(a.get('target'))
                if cid=='EX1_539' and t and t is not o['hero']:
                    damage=5 if any(is_beast(m) for m in y['board']) else 3
                    if danger and damage>=t['health'] and not t.get('divine_shield'):score+=survival*t['attack']
                if c['type']=='MINION' and danger and cid not in ('DS1_070','EX1_543'):
                    score-=survival*max(0,incoming-hp+1)*.6
                # Bow tempo and a developed board make a renewable hero power competitive.
                if cid=='EX1_539' and a.get('target')==o['hero']['entity_id'] and ehp>5:
                    score-=resource*1.2
            elif a['type']=='hero_power':
                affordable=[c for c in y['hand'] if c['cost']<=y['mana'] and c.get('playable')]
                if affordable and all(c['cost']<=y['mana']-y['hero_power']['cost'] for c in affordable):score+=resource*1.2
                if danger:score-=survival
        if cfg.get('secret_rules'):
            if a['type']=='play_card':
                c=hand[a['card']];cid=c['card_id'];remaining=y['mana']-c['cost']
                if cid in SECRETS:
                    # Delayed effects are discounted for avoidance; never delete enemy minions.
                    fragile=sum(m['health']<=2 and not m.get('divine_shield') for m in o['board'])
                    has_taunt=any(m.get('taunt') for m in y['board'])
                    if cid=='EX1_610':
                        score-=secret*(fragile*1.0+(1.5 if has_taunt else 0))
                        if danger and fragile:score+=secret*1.5
                    if cid=='EX1_611' and len(o['board'])>=2:
                        score-=secret*1.0
                    if cid=='EX1_554':
                        score+=secret*(2 if has_taunt and len(y['board'])<=4 else -1)
                    if cid=='EX1_533':score-=secret*(1.5 if y['board'] else 0)
                    if not o['board'] and not any(m['card_id']=='EX1_080' for m in y['board']) and not y.get('weapon'):score-=secret*2
                if cid in ('NEW1_019','EX1_531') and any(d['card_id']=='EX1_538' and d['cost']<=remaining for d in y['hand']):
                    score+=combo*min(len(o['board']),7-len(y['board'])-1)*1.5
                if cid=='EX1_538' and len(y['board'])>=6:score-=combo*2
                if cid=='EX1_066' and not o.get('weapon') and o['hero']['hero_class'] in ('WARRIOR','PALADIN','ROGUE','HUNTER'):
                    if any(d['entity_id']!=c['entity_id'] and d['type']=='MINION' and d['cost']<=y['mana'] for d in y['hand']):score-=resource*2
                if cid=='DS1_184' and any(d['cost']==y['mana'] and d['type']=='MINION' for d in y['hand']):score-=resource*2
            if a['type']=='attack':
                at,t=obj[a['attacker']],obj[a['target']]
                if is_beast(at) and len([m for m in y['board'] if is_beast(m)])==1 and t is not o['hero']:
                    dying=t['attack']>=at['health'] and not at.get('divine_shield')
                    if dying and any(c['card_id']=='EX1_539' and c['cost']<=y['mana'] for c in y['hand']):score-=combo*3
                w=y.get('weapon') or {}
                if a['attacker']==y['hero']['entity_id'] and w.get('durability')==1 and y.get('secrets'):
                    if any(c['card_id']=='EX1_536' for c in y['hand']) or ehp<=8:score+=resource*2.5
    
        out.append((score,a))
    return sorted(out,key=lambda x:x[0],reverse=True) or ranked
