"""Small deterministic whole-turn alternatives; no hidden-card sampling online."""
import json
import time
import tactical_model as model
from actions import expand
from race_plan import value
from evaluator import minion_value


def context(s):
    if s.get('phase')!='main':return []
    y,o=s['you'],s['opponent'];enemy={m['card_id'] for m in o['board']}
    available={c['card_id'] for c in y['hand'] if c['cost']<=y['mana']}
    types=[]
    if ('EX1_610' in {c['card_id'] for c in y.get('secrets',[])} or 'EX1_610' in available) and any(m.get('deathrattle') for m in o['board']):types.append('trap')
    if 'NEW1_019' in enemy or 'EX1_162' in enemy:types.append('knife_wolf')
    if 'EX1_393' in enemy:types.append('amani')
    return types


def public_features(s):
    y,o=s['you'],s['opponent']
    mana=min(10,o.get('max_mana',0)+1)
    resources=min(o.get('hand_size',0),7-len(o['board']),max(0,mana//2))
    vulnerable=sum(m['health']<=2 for m in y['board'])
    knives=sum(m['card_id']=='NEW1_019' and not m.get('silenced') for m in o['board'])
    wolves=sum(m['card_id']=='EX1_162' and not m.get('silenced') for m in o['board'])
    incoming=sum(m['attack'] for m in o['board'])+(o.get('weapon') or {}).get('attack',0)
    amani=any(m['card_id']=='EX1_393' and not m.get('silenced') and m['health']==m['max_health'] for m in o['board'])
    coil_window=amani and o['hero']['hero_class']=='WARLOCK' and mana>=1 and o.get('hand_size',0)>0
    taunt=any(m.get('taunt') for m in y['board'])
    return {'knife_potential':knives*resources*(1+.35*vulnerable),
            'wolf_pressure':wolves*min(2,max(0,len(o['board'])-1)),
            'amani_window':float(coil_window and not taunt and incoming+3>=y['hero']['health']+y['hero'].get('armor',0)),
            'retained_burn':sum(c['card_id']=='EX1_539' for c in y['hand']),
            'keeper_board':sum(m['card_id']=='EX1_080' for m in y['board'])}


def score(s,cfg,route='balanced'):
    v=value(s,cfg);f=public_features(s);o=s['opponent'];y=s['you']
    weights=cfg.get('route_weights',{})
    v-=weights.get('knife',0)*f['knife_potential']
    v-=weights.get('amani',0)*f['amani_window']
    v+=weights.get('reserve',0)*f['retained_burn']
    target={'kill_juggler':'NEW1_019','kill_wolf':'EX1_162','bow_amani':'EX1_393','trade_amani':'EX1_393'}.get(route)
    if target:v-=30*sum(m['card_id']==target for m in o['board'])
    if route=='preserve':v+=4*f['retained_burn']+2*(y.get('weapon') or {}).get('durability',0)
    if route=='keeper':v+=12*f['keeper_board']
    if route=='highmane':v+=25*sum(m['card_id']=='EX1_534' for m in y['board'])
    if route=='taunt':v+=16*sum(bool(m.get('taunt')) for m in y['board'])
    if route=='face':v-=3*o['hero']['health']
    return v


def generate(state,cfg,deadline,route='balanced'):
    if not model.supported(state):return {'supported':False,'plans':[],'nodes':0}
    initial=model.prepare({**state,'planning_mode':'response'})
    endpoints={model.signature(initial):(score(initial,cfg,route),initial,[])}
    frontier=[(initial,[])];seen=set(endpoints);nodes=0
    for depth in range(8):
        following=[]
        for current,line in frontier:
            choices=expand(state,positions=False) if not line else model.options(current)
            for a in choices:
                if a['type'] in ('end_turn','concede'):continue
                if time.monotonic()>=deadline or nodes>=cfg.get('route_nodes',220):break
                if route=='bow_amani' and a['type']=='play_card' and next((c['card_id'] for c in current['you']['hand'] if c['entity_id']==a.get('card')),None)=='EX1_539':continue
                successor=model.transition(current,a);nodes+=1
                if successor is None:continue
                k=model.signature(successor)
                if k in seen:continue
                seen.add(k);path=line+[a];v=score(successor,cfg,route)
                endpoints[k]=(v,successor,path);following.append((v,successor,path))
            if time.monotonic()>=deadline or nodes>=cfg.get('route_nodes',220):break
        if not following or time.monotonic()>=deadline or nodes>=cfg.get('route_nodes',220):break
        following.sort(key=lambda x:x[0],reverse=True)
        frontier=[(s,line) for _,s,line in following[:cfg.get('route_width',6)]]
    plans=[]
    for v,s,line in sorted(endpoints.values(),key=lambda x:x[0],reverse=True)[:6]:
        plans.append({'value':v,'state':s,'sequence':line+[{'type':'end_turn'}],'features':public_features(s)})
    return {'supported':True,'plans':plans,'nodes':nodes}


def choose(state,cfg,deadline,route='balanced'):
    result=generate(state,cfg,deadline,route)
    if not result['plans']:return None,result
    if route=='balanced' and 'trap' in context(state):
        from public_response import worst_reply
        evaluated=[]
        for p in result['plans'][:4]:
            if time.monotonic()>=deadline:break
            reply=worst_reply(p['state'],cfg,deadline,32)
            if not reply['supported']:continue
            evaluated.append((.15*p['value']+.85*reply['value'],p))
        if len(evaluated)==min(4,len(result['plans'])):
            chosen=max(evaluated,key=lambda pair:pair[0])[1]
        else:chosen=result['plans'][0]
    else:chosen=result['plans'][0]
    return chosen,result
