"""21 bounded, interpretable coefficients trained offline against a frozen pool.

Secret potential and exposed attack are estimates, not simulated future events.
No hidden cards, real RNG, deck order, or opponent identity enter these features.
"""
from evaluator import DEATH_VALUE, THREATS, threat
from state_features import effective_health, is_beast

DEFAULT = dict(own_attack=1.3675, own_health=.7111, enemy_attack=1.3675,
 enemy_health=.7111, shield=1.9692, taunt=1.2034, stealth=.547,
 windfury=.547, poison=2.188, death=1.094, engine=1.094,
 face=1.116, hero_health=.2, hand=.973, weapon=.6, risk=3.273,
 secret=1.0, exposure=.3, beast=.2, mana=.05, finish=.6)


def secret_potential(s):
    y,o=s['you'],s['opponent']; value=0.0
    for c in y.get('secrets', []):
        cid=c['card_id'];v=.6
        if cid=='EX1_610':
            v += sum(.7 if m['health']<=2 and not m.get('divine_shield') else .1 for m in o['board'])
        elif cid=='EX1_611':v += min((.35*m['attack'] for m in o['board']),default=0)
        elif cid=='EX1_554':v += .45*min(3,7-len(y['board'])) if y['board'] and o['board'] else 0
        elif cid=='EX1_533':v += .6 if o['board'] else 0
        v += .6 if (y.get('weapon') or {}).get('card_id')=='EX1_536' else 0
        value += v
    return value


def exposed_attack(s):
    """Greedy attack-capacity estimate after taunt blocks; never a lethal proof.

Includes shields and attack overkill. Ignores hidden removal, buffs, Secrets and
deathrattles, so use only as a soft exposure feature. Frozen bodies are excluded.
    """
    y,o=s['you'],s['opponent']
    attacks=sorted([m['attack'] for m in o['board'] if not m.get('frozen')
                    for _ in range(2 if m.get('windfury') else 1)] +
                   ([(o.get('weapon') or {}).get('attack',0)] if o.get('weapon') else []))
    for t in sorted((m for m in y['board'] if m.get('taunt') and not m.get('stealth')),key=lambda m:m['health']):
        if t.get('divine_shield') and attacks:attacks.pop(0)
        left=t['health']
        while left>0 and attacks:
            k=next((i for i,a in enumerate(attacks) if a>=left),len(attacks)-1)
            left-=attacks.pop(k)
        if left>0:return 0
    return sum(attacks)


def evaluate(s,cfg):
    y,o=s['you'],s['opponent'];hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    if ehp<=0:return 1000000
    if hp<=0:return -1000000
    w=cfg.get('weights',DEFAULT)
    def body(m,own):
        v=w['own_attack' if own else 'enemy_attack']*m['attack']
        v+=w['own_health' if own else 'enemy_health']*m['health']
        for flag in ('shield','taunt','stealth','poison'):
            key={'shield':'divine_shield','poison':'poisonous'}.get(flag,flag)
            v+=w[flag]*bool(m.get(key))
        v+=w['windfury']*m['attack']*bool(m.get('windfury'))
        if not m.get('silenced'):
            v+=w['engine']*THREATS.get(m['card_id'],0)
            if m.get('deathrattle'):v+=w['death']*DEATH_VALUE.get(m['card_id'],1)
        return v
    incoming=threat(o)
    exposed=exposed_attack(s) if cfg.get('response_exposure') else incoming
    score=sum(body(m,True) for m in y['board'])-sum(body(m,False) for m in o['board'])
    score-=(w['face']+(w['finish'] if ehp<=10 else 0))*ehp
    score+=w['hero_health']*hp+w['hand']*len(y['hand'])
    weapon=y.get('weapon') or {}
    score+=w['weapon']*weapon.get('attack',0)*weapon.get('durability',0)
    score-=w['risk']*max(0,exposed-hp+4)
    score-=w['exposure']*exposed if cfg.get('response_exposure') else 0
    score+=w['secret']*secret_potential(s)
    score+=w['beast']*min(2,sum(is_beast(m) for m in y['board']))*any(c['card_id']=='EX1_539' for c in y['hand'])
    score-=w['mana']*y['mana']
    # Existing Secrets cannot be assumed to prevent visible open-board lethal.
    if not any(m.get('taunt') and not m.get('stealth') for m in y['board']) and incoming>=hp:score-=10000
    return score
