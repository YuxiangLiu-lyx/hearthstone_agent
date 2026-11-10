"""Bounded exchange scoring, using only public observations and legal first actions.

Look ahead at most three actions against ONE enemy minion. This is not a lethal
solver. Random discard cannot remove board attackers; at most one burn is used.
Unknown combat triggers cause abstention. Recompute after every actual action.
"""
from evaluator import CATALOG, DEATH_VALUE, hand_body, minion_value, threat

WOLF='EX1_162'
# These minions have no combat-time mutation except the effects handled below.
SAFE=set('EX1_319 CS2_065 EX1_008 CS2_188 EX1_162 NEW1_019 EX1_066 EX1_556 EX1_019 EX1_020 EX1_046 EX1_093 EX1_067 CS2_182 CS2_179 EX1_586 EX1_110 CS2_151 CS2_152 CS2_147 EX1_058 CS2_172 CS2_120 CS2_200 EX1_032 CS2_168 CS2_171 EX1_556t EX1_110t'.split())
BURN={'EX1_308':4,'EX1_302':1,'CS2_057':4}
TOKENS={'EX1_556':('EX1_556t',2,1), 'EX1_110':('EX1_110t',4,5)}


def key(a):
    return tuple(sorted(a.items()))


def aura(board, index):
    return sum(board[j]['card_id']==WOLF and not board[j].get('silenced')
               for j in (index-1,index+1) if 0<=j<len(board))


def body(m):
    return minion_value(m)-(DEATH_VALUE.get(m['card_id'],1) if m.get('deathrattle') and not m.get('silenced') else 0)


def joint_scores(state, ranked, max_nodes=1600):
    you,opp=state['you'],state['opponent']
    if any(m['card_id'] not in SAFE and not m.get('silenced') for m in you['board']):
        return {}
    # Unsupported opponent triggers may change health/attack mid-combat.
    if any(not m.get('silenced') and set(CATALOG.get(m['card_id'],{}).get('mechanics',[])) & {'TRIGGER','ENRAGE'} for m in opp['board']):
        return {}
    board=[dict(m,base_attack=m['attack']-aura(you['board'],i)) for i,m in enumerate(you['board'])]
    hand={c['entity_id']:c for c in you['hand']}
    danger=threat(opp)+3>=you['hero']['health']+you['hero'].get('armor',0)
    face_tax=.35 if opp['hero']['health']+opp['hero'].get('armor',0)<=15 else .12
    juggler=any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in board)
    out={};nodes=0
    for target in opp['board']:
        if target.get('immune') or target.get('stealth'):
            continue
        if target['card_id'] not in SAFE and not target.get('silenced'):
            continue
        options=[a for _,a in ranked if a.get('target')==target['entity_id'] and (
            a['type']=='attack' and any(m['entity_id']==a['attacker'] for m in board)
            or a['type']=='play_card' and hand[a['card']]['card_id'] in BURN)]
        if len(options)<2:
            continue
        enemy_value=body(target)+(.8*target['attack'] if danger else 0)
        def visit(own, hp, shield, used, spell_used, cost, sequence, attack_spent):
            nonlocal nodes
            if nodes>=max_nodes:
                return
            nodes+=1
            if hp<=0:
                if len(sequence)>=2:
                    value=enemy_value-cost+1.3+.8*target.get('taunt',False)-.65*(len(sequence)-1)
                    if not target.get('taunt') and not danger:
                        value-=face_tax*attack_spent
                    k=key(sequence[0]);out[k]=max(out.get(k,-1000),value)
                return
            if len(sequence)>=3:
                return
            for a in options:
                next_own=[dict(m) for m in own];next_used=set(used)
                next_cost=cost;next_shield=shield;next_hp=hp;spent=attack_spent
                if a['type']=='attack':
                    ident=a['attacker']
                    if ident in used:
                        continue
                    index=next((i for i,m in enumerate(next_own) if m['entity_id']==ident),None)
                    if index is None:
                        continue
                    m=next_own[index];attack=m['base_attack']+aura(next_own,index)
                    if attack<=0:
                        continue
                    next_used.add(ident);spent+=attack
                    if shield:
                        next_shield=False
                    else:
                        next_hp=0 if m.get('poisonous') else hp-attack
                    retaliation=target['attack']
                    if retaliation and not m.get('immune'):
                        if m.get('divine_shield'):
                            m['divine_shield']=False;next_cost+=1.8
                        elif retaliation>=m['health'] or target.get('poisonous'):
                            if m.get('deathrattle') and not m.get('silenced') and (juggler or m['card_id'] not in TOKENS):
                                continue  # Random summon triggers / unknown deathrattle.
                            next_cost+=body(m);next_own.pop(index)
                            if m.get('deathrattle') and not m.get('silenced'):
                                cid,atk,health=TOKENS[m['card_id']]
                                next_own.insert(index,{'entity_id':-ident,'card_id':cid,'base_attack':atk,'attack':atk,'health':health})
                        else:
                            m['health']-=retaliation;next_cost+=.4*retaliation
                    next_spell=spell_used
                else:
                    if spell_used:
                        continue
                    c=hand[a['card']]
                    sd=sum(m.get('spell_damage',0) for m in own)
                    damage=BURN[c['card_id']]+sd
                    if shield:
                        next_shield=False
                    else:
                        next_hp=hp-damage
                    next_cost+=.45*c['cost']+1.1
                    if c['card_id']=='EX1_308':
                        rest=[d for d in hand.values() if d is not c]
                        if rest:
                            next_cost+=.35*sum(hand_body(d) if d['type']=='MINION' else 3 for d in rest)/len(rest)
                    if c['card_id']=='EX1_302' and next_hp<=0 and not shield:
                        next_cost-=2.5
                    next_spell=True
                visit(next_own,next_hp,next_shield,next_used,next_spell,next_cost,sequence+[a],spent)
        visit(board,target['health'],target.get('divine_shield',False),set(),False,0,[],0)
    return out
