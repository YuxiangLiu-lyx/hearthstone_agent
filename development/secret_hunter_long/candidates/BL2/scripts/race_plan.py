"""Public hand-based next-turn clocks and role-sensitive end-state evaluation."""
from functools import lru_cache
from state_features import effective_health,is_beast
from evaluator import minion_value,threat


@lru_cache(maxsize=1024)
def hand_damage(cards,mana,beast,slots,charge_open=True,power_cost=2):
    # Track actual board slots and mana; Krush damage belongs to a new minion,
    # so a frozen friendly hero does not prevent its charge attack.
    states={(0,beast,0):0}
    for cid,cost,kind in cards:
        updated=dict(states)
        for (spent,active,used),damage in states.items():
            if spent+cost>mana:continue
            gain=0;next_active=active;next_used=used
            if cid=='EX1_539':gain=5 if active else 3
            elif cid=='DS1_185':gain=2
            elif kind and used<slots:
                next_active=True;next_used+=1
                if cid=='EX1_543' and charge_open:gain=8
            else:continue
            key=(spent+cost,next_active,next_used)
            updated[key]=max(updated.get(key,-1),damage+gain)
        states=updated
    return max(d+(2 if mana-spent>=power_cost else 0) for (spent,_,_),d in states.items())


def burst(state,assume_beast=False):
    y,o=state['you'],state['opponent']
    mana=max(0,min(10,y['max_mana']+1)-y.get('overload_next_turn',0))
    cards=tuple(sorted(((c['card_id'],c['cost'],bool(c.get('type')=='MINION' and is_beast(c))) for c in y['hand']),key=lambda c:not c[2]))
    charge_open=not any(m.get('taunt') and not m.get('stealth') for m in o['board'])
    return hand_damage(cards,mana,assume_beast,7-len(y['board']),charge_open,y['hero_power'].get('cost',2))


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
    attack_clock=(board_attack+(weapon.get('attack',0) if not y['hero'].get('frozen') else 0)) if not enemy_taunts else 0
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
    from reply_features import value_adjustment
    return score + value_adjustment(s, cfg, after_response)


def describe(state,cfg):
    y,o=state['you'],state['opponent'];hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    incoming=threat(o);burn=burst(state)
    return {'own_ehp':hp,'enemy_ehp':ehp,'visible_incoming_before_taunts':incoming,
      'next_turn_hand_damage_no_surviving_beast':burn,
      'next_turn_hand_damage_if_beast_survives':burst(state,any(is_beast(m) for m in y['board'])),
      'role':'defend' if incoming+cfg.get('hidden_burst_buffer',3)>=hp else 'close' if ehp<=burn+4 else 'develop_and_trade',
      'uncertainty':'No future draw or hidden heal/removal is known. Hand clock is a conditional setup estimate, not a forced next-turn lethal.'}
