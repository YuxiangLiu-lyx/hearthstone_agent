"""Public endpoint -> sparse response scenarios -> observed-hand recovery search.

Independent adaptation of PredatorMCTS's selective leaf/response/own-turn scheme.
Hypotheses are possible card plays, never assertions about an actual hidden hand.
No learned weights, proxy identity, seed, outcome label or external prior is used.
"""
import copy,json,time
import tactical_model as m
from action_validator import legal
from race_plan import value
from public_response import prepare_reply,attacks,attack
from state_features import CATALOG

def end_turn(s,side):
    """Only supported public end effects and explicitly tracked temporary buffs."""
    r=m.end_effects(s,side)
    if r is None:return None
    for key in ('you','opponent'):
        for x in r[key]['board']:
            if x.get('temporary_attack',0):
                x['base_attack']-=x.pop('temporary_attack')
    m.refresh(r)
    return r

def recovery(s,cfg,deadline,cap=24):
    r=end_turn(s,'opponent')
    if r is None:return None,0
    if r['you']['hero']['health']<=0 or r['opponent']['hero']['health']<=0:return value(r,cfg,True),0
    y=r['you'];y['mana']=max(0,min(10,y['max_mana']+1)-y.get('overload_next_turn',0));y['max_mana']=min(10,y['max_mana']+1)
    y['hero_power']['usable']=True;r['turn']+=2
    for x in y['board']:
        x['remaining_attacks']=0 if x.get('frozen') else 2 if x.get('windfury') else 1
    y['hero']['attack']=(y.get('weapon') or {}).get('attack',0)
    y['hero']['remaining_attacks']=int(not y['hero'].get('frozen') and y['hero']['attack']>0)
    r['hero_attack_available']=not y['hero'].get('frozen');m.refresh(r)
    # No unseen draw is invented. This is a conservative known-hand recovery estimate.
    base=value(s,cfg,True)
    recovery_cfg={**cfg,'race_face_bonus':0,'hand_clock_bonus':0,'board_clock_bonus':0}
    best=value(r,recovery_cfg,True);initial=best;front=[r];seen=set();nodes=0
    def conservative():return base+.15*min(6,max(0,best-initial))
    for _ in range(3):
        nxt=[]
        for z in front:
            for a in m.options(z):
                if time.monotonic()>=deadline or nodes>=cap:return conservative(),nodes
                q=m.transition(z,a);nodes+=1
                if q is None:continue
                key=m.signature(q)
                if key in seen:continue
                seen.add(key);v=value(q,recovery_cfg,True);best=max(best,v);nxt.append((v,q))
        nxt.sort(key=lambda x:x[0],reverse=True);front=[z for _,z in nxt[:2]]
        if not front:break
    return conservative(),nodes

def hypotheses(state):
    """Feasible one-card scenarios; the visible-only world always remains present."""
    o=state['opponent'];e=state.get('public_opponent_evidence',{});shown=e.get('shown_cards',[]);counts=e.get('shown_card_counts',{})
    mana=max(0,min(10,o['max_mana']+1)-o.get('overload_next_turn',0));hand=min(10,o.get('hand_size',0)+int(o.get('deck_remaining',0)>0));cls=o['hero']['hero_class']
    if hand==0:return []
    proposal=[]
    for cid in shown:
        if cid in {'CS2_188','EX1_046','EX1_093','EX1_058','CS2_179','CS2_172','EX1_162','EX1_008','EX1_029','EX1_302','EX1_308','DS1_185','EX1_539','CS2_024','CS2_029'}:proposal.append(cid)
    if e.get('cheap_minions_played',0)>=2:proposal+=['CS2_188','CS2_179']
    proposal+= {'WARLOCK':['EX1_302'],'HUNTER':['DS1_185'],'MAGE':['CS2_024']}.get(cls,[])
    out=[];categories=set()
    for cid in proposal:
        c=CATALOG[cid];kind='buff' if cid in {'CS2_188','EX1_046','EX1_093','EX1_058','EX1_162'} else 'spell' if c['type']=='SPELL' else 'develop'
        if c['cost']>mana or counts.get(cid,0)>=2 or c['card_class'] not in (cls,'NEUTRAL'):continue
        if c['type']=='MINION' and len(o['board'])>=7:continue
        if cid in {'CS2_188','EX1_046','EX1_093','EX1_058'} and not o['board']:continue
        if cid=='EX1_308' and hand<2:continue
        if kind in categories:continue
        categories.add(kind);out.append({'card_id':cid,'kind':kind,'publicly_seen':cid in shown,'mana':mana,'hand_size':hand})
        if len(out)==3:break
    return out

