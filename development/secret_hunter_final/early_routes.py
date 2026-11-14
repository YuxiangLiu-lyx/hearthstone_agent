"""Small reactive turn interventions. Reads public observations only.

These are offline route programs, not recommendations. Recheck legality after
every random summon/Knife Juggler result and preserve concrete positions/order.
"""
from action_validator import expand

ROUTES=('develop','hold_coin','coin_bow','coin_minion','kill_juggler','kill_wolf',
        'kill_amani','cheap_defense','trap','face','power','hounds_trade','bank_tail')

def features(s):
    y,o=s['you'],s['opponent'];board=o['board']
    return {'mana':y['max_mana'],'current_mana':y['mana'],'own_empty':int(not y['board']),
            'incoming':sum(m['attack'] for m in board),'enemy_hand':o['hand_size'],
            'own_low_health':sum(m['health']==1 for m in y['board']),
            'enemy_space':7-len(board),'coin':int(any(c['card_id']=='GAME_005' for c in y['hand'])),
            'juggler':int(any(m['card_id']=='NEW1_019' for m in board)),
            'wolf':int(any(m['card_id']=='EX1_162' for m in board)),
            'amani':int(any(m['card_id']=='EX1_393' and m['health']==m['max_health'] for m in board)),
            'health':y['hero']['health']+y['hero'].get('armor',0),
            'opponent_hunter':int(o['hero']['hero_class']=='HUNTER'),
            'our_secret':int(bool(y.get('secrets')))}

def propose(s,route,memory,baseline=None):
    if s.get('phase')!='main':return None
    y,o=s['you'],s['opponent'];actions=expand(s,positions=False)
    hand={c['entity_id']:c for c in y['hand']}
    bodies={m['entity_id']:m for side in (y,o) for m in side['board']+[side['hero']]}
    plays=[a for a in actions if a['type']=='play_card']
    def play(cid):return next((a for a in plays if hand[a['card']]['card_id']==cid),None)
    coin=play('GAME_005')
    minions=[a for a in plays if hand[a['card']]['type']=='MINION' and 'target' not in a]
    def develop():
        return max(minions,key=lambda a:(hand[a['card']]['cost'],hand[a['card']].get('attack',0)+hand[a['card']].get('health',0)),default=None)
    if route=='develop':return develop()
    if route=='preserve_burn':
        expensive=baseline and ((baseline.get('card') in hand and hand[baseline['card']]['card_id'] in ('EX1_539','EX1_617')) or
                               (baseline.get('attacker')==y['hero']['entity_id']))
        if expensive:return develop() or next((a for a in actions if a['type']=='hero_power'),{'type':'end_turn'})
        return None
    if route=='bow_amani':
        amani={m['entity_id'] for m in o['board'] if m['card_id']=='EX1_393'}
        if not amani:return None
        a=next((a for a in actions if a['type']=='attack' and a['attacker']==y['hero']['entity_id'] and a['target'] in amani
                and y['hero']['health']+y['hero'].get('armor',0)>bodies[a['target']]['attack']),None)
        return a or (play('EX1_536') if not y.get('weapon') else None)
    if route=='hold_coin':
        if baseline and baseline.get('card') in hand and hand[baseline['card']]['card_id']=='GAME_005':
            return develop() or {'type':'end_turn'}
        return None
    if route in ('coin_bow','coin_minion'):
        if memory.get('done'):return None
        target=memory.get('target')
        if target:
            a=next((a for a in plays if a['card']==target and 'target' not in a),None)
            if a:memory['done']=True;return a
            return None
        desired=[c for c in y['hand'] if c['cost']==y['mana']+1 and
                 (c['card_id']=='EX1_536' if route=='coin_bow' else c['type']=='MINION')]
        if coin and desired and (route=='coin_bow' or len(y['board'])<7):
            c=max(desired,key=lambda c:(c.get('attack',0)+c.get('health',0),c['card_id']))
            memory['target']=c['entity_id'];return coin
        return None
    target_id={'kill_juggler':'NEW1_019','kill_wolf':'EX1_162','kill_amani':'EX1_393'}.get(route)
    if target_id or route in ('cheap_defense','hounds_trade'):
        if route=='hounds_trade' and not memory.get('hounds'):
            a=play('EX1_538')
            if a:memory['hounds']=True;return a
        targets=[m for m in o['board'] if m['card_id']==target_id] if target_id else list(o['board'])
        attacks=[a for a in actions if a['type']=='attack' and a['target'] in {m['entity_id'] for m in targets}
                 and a['attacker']!=y['hero']['entity_id']]
        if route=='cheap_defense':
            f=features(s)
            if memory.get('done') or f['incoming']+3<f['health']:return None
            attacks=[a for a in attacks if bodies[a['attacker']]['card_id']=='EX1_538t' and
                     bodies[a['target']]['health']<=bodies[a['attacker']]['attack'] and not bodies[a['target']].get('divine_shield')]
        if not attacks:return None
        def priority(a):
            src,t=bodies[a['attacker']],bodies[a['target']]
            return (t['attack'] if not target_id else 0,
                    int(t['health']<=src['attack'] and not t.get('divine_shield')),
                    -src['attack']-src['health'], -a['attacker'])
        result=max(attacks,key=priority)
        if route=='cheap_defense':memory['done']=True
        return result
    if route=='trap':return play('EX1_610')
    if route=='power':return next((a for a in actions if a['type']=='hero_power'),None)
    if route=='face':
        return next((a for a in actions if a['type']=='attack' and a['target']==o['hero']['entity_id']),None)
    if route=='bank_tail':
        if not memory.get('first'):
            memory['first']=True;return baseline
        return {'type':'end_turn'}
    return None
