"""Public expected endpoint comparisons with observation-contingent continuation.

Only the first current legal action is returned. Small chance sets are exact;
large sets are sampled. This heuristic is deliberately separate from lethal proof.
"""
import math
import time
import tactical_model as model
from action_validator import legal
from chance_model import outcomes
from turn_search import value


def utility(s, cfg):
    return max(-200.0, min(200.0, value(s, cfg)))


def continuation(s, cfg, deadline, report, cap=32):
    """Independent bounded deterministic continuation after observing an outcome."""
    best = (utility(s,cfg), s); frontier = [s]; seen = {model.signature(s)}; used = 0
    for _ in range(6):
        children = []
        for current in frontier:
            for a in model.options(current):
                if time.monotonic() >= deadline:
                    raise TimeoutError
                if used >= cap:
                    return best
                child = model.transition(current,a); used += 1; report['nodes'] += 1
                if child is None:
                    continue
                key = model.signature(child)
                if key in seen:
                    continue
                seen.add(key); v = utility(child,cfg)
                if v > best[0]:best = (v,child)
                children.append((v,child))
        if not children:break
        children.sort(key=lambda x:x[0],reverse=True)
        frontier = [x[1] for x in children[:3]]
    return best


class UnsupportedResponse(Exception):
    pass


def score_endpoint(endpoint, before, cfg, deadline, report):
    if min(endpoint[k]['hero']['health'] for k in ('you','opponent'))<=0:
        return utility(endpoint,cfg)
    from public_response import worst_reply
    reply=worst_reply(endpoint,cfg,deadline,16)
    if not reply['supported']:
        from chance_reply import reply as chance_reply
        random_reply=chance_reply(endpoint,cfg,deadline)
        report['nodes']+=reply['nodes']
        reply=random_reply
        report['misdirection_responses']=report.get('misdirection_responses',0)+int(reply['supported'])
    report['nodes']+=reply['nodes']
    report['reply_bounded']=report.get('reply_bounded',0)+int(reply.get('bounded',False))
    if time.monotonic()>=deadline:raise TimeoutError
    if not reply['supported']:raise UnsupportedResponse
    after=max(-200.0,min(200.0,reply['value']))
    if reply['visible_lethal_found']:after=-200.0
    return .15*before+.85*after


def evaluate(s, action, cfg, deadline, report):
    if action['type']=='end_turn':
        dist={'supported':True,'exact':True,'outcomes':[(1.0,s)],'nodes':0}
    else:
        dist=outcomes(s,action,deadline,cap=cfg.get('chance_exact_cap',8),samples=cfg.get('chance_samples',6))
    report['nodes']+=dist['nodes']
    if not dist['supported']:
        report['excluded']+=1
        if dist['reason']=='deadline':raise TimeoutError
        return None
    report['exact_distributions' if dist['exact'] else 'sampled_distributions']+=1
    values=[];lethal_mass=0.0
    for weight,child in dist['outcomes']:
        if action['type']=='end_turn':v,endpoint=utility(child,cfg),child
        else:v,endpoint=continuation(child,cfg,deadline,report)
        v=score_endpoint(endpoint,v,cfg,deadline,report)
        # One additional chance action lets a newly played Juggler plan a summon.
        # Each random outcome gets its own continuation; no future RNG is revealed.
        if cfg.get('chance_followup') and action['type']!='end_turn':
            alternatives=[]
            for start in (child,endpoint):
                for a in model.options(start,random=True):
                    if a['type']!='play_card':continue
                    card=next(c for c in start['you']['hand'] if c['entity_id']==a['card'])
                    if card['card_id'] not in ('EX1_538','NEW1_031') and card['type']!='MINION':continue
                    if not any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in start['you']['board']):continue
                    alternatives.append((start,a))
                    if len(alternatives)>=2:break
                if len(alternatives)>=2:break
            for start,a in alternatives:
                d=outcomes(start,a,deadline,cap=8,samples=6);report['nodes']+=d['nodes']
                if not d['supported']:
                    if d['reason']=='deadline':raise TimeoutError
                    report['excluded']+=1;continue
                report['exact_distributions' if d['exact'] else 'sampled_distributions']+=1
                expected=0.0
                for p,x in d['outcomes']:
                    before,end=continuation(x,cfg,deadline,report,cap=16)
                    expected+=p*score_endpoint(end,before,cfg,deadline,report)
                v=max(v,expected)
        values.append((weight,v))
        # This is an estimated endpoint mass, never a guaranteed-lethal flag.
        if endpoint['opponent']['hero']['health']<=0:lethal_mass+=weight
    mean=sum(w*v for w,v in values)
    sd=math.sqrt(max(0,sum(w*(v-mean)**2 for w,v in values)))
    return {'value':mean-cfg.get('chance_risk',0.0)*sd,'mean':mean,'sd':sd,'outcomes':len(values),'exact_root':dist['exact'],'endpoint_lethal_mass':lethal_mass}


def plan(state, ranked, baseline, cfg, outer_deadline):
    start=time.monotonic();deadline=min(outer_deadline,start+cfg.get('chance_budget_s',.45))
    report={'active':False,'nodes':0,'excluded':0,'exact_distributions':0,'sampled_distributions':0,'comparisons':[],'guaranteed':False}
    if not model.supported(state):return report
    y=state['you'];knives=any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in y['board'])
    available=[c for c in y['hand'] if c['cost']<=y['mana']]
    companion_ready=any(c['card_id']=='NEW1_031' for c in available) and len(y['board'])<7
    if not companion_ready and not knives and not any(c['card_id']=='NEW1_019' and any(d['entity_id']!=c['entity_id'] and d['cost']+c['cost']<=y['mana'] and (d['type']=='MINION' or d['card_id']=='EX1_538') for d in available) for c in available):return report
    if not any(c['type']=='MINION' or c['card_id'] in ('EX1_538','NEW1_031') for c in available):return report
    report['active']=True
    initial=model.prepare({**state,'planning_mode':'proof'})
    candidates=[baseline];keys={str(sorted(baseline.items()))};cards=set()
    for _,a in ranked:
        if a['type']=='play_card':
            if a['card'] in cards:continue
            cards.add(a['card'])
        key=str(sorted(a.items()))
        if key not in keys:candidates.append(a);keys.add(key)
        if len(candidates)>=cfg.get('chance_roots',7):break
    try:
        baseline_result=evaluate(initial,baseline,cfg,deadline,report)
        if baseline_result is None:
            report['reason']='baseline_outside_coverage';return report
        best=baseline_result['value'];chosen=baseline
        report['comparisons'].append({'action':baseline,**baseline_result})
        for a in candidates[1:]:
            try:
                result=evaluate(initial,a,cfg,deadline,report)
            except UnsupportedResponse:
                report['excluded_response_roots']=report.get('excluded_response_roots',0)+1
                continue
            if result is None:continue
            report['comparisons'].append({'action':a,**result})
            if result['value']>best+cfg.get('chance_margin',1.0):best=result['value'];chosen=a
        report['complete']=True
        if chosen!=baseline and legal(state,chosen):report['action']=chosen
    except UnsupportedResponse:
        report['complete']=False;report['reason']='unsupported_visible_response';report.pop('action',None)
    except TimeoutError:
        report['complete']=False;report['reason']='deadline';report.pop('action',None)
    report['elapsed_s']=time.monotonic()-start
    return report
