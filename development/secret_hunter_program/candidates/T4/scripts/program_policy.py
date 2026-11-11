"""One public-state decision, with a prepared legal fallback and bounded search."""
import time
from action_validator import fallback, legal
from secret_policy import rank
from lethal_planner import search


def decide(state, config, publish=None):
    start=time.monotonic()
    if state['phase'] in ('deck_submission','game_over'):
        from fallback import basic
        return basic(state),{'fallback':False,'reason':state['phase'],'nodes':0,'elapsed_s':time.monotonic()-start}
    best=fallback(state)
    info={'fallback':True,'nodes':0,'search_used':False,'reason':'phase_fallback'}
    def save(action,reason):
        nonlocal best
        if legal(state,action):
            best=action;info.update(fallback=False,reason=reason)
            if publish:publish(best,dict(info))
    if publish:publish(best,dict(info))
    try:
        ranked=rank(state,config)
        if ranked:save(ranked[0][1],'baseline_rank')
        deadline=start+min(1.5,config.get('search_soft_s',1.5))
        if state['phase']=='main' and time.monotonic()<deadline:
            lethal=search(state,budget_s=max(0,min(config.get('search_budget_s',.15),deadline-time.monotonic())),max_nodes=config.get('search_nodes',1600))
            info.update(lethal=lethal,nodes=lethal['nodes'])
            if lethal['guaranteed']:save(lethal['first_action'],'guaranteed_lethal')
            else:
                if config.get('scoring') or config.get('secret_rules'):
                    from improvements import rerank
                    ranked=rerank(state,ranked,config,deadline)
                    if ranked:save(ranked[0][1],'enhanced_rank')
                if config.get('turn_search') and time.monotonic()<deadline:
                    from turn_search import plan
                    result=plan(state,ranked,config,deadline)
                    info['turn_search']=result;info['nodes']+=result.get('nodes',0)
                    if result.get('action'):save(result['action'],'turn_search');info['search_used']=True
    except Exception as exc:
        info['error']=type(exc).__name__+': '+str(exc)
    info['elapsed_s']=time.monotonic()-start
    info['over_budget']=info['elapsed_s']>2
    return best,info