def hypothetical_plays(s,h):
    """One hypothetical card plus its public targets and positions."""
    cid=h['card_id'];c=CATALOG[cid];o=s['opponent'];y=s['you']
    if s.get('_hypothesis_used') or c['cost']>s['_reply_mana']:return
    targets=[None];positions=[len(o['board'])]
    if c['type']=='MINION':
        if len(o['board'])>=7 or any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in o['board']):return
        if cid in {'CS2_188','EX1_046'}:targets=[x['entity_id'] for x in o['board']]
        if cid in {'EX1_093','EX1_058','EX1_162'}:positions=list(range(len(o['board'])+1))
    else:
        targets=[x['entity_id'] for x in y['board'] if not x.get('stealth') and not x.get('immune')]
        if cid!='EX1_302':targets+=[y['hero']['entity_id']]
    for target in targets:
        for pos in positions:yield (target,pos)

def play_hypothesis(s,h,action):
    r=copy.deepcopy(s);cid=h['card_id'];c=CATALOG[cid];o=r['opponent'];y=r['you'];target,pos=action
    r['_hypothesis_used']=True;r['_reply_mana']-=c['cost'];o['hand_size']=max(0,o.get('hand_size',0)-1)
    t=next((x for x in y['board']+o['board']+[y['hero']] if x['entity_id']==target),None)
    if c['type']=='MINION':
        m.summon(r,o,cid,position=pos,trigger=False)
        if cid in {'CS2_188','EX1_046'}:
            if t is None:return None
            t['base_attack']+=2;t['temporary_attack']=t.get('temporary_attack',0)+2
        if cid in {'EX1_093','EX1_058'}:
            for j in (pos-1,pos+1):
                if 0<=j<len(o['board']):
                    x=o['board'][j];x['taunt']=True
                    if cid=='EX1_093':x['base_attack']+=1;x['health']+=1;x['max_health']+=1
    else:
        amount={'EX1_302':1,'EX1_308':4,'DS1_185':2,'EX1_539':5 if any(m.is_beast(x) for x in o['board']) else 3,'CS2_024':3,'CS2_029':6}[cid]
        amount+=sum(x.get('spell_damage',0) for x in o['board']);m.damage(t,amount)
        if cid=='EX1_302' and t['health']<=0:
            if o.get('deck_remaining',0)<=0:return None
            o['deck_remaining']-=1;o['hand_size']=min(10,o['hand_size']+1)
        if cid=='CS2_024':t['frozen']=True
        if cid=='EX1_308':o['hand_size']=max(0,o['hand_size']-1)
        for x in o['board']:
            if x['card_id']=='EX1_608' and not x.get('silenced'):x['base_attack']+=1
    if not m.cleanup(r):return None
    m.refresh(r);return r

def response(endpoint,h,cfg,deadline,cap=32):
    s=prepare_reply(endpoint)
    if s is None:return None,0
    s['_reply_mana']=h['mana'] if h else 0
    if h:s['opponent']['hand_size']=h['hand_size']
    # Search interleaved public attacks and a single hypothetical card.
    frontier=[s];seen=set();ends=[];nodes=0
    for _ in range(7):
        nxt=[]
        for z in frontier:
            ends.append(z)
            choices=[('attack',a) for a in attacks(z)]
            if h:choices += [('play',a) for a in hypothetical_plays(z,h)]
            for typ,a in choices:
                if nodes>=cap or time.monotonic()>=deadline:break
                q=attack(z,a) if typ=='attack' else play_hypothesis(z,h,a);nodes+=1
                if q is None:continue
                key=(m.signature(q),q.get('_hypothesis_used',False))
                if key in seen:continue
                seen.add(key);nxt.append((value(q,cfg,True),q))
            if nodes>=cap or time.monotonic()>=deadline:break
        nxt.sort(key=lambda x:x[0]);frontier=[z for _,z in nxt[:2]]
        if nodes>=cap or time.monotonic()>=deadline:ends+=frontier;break
        if not frontier:break
    # Evaluate the two threatening endpoints, then our best supported recovery.
    ends.sort(key=lambda s:value(s,cfg,True));best=None
    for z in ends[:2]:
        v,n=recovery(z,cfg,deadline);nodes+=n
        if v is not None:best=v if best is None else min(best,v)
    return best,nodes

