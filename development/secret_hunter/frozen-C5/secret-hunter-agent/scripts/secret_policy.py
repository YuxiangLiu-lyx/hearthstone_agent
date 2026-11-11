"""Public-observation plans; numeric ranks are heuristics, never win probabilities."""
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


def rank(state,config):
    if state['phase']=='mulligan':
        a=mulligan(state) if config.get('guide_rules') else generic_mulligan(state)
        return [(1.,a),(0.,{'type':'mulligan','replace':[]})]
    if state['phase']=='choice':return choice_actions(state)
    ranked=rank_actions(state,config)
    if not config.get('guide_rules'):return ranked
    y,o=state['you'],state['opponent'];objects=entities(state)
    hand={c['entity_id']:c for c in y['hand']}; hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    dangerous=sum(m['attack'] for m in o['board'])+3>=hp
    values=[]
    for score,a in ranked:
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
    return sorted(values,key=lambda x:x[0],reverse=True)


def action_risk(state,a):
    y,o=state['you'],state['opponent'];objects=entities(state)
    after_hp=effective_health(y['hero']);cost=0;damage=0;note=[]
    if a['type']=='attack':
        source,target=objects[a['attacker']],objects[a['target']]
        if source is y['hero']:after_hp-=target['attack']
        if target is o['hero']:damage=source['attack']
        if target.get('deathrattle'):note.append('Deathrattle may change damage or board; raw trade estimate incomplete.')
    elif a['type']=='play_card':
        c=next(c for c in y['hand'] if c['entity_id']==a['card']);cost=c['cost']
        if a.get('target')==o['hero']['entity_id']:damage=direct_damage(c,state)
        if c['card_id'] in SECRETS:note.append('Delayed trigger; opponent may bait or avoid it.')
        if c['card_id'] in ('NEW1_031','EX1_617','EX1_538'):note.append('Random/trigger interactions may alter continuation.')
    elif a['type']=='hero_power':cost=y['hero_power']['cost'];damage=2
    incoming=sum(m['attack'] for m in o['board'])+(o.get('weapon') or {}).get('attack',0)
    if after_hp<=incoming+4:note.append('Possible retaliation risk: remaining actions, Taunts, Secrets and hidden burn require judgment.')
    return {'direct_face_damage_before_secrets':damage,'mana_left':y['mana']-cost,
            'hero_health_after_raw_combat':after_hp,'enemy_current_board_attack':incoming,'risks':note}


def label(state,a):
    if a['type']=='play_card':
        c=next(c for c in state['you']['hand'] if c['entity_id']==a['card'])
        return 'deploy_secret' if c['card_id'] in SECRETS else 'develop_or_use_'+c['name']
    if a['type']=='attack':return 'pressure' if a['target']==state['opponent']['hero']['entity_id'] else 'trade'
    return a['type']


def analyze(state,config,deep=False):
    ranked=rank(state,config);lethal={'status':'unknown','guaranteed':False}
    if state['phase']=='main':
        from lethal_planner import search
        lethal=search(state,budget_s=.7 if deep else config.get('search_budget_s',.15),
                      max_nodes=6000 if deep else config.get('search_nodes',1600))
        lethal['status']='proven_within_effect_coverage' if lethal['guaranteed'] else ('unknown' if lethal['supported'] else 'unsupported')
        if lethal['guaranteed']:ranked=[(1000000.,lethal['first_action'])]+ranked
    unique=[];seen=set()
    for score,a in ranked:
        key=tuple((k,str(v)) for k,v in a.items() if k!='position')
        if key not in seen:unique.append((score,a));seen.add(key)
    if config.get('risk_summaries') and state['phase']=='main':
        # Preserve the default, then expose different plans rather than five similar trades.
        diverse=unique[:1];used={label(state,unique[0][1])} if unique else set()
        for item in unique[1:]:
            tag=label(state,item[1])
            if tag not in used and item[0]>-10:diverse.append(item);used.add(tag)
            if len(diverse)>=5:break
        for item in unique:
            if item not in diverse:diverse.append(item)
            if len(diverse)>=5:break
        unique=diverse
    candidates=[{'id':i,'action':a,'plan':label(state,a) if state['phase']=='main' else state['phase'],
                 'heuristic_score':round(score,3)} for i,(score,a) in enumerate(unique[:5])]
    extra={}
    if config.get('risk_summaries') and state['phase']=='main':
        for c in candidates:c['consequences']=action_risk(state,c['action'])
        from next_turn import burn_reach
        y=state['you'];nm=min(10,y['max_mana']+1)
        extra['next_turn_burn']={'mana':nm,'without_surviving_beast':burn_reach(y['hand'],nm,False,slots=7-len(y['board'])),
                                 'with_surviving_beast':burn_reach(y['hand'],nm,any(is_beast(m) for m in y['board']),slots=7-len(y['board'])),
                                 'conditions':'No draw, healing, secrets, mana disruption or unexpected deaths; estimate, not forced win.'}
        if deep:
            from lethal_planner import probabilistic_lethal
            extra['companion_branches']=probabilistic_lethal(state,budget_s=.6,max_nodes=4500)
    return {'candidates':candidates,'default_id':0,'lethal':lethal,
            'facts':facts(state) if state['phase']=='main' else {},
            'estimates_note':'Ranks and future plans are estimates; no calibrated win probabilities.',
            'model_needed':config.get('model_authority',True) and len(candidates)>1 and not lethal['guaranteed'],**extra}


def decide(state,config):
    return analyze(state,config)['candidates'][0]['action']
