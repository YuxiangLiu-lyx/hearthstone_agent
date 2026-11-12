"""Bounded expected public reply for one Misdirection; never a lethal proof."""
import copy,time
import tactical_model as m
from public_response import prepare_reply,attacks,attack
from race_plan import value

def transitions(s,a):
    secrets=s['you'].get('secrets',[])
    if not secrets or a['target']!=s['you']['hero']['entity_id']:
        r=attack(s,a)
        return [(1.,r)] if r is not None else None
    if [x['card_id'] for x in secrets]!=['EX1_533']:return None
    targets=[x for side in ('you','opponent') for x in s[side]['board']+[s[side]['hero']]
             if x['entity_id'] not in (a['attacker'],s['you']['hero']['entity_id']) and x['health']>0]
    if not targets:return None
    result=[]
    for target in targets:
        b=copy.deepcopy(s);y,o=b['you'],b['opponent'];y['secrets']=[]
        if (y.get('weapon') or {}).get('card_id')=='EX1_536':y['weapon']['durability']+=1
        swapped={**b,'you':o,'opponent':y};swapped['you'].setdefault('hand',[])
        r=m.transition(swapped,{**a,'target':target['entity_id']})
        # Unknown draws/terminal interruption stay outside this local projector.
        if r is None:return None
        result.append((1./len(targets),{**r,'you':r['opponent'],'opponent':r['you']}))
    return result

def reply(state,cfg,deadline,max_nodes=96):
    secrets=state['you'].get('secrets',[])
    if [x['card_id'] for x in secrets]!=['EX1_533']:return {'supported':False,'nodes':0}
    tmp=copy.deepcopy(state);tmp['you']['secrets']=[]
    initial=prepare_reply(tmp)
    if initial is None:return {'supported':False,'nodes':0}
    initial['you']['secrets']=copy.deepcopy(secrets)
    count=0;bounded=False;memo={}
    def visit(s,depth):
        nonlocal count,bounded
        if time.monotonic()>=deadline:raise TimeoutError
        raw=max(-200.,min(200.,value(s,cfg,after_response=True)))
        if depth==0 or count>=max_nodes:
            bounded=True;return raw
        key=(m.signature(s),depth)
        if key in memo:return memo[key]
        best=raw
        for a in attacks(s):
            if count>=max_nodes:bounded=True;break
            distribution=transitions(s,a);count+=len(distribution) if distribution else 1
            if distribution is None:raise ValueError('unsupported_response_branch')
            score=sum(prob*visit(x,depth-1) for prob,x in distribution)
            best=min(best,score)
        memo[key]=best;return best
    try:score=visit(initial,3)
    except (ValueError,TimeoutError):return {'supported':False,'nodes':count}
    return {'supported':True,'nodes':count,'value':score,'bounded':bounded,'visible_lethal_found':False,
            'scope':'Expected exact single-Misdirection targets and bounded observation-contingent visible attacks, no proof or hidden hand.'}