def endpoints(state,ranked,baseline,cfg,deadline):
    """Deduplicate states rather than roots, preserving plans with a shared prefix."""
    s=m.prepare({**state,'planning_mode':'response'})
    if baseline['type']!='end_turn' and m.transition(s,baseline) is None:return [],{'reason':'baseline_outside_deterministic_coverage','nodes':0}
    card=next((c for c in state['you']['hand'] if c['entity_id']==baseline.get('card')), {})
    if card.get('card_id')=='GAME_005':
        knives=any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in state['you']['board'])
        if any(state['you']['mana']<c['cost']<=state['you']['mana']+1 and
               (c['card_id'] in ('NEW1_031','NEW1_019') or (knives and (c['type']=='MINION' or c['card_id']=='EX1_538')))
               for c in state['you']['hand']):
            return [],{'reason':'coin_followup_outside_deterministic_coverage','nodes':0}
    front=[(s,[])];seen=set();all_ends=[];nodes=0
    width=6;root_count=len(ranked);depth=7 if root_count<12 else 5 if root_count<25 else 4
    for _ in range(depth):
        nxt=[]
        for z,path in front:
            all_ends.append((value(z,cfg),z,path+[{'type':'end_turn'}]))
            choices=[a for _,a in ranked if a['type'] not in ('end_turn','concede')] if not path else list(m.options(z))
            for a in choices:
                if nodes>=cfg.get('response_nodes',240) or time.monotonic()>=deadline:break
                q=m.transition(z,a);nodes+=1
                if q is None:continue
                key=(json.dumps((path+[a])[0],sort_keys=True),m.signature(q))
                if key in seen:continue
                seen.add(key);nxt.append((value(q,cfg),q,path+[a]))
            if nodes>=cfg.get('response_nodes',240) or time.monotonic()>=deadline:break
        nxt.sort(key=lambda x:x[0],reverse=True);front=[(q,p) for _,q,p in nxt[:width]]
        if nodes>=cfg.get('response_nodes',240) or time.monotonic()>=deadline:break
        if not front:break
    all_ends += [(value(z,cfg),z,p+[{'type':'end_turn'}]) for z,p in front]
    all_ends.sort(key=lambda x:x[0],reverse=True)
    # Preserve a baseline-root plan, then unique competitive endpoints (two per root).
    base=next((x for x in all_ends if x[2][0]==baseline),None)
    if base is None:return [],{'nodes':nodes,'reason':'baseline_endpoint_missing'}
    chosen=[base];counts={json.dumps(baseline,sort_keys=True):1};keys={m.signature(base[1])}
    for x in all_ends:
        k=m.signature(x[1]);root=json.dumps(x[2][0],sort_keys=True)
        if k in keys or counts.get(root,0)>=2:continue
        chosen.append(x);keys.add(k);counts[root]=counts.get(root,0)+1
        if len(chosen)>=cfg.get('response_candidates',5):break
    return chosen,{'nodes':nodes,'generated_endpoints':len(all_ends),'unique_states':len(seen),'depth_budget':depth}

def plan(state,ranked,baseline,cfg,outer_deadline):
    start=time.monotonic();report={'nodes':0,'action':None}
    if state.get('phase')!='main' or not 2<=state['you']['max_mana']<=4 or not m.supported(state):return report
    deadline=min(outer_deadline,start+cfg.get('response_budget_s',.30))
    candidates,details=endpoints(state,ranked,baseline,cfg,min(deadline,start+.09));report.update(details)
    if len(candidates)<2:return report
    hs=hypotheses(state) if cfg.get('response_hypotheses') else []
    evaluated=[]
    for before,endpoint,path in candidates:
        if time.monotonic()>=deadline:report['reason']='deadline';break
        visible,n=response(endpoint,None,cfg,deadline);report['nodes']+=n
        if visible is None:continue
        scores=[]
        for h in hs:
            v,n=response(endpoint,h,cfg,deadline);report['nodes']+=n
            if v is not None:scores.append(v)
        # Uncalibrated hand membership gets a bounded, low influence. This is
        # robust sensitivity analysis, not an estimated scenario probability.
        adjusted=visible
        if scores:adjusted+=.25*max(-12,min(0,min(scores)-visible))
        v=.2*before+.8*adjusted
        evaluated.append({'value':v,'visible':visible,'hypothesis_values':scores,'path':path,'before':before})
    report.update(candidates=evaluated,hypotheses=hs,elapsed_s=time.monotonic()-start,probability_claim=False)
    if len(evaluated)!=len(candidates) or time.monotonic()>=deadline:
        report['reason']='incomplete_comparison';return report
    base=next((x for x in evaluated if x['path'][0]==baseline),None)
    if base is None:return report
    winner=max(evaluated,key=lambda x:x['value'])
    if winner['value']>base['value']+cfg.get('response_margin',1.0) and legal(state,winner['path'][0]):
        report.update(action=winner['path'][0],sequence=winner['path'],reason='complete_endpoint_comparison')
    return report
