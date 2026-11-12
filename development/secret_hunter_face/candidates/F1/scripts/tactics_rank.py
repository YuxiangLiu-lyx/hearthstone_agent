"""Explicit legal-action hints for combos, protection, and opening curve."""
from state_features import is_beast,effective_health,entities
from evaluator import minion_value,threat
from race_plan import burst


def mulligan(state):
    hand=state['you']['hand'];hc=state['opponent']['hero']['hero_class']
    pressure=hc in ('HUNTER','WARLOCK','PALADIN','SHAMAN')
    coin=len(hand)>=4
    ones=[c for c in hand if c['card_id'] in ('EX1_080','EX1_029')]
    two=[c for c in hand if c['type']=='MINION' and c['cost']==2]
    keeper=any(c['card_id']=='EX1_080' for c in ones)
    keep=[];seen=set()
    for c in sorted(ones,key=lambda c:c['card_id']!='EX1_080'):
        if c['card_id'] not in seen:keep.append(c['entity_id']);seen.add(c['card_id'])
    # Two-drop support matters more than collecting several copies of a combo piece.
    priority={'NEW1_019':5,'EX1_531':3,'EX1_066':3,'EX1_162':2}
    for c in sorted(two,key=lambda c:-priority.get(c['card_id'],0)):
        if c['card_id'] in seen or sum(x['entity_id'] in keep and x['cost']==2 for x in hand)>= (2 if coin and not ones else 1):continue
        keep.append(c['entity_id']);seen.add(c['card_id'])
    low=bool(keep)
    secrets=[c for c in hand if c['card_id'] in ('EX1_610','EX1_611','EX1_554','EX1_533')]
    secrets.sort(key=lambda c:({'EX1_610':4 if pressure else 1,'EX1_611':3,'EX1_554':2,'EX1_533':0}[c['card_id']]),reverse=True)
    if secrets and (keeper or (pressure and low and secrets[0]['card_id']=='EX1_610')):keep.append(secrets[0]['entity_id'])
    threes=[c for c in hand if c['card_id'] in ('EX1_536','NEW1_031','EX1_538')]
    for c in sorted(threes,key=lambda c:c['card_id']!='EX1_536'):
        hounds_ok=pressure and ('NEW1_019' in seen or 'EX1_531' in seen) and (ones or coin)
        if low and (c['card_id']!='EX1_538' or hounds_ok):keep.append(c['entity_id']);break
    return {'type':'mulligan','replace':[c['entity_id'] for c in hand if c['entity_id'] not in keep]}


def adjust(state,ranked,cfg):
    y,o=state['you'],state['opponent'];obj=entities(state);hand={c['entity_id']:c for c in y['hand']}
    hp=effective_health(y['hero']);ehp=effective_health(o['hero']);danger=threat(o)+3>=hp
    burn=burst(state);weight=cfg.get('combo_weight',1);protection=cfg.get('protection_weight',.5)
    hounds=next((c for c in y['hand'] if c['card_id']=='EX1_538'),None)
    beasts=[m for m in y['board'] if is_beast(m)]
    sacrifices=[m for m in beasts if m.get('can_attack') and any(e['attack']>=m['health'] and e['attack']>0 for e in o['board'])]
    out=[]
    for score,a in ranked:
        if score>=100000:out.append((score,a));continue
        if a['type']=='play_card':
            c=hand[a['card']];cid=c['card_id']
            if cid in ('EX1_531','NEW1_019') and hounds and c['cost']+hounds['cost']<=y['mana'] and len(y['board'])<=5:
                score+=weight*min(3,len(o['board']))*(2 if cid=='EX1_531' else 1.5)
            if cid=='EX1_531' and c['cost']<=y['mana'] and sacrifices:score+=weight*min(3,len(sacrifices))*2
            if cid=='EX1_538' and len(o['board'])<=1 and not danger:score-=3*weight
            if cid=='EX1_610' and sum(m['health']<=2 and not m.get('divine_shield') for m in o['board'])>=2:
                score+=cfg.get('explosive_priority',2)
        elif a['type']=='attack':
            at=obj[a['attacker']];target=obj[a['target']]
            if at['card_id']=='EX1_531' and not at.get('silenced'):
                score-=weight*2*sum(m['entity_id']!=at['entity_id'] for m in sacrifices)
            if a['target']==o['hero']['entity_id']:
                if not danger and ehp-at['attack']<=burn:score+=cfg.get('setup_rank_bonus',5)
                if cfg.get('face_preference'):
                    from face_preference import attack_bonus
                    score += attack_bonus(state, a, cfg, at)
            else:
                kill=not target.get('divine_shield') and (at['attack']>=target['health'] or at.get('poisonous'))
                dies=not at.get('divine_shield') and target['attack']>=at['health']
                if kill:
                    taunts=[m for m in y['board'] if m.get('taunt') and not m.get('stealth')]
                    victims=[m for m in (taunts or y['board']) if m['entity_id']!=at['entity_id'] and not m.get('stealth') and not m.get('divine_shield') and target['attack']>=m['health']]
                    saved=max((max(0,minion_value(m)-minion_value(target)) for m in victims),default=0)
                    score+=protection*saved
                if dies and is_beast(at) and len(beasts)==1 and any(c['card_id']=='EX1_539' and c['cost']<=y['mana'] for c in y['hand']):score-=2*weight
        out.append((score,a))
    return sorted(out,key=lambda x:x[0],reverse=True)
