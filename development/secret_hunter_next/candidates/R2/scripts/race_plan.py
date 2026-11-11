"""Public hand-based next-turn clocks and role-sensitive end-state evaluation."""
from functools import lru_cache
from state_features import effective_health,is_beast
from evaluator import minion_value,threat


@lru_cache(maxsize=1024)
def hand_damage(cards,mana,beast,slots):
    # Tiny knapsack: spell damage plus reusable power, with an optional Beast setup.
    # No future draw, random Huffer, or surviving board is assumed by the lower scenario.
    states={(0,beast):0}
    for cid,cost,kind in cards:
        updated=dict(states)
        for (spent,active),damage in states.items():
            if spent+cost>mana:continue
            if cid=='EX1_539':key=(spent+cost,active);gain=5 if active else 3
            elif cid=='DS1_185':key=(spent+cost,active);gain=2
            elif kind and slots>0:key=(spent+cost,True);gain=0
            else:continue
            updated[key]=max(updated.get(key,-1),damage+gain)
        states=updated
    return max(d+(2 if mana-spent>=2 else 0) for (spent,_),d in states.items())


def burst(state,assume_beast=False):
    y=state['you'];mana=min(10,y['max_mana']+1)
    # Setup minions precede damage spells in this hypothetical plan.
    cards=tuple(sorted(((c['card_id'],c['cost'],bool(c.get('type')=='MINION' and is_beast(c))) for c in y['hand']),key=lambda c:not c[2]))
    return hand_damage(cards,mana,assume_beast,7-len(y['board']))


def value(s,cfg,after_response=False):
    y,o=s['you'],s['opponent'];hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    if ehp<=0:return 1e6
    if hp<=0:return -1e6
    incoming=threat(o);taunts=any(m.get('taunt') and not m.get('stealth') for m in y['board'])
    safe=hp>incoming+cfg.get('hidden_burst_buffer',3) or (after_response and hp>cfg.get('hidden_burst_buffer',3))
    burn=burst(s,False);beast_burn=burst(s,any(is_beast(m) for m in y['board']))
    board_attack=sum(m['attack'] for m in y['board'] if not m.get('frozen'))
    enemy_taunts=any(m.get('taunt') and not m.get('stealth') for m in o['board'])
    weapon=y.get('weapon') or {}
    attack_clock=(board_attack+weapon.get('attack',0)) if not enemy_taunts else 0
    face=cfg.get('turn_face',1.116)
    score=cfg.get('turn_board',1.094)*(sum(minion_value(m) for m in y['board'])-sum(minion_value(m) for m in o['board']))
    score-=face*ehp
    score+=.6*max(0,10-ehp)
    if safe:score+=cfg.get('race_face_bonus',.55)*max(0,beast_burn+attack_clock-ehp)
    score+=.2*hp+cfg.get('turn_hand',.973)*len(y['hand'])
    score+=.6*weapon.get('attack',0)*weapon.get('durability',0)
    # After the attack response, reserve covers unknown hand burst instead of charging attacks twice.
    pressure=cfg.get('hidden_burst_buffer',3) if after_response else incoming+3
    score-=cfg.get('turn_risk',3.273)*max(0,pressure-hp)
    if not after_response and not taunts and incoming>=hp and not y.get('secrets'):score-=10000
    if safe:
        if ehp<=burn:score+=cfg.get('hand_clock_bonus',15)
        elif ehp<=beast_burn+.65*attack_clock:score+=cfg.get('board_clock_bonus',5)
    # A trap is a contingent resource; attack-response search realizes only tested triggers.
    for c in y.get('secrets',[]):
        v=.7
        if c['card_id']=='EX1_610':v+=sum(1.1 if m['health']<=2 and not m.get('divine_shield') else .2 for m in o['board'])
        if c['card_id']=='EX1_611':v+=min((.4*m['attack'] for m in o['board']),default=0)
        if c['card_id']=='EX1_554' and y['board']:v+=.7*min(3,7-len(y['board']))
        score+=cfg.get('trap_resource',1.3)*v
    if cfg.get('generator_value'):
        score -= cfg['generator_value'] * sum(min(3, x['health']) for x in o['board'] if x['card_id']=='EX1_597' and not x.get('silenced'))
    return score


def describe(state,cfg):
    y,o=state['you'],state['opponent'];hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    incoming=threat(o);burn=burst(state)
    return {'own_ehp':hp,'enemy_ehp':ehp,'visible_incoming_before_taunts':incoming,
      'next_turn_hand_damage_no_surviving_beast':burn,
      'next_turn_hand_damage_if_beast_survives':burst(state,any(is_beast(m) for m in y['board'])),
      'role':'defend' if incoming+cfg.get('hidden_burst_buffer',3)>=hp else 'close' if ehp<=burn+4 else 'develop_and_trade',
      'uncertainty':'No future draw or hidden heal/removal is known. Hand clock is a conditional setup estimate, not a forced next-turn lethal.'}
