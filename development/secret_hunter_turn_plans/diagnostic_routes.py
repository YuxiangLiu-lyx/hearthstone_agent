"""Public reactive interventions for one known Amani turn, used offline only."""


def override(state,route,memory,legal):
    you,foe=state['you'],state['opponent']
    def play(card_id):
        ids={c['entity_id'] for c in you['hand'] if c['card_id']==card_id}
        return next((a for a in legal if a['type']=='play_card' and a['card'] in ids),None)
    def attack(attacker_ids,target_ids):
        return next((a for a in legal if a['type']=='attack' and a['attacker'] in attacker_ids
                     and a['target'] in target_ids),None)
    hounds={m['entity_id'] for m in you['board'] if m['card_id']=='EX1_538t'}
    amani={m['entity_id'] for m in foe['board'] if m['card_id']=='EX1_393'}
    if route=='diagnostic_cheap_trade_highmane' and not memory.get('cheap_trade'):
        # One Hound removes a one-attack minion. Remaining decisions use the
        # observed board, so no random result is assumed in advance.
        small={m['entity_id'] for m in foe['board'] if m['health']==1 and m['attack']==1
               and not m.get('divine_shield') and not m.get('deathrattle')}
        action=attack(hounds,small)
        memory['cheap_trade']=True
        if action:return action
    if route in ('diagnostic_highmane_face','diagnostic_cheap_trade_highmane'):
        action=play('EX1_534')
        if action:return action
        return attack(hounds,{foe['hero']['entity_id']})
    if route=='diagnostic_companion' and not memory.get('companion_played'):
        action=play('NEW1_031')
        if action:memory['companion_played']=True;return action
    if route=='diagnostic_bow_amani' and amani:
        action=attack({you['hero']['entity_id']},amani)
        if action:return action
        if not you.get('weapon'):return play('EX1_536')
    return None
