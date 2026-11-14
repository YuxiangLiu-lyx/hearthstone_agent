"""Bounded public-effect turn search; unsupported branches retain the ranked action."""
import copy,json,time
from action_validator import legal
from state_features import effective_health,is_beast
from evaluator import minion_value,threat
import tactical_model as model


def value(s,cfg):
    if cfg.get('race_plan'):
        from race_plan import value as race_value
        return race_value(s,cfg)
    y,o=s['you'],s['opponent'];hp=effective_health(y['hero']);ehp=effective_health(o['hero'])
    if ehp<=0:return 1000000
    if hp<=0:return -1000000
    face=cfg.get('turn_face',1.1)+(0.6 if ehp<=10 else 0)
    board=cfg.get('turn_board',1.0)
    incoming=threat(o)
    taunts=[m for m in y['board'] if m.get('taunt')]
    # A conservative warning: existing Secrets provide no guaranteed protection.
    known_open_lethal=not taunts and incoming>=hp
    score=board*(sum(minion_value(m) for m in y['board'])-sum(minion_value(m) for m in o['board']))
    score-=face*ehp
    score+=.2*hp+cfg.get('turn_hand',1.4)*len(y['hand'])
    score+=(y.get('weapon') or {}).get('attack',0)*(y.get('weapon') or {}).get('durability',0)*.6
    score-=cfg.get('turn_risk',4.0)*max(0,incoming-hp+4)
    if known_open_lethal:score-=10000
    return score


def plan(state,ranked,cfg,outer_deadline):
    begin=time.monotonic();deadline=min(outer_deadline,begin+cfg.get('turn_budget_s',.045))
    report={'nodes':0,'action':None,'supported':model.supported(state),'bounded_out':False,'depth':0,'excluded':0,'deduplicated':0,'beam_pruned':0,'stop_reason':None}
    if not report['supported'] or not ranked:return report
    initial=model.prepare({**state,'planning_mode':'response' if cfg.get('extended_turn') or cfg.get('public_response') else 'base'})
    # Do not replace a strong unmodelled random/development action with an incomplete comparison.
    if ranked[0][1]['type']!='end_turn' and model.transition(initial,ranked[0][1]) is None:
        report['reason']='top_action_outside_effect_coverage';return report
    if cfg.get('coin_coverage_guard') and ranked[0][1]['type']=='play_card':
        root_card=next((c for c in state['you']['hand'] if c['entity_id']==ranked[0][1]['card']),{})
        if root_card.get('card_id')=='GAME_005' and len(state['you']['board'])<7:
            knives=any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in state['you']['board'])
            followups=[c for c in state['you']['hand'] if state['you']['mana']<c['cost']<=state['you']['mana']+1
                       and (c['card_id'] in ('NEW1_019','NEW1_031') or (knives and (c['type']=='MINION' or c['card_id']=='EX1_538')))]
            if followups:
                report['reason']='coin_followup_outside_effect_coverage';return report
    best=value(initial,cfg);best_line=[];frontier=[(initial,[])];seen=set()
    endpoints={'end_turn':[(best,initial,[])]}
    cap=cfg.get('turn_nodes',300);width=cfg.get('turn_width',10);depth=cfg.get('turn_depth',7)
    for d in range(depth):
        following=[]
        for current,line in frontier:
            choices=(a for _,a in ranked if a['type']!='end_turn') if not line else model.options(current)
            for action in choices:
                if time.monotonic()>=deadline or report['nodes']>=cap:
                    report['bounded_out']=True;report['stop_reason']='time' if time.monotonic()>=deadline else 'nodes';break
                successor=model.transition(current,action);report['nodes']+=1
                if successor is None:report['excluded']+=1;continue
                key=model.signature(successor)
                if key in seen:report['deduplicated']+=1;continue
                seen.add(key);path=line+[action];v=value(successor,cfg)
                root=json.dumps(path[0],sort_keys=True)
                endpoints[root]=retain_endpoint(endpoints.get(root,[]),(v,successor,path))
                if v>best+1e-8:
                    best=v;best_line=path
                following.append((v,successor,path))
            if report['bounded_out']:break
        report['depth']=d+1
        if report['bounded_out'] or not following:break
        following.sort(key=lambda x:x[0],reverse=True)
        report['beam_pruned']+=max(0,len(following)-width)
        frontier=[(s,line) for _,s,line in following[:width]]
    if cfg.get('public_response') and time.monotonic()<outer_deadline:
        from public_response import worst_reply
        candidates=response_shortlist(list(endpoints.values()),cfg.get('reply_candidates',6))
        report['endpoint_funnel']={'first_actions':len(endpoints),'retained':sum(map(len,endpoints.values())),'same_first_alternates':sum(len(b)>1 for b in endpoints.values()),'response_candidates':len(candidates),'max_total_response_candidates':cfg.get('reply_candidates',6)}
        reply_deadline=min(outer_deadline,time.monotonic()+cfg.get('reply_budget_s',.16))
        evaluated=[];reply_nodes=0;complete=True
        for before,endpoint,path in candidates:
            if time.monotonic()>=reply_deadline:complete=False;break
            response=worst_reply(endpoint,cfg,reply_deadline,cfg.get('reply_nodes',48))
            reply_nodes+=response['nodes']
            if not response['supported'] or time.monotonic()>=reply_deadline:complete=False;break
            # Preserve a fraction of end-turn tempo while testing visible tactical vulnerabilities.
            v=(1-cfg.get('reply_weight',.85))*before+cfg.get('reply_weight',.85)*response['value']
            if response['visible_lethal_found']:v-=100000
            evaluated.append((v,path,response))
        report['reply']={'nodes':reply_nodes,'candidates':len(evaluated),'comparable':complete,
                         'scope':'visible attacks only; hidden cards excluded'}
        report['nodes']+=reply_nodes
        if complete and evaluated:
            v,path,response=max(evaluated,key=lambda x:x[0])
            best=v;best_line=path or [{'type':'end_turn'}]
            report['reply']['visible_lethal_found']=response['visible_lethal_found']
    if best_line and legal(state,best_line[0]):report.update(action=best_line[0],sequence=best_line,value=best)
    report['elapsed_s']=time.monotonic()-begin
    return report

def endpoint_resources(s):
    y,o=s['you'],s['opponent']
    return (tuple(sorted(c['card_id'] for c in y['hand'])),
            (y.get('weapon') or {}).get('durability',0),
            sum(m['health']==1 for m in y['board']),
            sum(m['attack'] for m in o['board']),y['hero']['health'])

def retain_endpoint(bucket,item):
    pool=sorted(bucket+[item],key=lambda x:x[0],reverse=True)
    first=pool[0];signature=endpoint_resources(first[1])
    second=next((x for x in pool[1:] if endpoint_resources(x[1])!=signature),None)
    return [first]+([second] if second else [])

def response_shortlist(buckets,limit):
    primary=sorted((b[0] for b in buckets),key=lambda x:x[0],reverse=True)
    # Four first actions and at most two alternative tails use the old six-leaf
    # response budget. If no distinct tail exists, restore the original breadth.
    leaders=primary[:max(1,limit-2)]
    alternate=[]
    for first in leaders:
        bucket=next(b for b in buckets if b[0] is first)
        if len(bucket)>1:alternate.append(bucket[1])
    alternate.sort(key=lambda x:x[0],reverse=True)
    selected=leaders+alternate[:2]
    for item in primary[len(leaders):]:
        if len(selected)>=limit:break
        selected.append(item)
    return selected[:limit]
