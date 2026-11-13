"""Y1 with small public turn alternatives and verified deterministic continuations."""
import time
from parent_policy import decide as baseline
from action_validator import legal


def decide(state,cfg,publish=None,memory=None):
    start=time.monotonic()
    original,info=baseline(state,{**cfg,'plan_cache':False},publish,memory=None)
    if state.get('phase')!='main' or info.get('reason')=='guaranteed_lethal':return original,info
    from turn_routes import context,choose
    from continuation_cache import take,save
    ctx=context(state);record={'context':ctx,'hit':bool(ctx),'legal_alternative':False,'changed':False}
    info['turn_routes']=record
    if cfg.get('continuation_memory') and memory is not None:
        cached,reason=take(state,cfg,memory);record['cache']=reason
        if cached is not None and cfg.get('continuation_mode')=='finish_minions' and cached!=original:
            card=next((c for c in state['you']['hand'] if c['entity_id']==cached.get('card')),None)
            permitted=original['type']=='end_turn' and cached['type']=='play_card' and card and card['type']=='MINION'
            if not permitted:
                memory.clear();cached=None;record['cache']='fresh_plan_preferred'
        if cached is not None:
            record.update(changed=cached!=original,cache_hit=True,legal_alternative=cached!=original)
            info['reason']='verified_continuation';info['elapsed_s']=time.monotonic()-start
            if publish:publish(cached,info)
            return cached,info
    eligible=bool(set(ctx)&set(cfg.get('route_contexts',[])))
    if ctx==['trap'] and state['you']['max_mana']<cfg.get('trap_min_max_mana',0):
        eligible=False;record['early_curve_preserved']=True
    deadline=min(cfg.get('_deadline',start+1.45),start+1.45)
    chosen=None
    if eligible and time.monotonic()<deadline:
        chosen,result=choose(state,cfg,min(deadline,time.monotonic()+cfg.get('route_budget_s',.08)))
        record.update(nodes=result['nodes'],plans=len(result['plans']),supported=result['supported'])
        if chosen:
            action=chosen['sequence'][0]
            record['legal_alternative']=any(p['sequence'][0]!=original and legal(state,p['sequence'][0]) for p in result['plans'])
            if legal(state,action):
                record.update(changed=action!=original,sequence=chosen['sequence'],features=chosen['features'])
                original=action;info['reason']='whole_turn_route'
    if cfg.get('continuation_memory') and memory is not None:
        sequence=chosen['sequence'] if chosen else info.get('turn_search',{}).get('sequence',[])
        # The retained line must start with the action that will actually execute.
        if sequence and sequence[0]==original:
            record['cached_steps']=save(state,cfg,sequence,memory,deadline)
    info['elapsed_s']=time.monotonic()-start
    if publish:publish(original,info)
    return original,info
