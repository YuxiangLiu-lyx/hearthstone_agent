"""Public-observation plans; numeric ranks are heuristics, never win probabilities."""
import time
from base_policy import rank_actions, mulligan as generic_mulligan, choose as generic_choice
from state_features import CATALOG, effective_health, entities, is_beast, direct_damage

SECRETS = {'EX1_533','EX1_554','EX1_610','EX1_611'}


def facts(state):
    y,o=state['you'],state['opponent']
    incoming=sum(m['attack'] for m in o['board'] if not m.get('frozen'))+(o.get('weapon') or {}).get('attack',0)
    ready=sum(m['attack'] for m in y['board'] if m.get('can_attack'))
    return {'own_health':effective_health(y['hero']), 'enemy_health':effective_health(o['hero']),
            'enemy_board_attack':incoming, 'ready_attack_before_taunts':ready,
            'mana':y['mana'], 'enemy_taunts':sum(bool(m.get('taunt')) for m in o['board']),
            'own_secrets_in_order':[c['card_id'] for c in y.get('secrets',[])],
            'unknown_enemy_secrets':o.get('secrets_count',0),
            'opponent_evidence':state.get('public_opponent_evidence',{'tendency':'unknown'}),
            'risk_note':'Board attack is a public lower-information signal; hidden burst/removal unknown.'}


def mulligan(state):
    hand=state['you']['hand']; keep=[]; counts={}
    keeper=any(c['card_id']=='EX1_080' for c in hand)
    low=any(c['type']=='MINION' and c['cost']<=2 for c in hand)
    for c in sorted(hand,key=lambda c:(c['cost'],c['entity_id'])):
        cid=c['card_id'];good=c['type']=='MINION' and c['cost']<=2 and counts.get(cid,0)==0
        good|=cid in ('NEW1_031','EX1_536') and low and not counts.get('three',0)
        good|=cid in SECRETS and keeper and not counts.get('secret',0)
        if good:
            keep.append(c['entity_id']);counts[cid]=counts.get(cid,0)+1
            if c['cost']==3:counts['three']=1
            if cid in SECRETS:counts['secret']=1
    return {'type':'mulligan','replace':[c['entity_id'] for c in hand if c['entity_id'] not in keep]}


def choice_actions(state):
    t=next(t for t in state['legal_actions'] if t['type']=='choose')
    y,o=state['you'],state['opponent']; next_mana=min(10,y['max_mana']+1)
    def value(c):
        cid=c['card_id'];v=c.get('attack',0)+.6*c.get('health',0)
        if c['cost']<=y['mana']:v+=3
        elif c['cost']>next_mana:v-=c['cost']-next_mana+2
        if cid=='EX1_539':v=8+(effective_health(o['hero'])<=5)*9
        if cid=='EX1_534':v+=4
        if cid=='EX1_543':v+=6 if next_mana>=9 else -4
        if cid=='EX1_538':v=3*min(len(o['board']),7-len(y['board']))
        if cid in SECRETS:v=2+(cid=='EX1_610')*sum(m['health']<=2 for m in o['board'])
        return v
    return sorted([(value(c),{'type':'choose','options':[c['entity_id']]}) for c in t['options']],key=lambda x:x[0],reverse=True)


def rank(state,config,deadline=None):
    if state['phase']=='mulligan':
        a=mulligan(state) if config.get('guide_rules') else generic_mulligan(state)
        return [(1.,a),(0.,{'type':'mulligan','replace':[]})]
    if state['phase']=='choice':return choice_actions(state)
    ranked=rank_actions(state,config,deadline)
    if not config.get('guide_rules'):return ranked
    y,o=state['you'],state['opponent'];objects=entities(state)
    hand={c['entity_id']:c for c in y['hand']}; hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    dangerous=sum(m['attack'] for m in o['board'])+3>=hp
    values=[]
    for score,a in ranked:
        if deadline is not None and time.monotonic()>=deadline:break
        if a['type']=='play_card':
            c=hand[a['card']];cid=c['card_id']
            keepers=sum(m['card_id']=='EX1_080' and not m.get('silenced') for m in y['board'])
            if cid in SECRETS:
                bow=bool(y.get('weapon') and y['weapon']['card_id']=='EX1_536')
                score=1+2.5*keepers+1.5*bow
                if cid=='EX1_610':score+=sum(2.5 if m['health']<=2 and not m.get('divine_shield') else .4 for m in o['board'])
                elif cid=='EX1_611':score+=min((m['attack']*.7+m['cost']*.2 if 'cost' in m else m['attack']*.7 for m in o['board']),default=0)
                elif cid=='EX1_554':score+=min(3,7-len(y['board']))*1.6 if y['board'] and o['board'] else 0
                elif cid=='EX1_533':score+=2 if o['board'] else -2
                if config.get('risk_summaries') and cid=='EX1_611' and any(d['card_id']=='EX1_610' and d['cost']+c['cost']<=y['mana'] for d in y['hand']):
                    # Engine fixture: Freezing first cancels the later Explosive trigger.
                    score-=4 if any(m['health']<=2 for m in o['board']) else 0
            if cid=='EX1_080':score+=2*any(d['card_id'] in SECRETS and d['cost']<=y['mana']-c['cost'] for d in y['hand'])
            if cid in ('NEW1_019','EX1_531'):
                score+=4*any(d['card_id']=='EX1_538' and d['cost']<=y['mana']-c['cost'] for d in y['hand'])
            if cid=='DS1_070' and a.get('target'):
                m=objects[a['target']];score+=4+2*bool(m.get('can_attack'))+3*dangerous
            if cid=='EX1_066':
                score+=3*(o.get('weapon') or {}).get('durability',0)
            if cid=='EX1_617':
                score=sum(m['attack']+m['health']*.6+2*bool(m.get('taunt')) for m in o['board'])/max(1,len(o['board']))-2
                if dangerous:score+=2
            if cid=='DS1_184':score=2.5+(not any(d.get('playable') and d['type']=='MINION' for d in y['hand']))*3
            if cid=='EX1_539' and a.get('target')==o['hero']['entity_id'] and not any(is_beast(m) for m in y['board']) and ehp>3:
                score-=3
        if a['type']=='attack' and a['attacker']==y['hero']['entity_id']:
            w=y.get('weapon') or {}
            if w.get('card_id')=='EX1_536' and w.get('durability')==1 and y.get('secrets') and ehp>y['hero']['attack'] and not dangerous:
                score-=2.5
        values.append((score,a))
    return sorted(values,key=lambda x:x[0],reverse=True) or ranked
