"""Bounded public-effect turn search; unsupported branches retain the ranked action."""
import copy,json,time
from action_validator import legal
from state_features import effective_health,is_beast
from evaluator import minion_value,threat
import tactical_model as model


def base_value(s,cfg):
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
    from evolved_value import secret_potential
    return score + secret_potential(s)


def value(s, cfg):
    if cfg.get('evolved_features'):
        from evolved_value import evaluate
        return evaluate(s, cfg)
    return base_value(s, cfg)


def plan(state,ranked,cfg,outer_deadline):
    begin=time.monotonic();deadline=min(outer_deadline,begin+cfg.get('turn_budget_s',.045))
    report={'nodes':0,'action':None,'supported':model.supported(state),'bounded_out':False,'depth':0}
    if not report['supported'] or not ranked:return report
    initial=model.prepare(state)
    # Do not replace a strong unmodelled random/development action with an incomplete comparison.
    if ranked[0][1]['type']!='end_turn' and model.transition(initial,ranked[0][1]) is None:
        report['reason']='top_action_outside_effect_coverage';return report
    best=value(initial,cfg);best_line=[];frontier=[(initial,[])];seen=set()
    cap=cfg.get('turn_nodes',300);width=cfg.get('turn_width',10);depth=cfg.get('turn_depth',7)
    for d in range(depth):
        following=[]
        for current,line in frontier:
            choices=(a for _,a in ranked if a['type']!='end_turn') if not line else model.options(current)
            for action in choices:
                if time.monotonic()>=deadline or report['nodes']>=cap:
                    report['bounded_out']=True;break
                successor=model.transition(current,action);report['nodes']+=1
                if successor is None:continue
                key=model.signature(successor)
                if key in seen:continue
                seen.add(key);path=line+[action];v=value(successor,cfg)
                if v>best+1e-8:
                    best=v;best_line=path
                following.append((v,successor,path))
            if report['bounded_out']:break
        report['depth']=d+1
        if report['bounded_out'] or not following:break
        following.sort(key=lambda x:x[0],reverse=True)
        frontier=[(s,line) for _,s,line in following[:width]]
    if best_line and legal(state,best_line[0]):report.update(action=best_line[0],sequence=best_line,value=best)
    report['elapsed_s']=time.monotonic()-begin
    return report
