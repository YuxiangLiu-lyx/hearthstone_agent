"""One atomic action: frozen Y1 protection followed by bounded public MCGS."""
import time
from y1_policy import decide as y1_decide
from action_validator import legal


def decide(state, config, publish=None, memory=None):
    start=time.monotonic()
    action,info=y1_decide(state,config,publish,memory=None)
    info['parent_reason']=info.get('reason')
    if state['phase'] not in ('main','choice') or info.get('lethal',{}).get('guaranteed'):
        return action,info
    mcgs=config.get('mcgs',{})
    if not mcgs or not mcgs.get('min_mana',2)<=state['you']['max_mana']<=mcgs.get('max_mana',6):
        return action,info
    if state['phase']=='main' and not state['opponent']['board']:
        return action,info
    deadline=min(start+config.get('search_soft_s',1.5),config.get('_deadline',float('inf')),
                 start+mcgs.get('budget_s',.35))
    if time.monotonic()>=deadline:return action,info
    # A full legal Y1 decision was already published before initialization.
    try:
        from mcgs_init import initialize
        initialize()
        from mcgs_search import search
        if time.monotonic()<deadline:
            result=search(state,{**config,**mcgs},action,deadline)
            info['mcgs']=result
            if legal(state,result['action']):
                action=result['action'];info['reason']='mcgs_changed' if result['changed'] else 'mcgs_retained_y1'
                if publish:publish(action,dict(info))
    except Exception as exc:
        info['mcgs_unavailable']=type(exc).__name__+': '+str(exc)
    info['elapsed_s']=time.monotonic()-start
    return action,info
