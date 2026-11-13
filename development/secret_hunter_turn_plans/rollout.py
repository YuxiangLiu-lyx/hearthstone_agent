"""One paired whole-turn intervention with common frozen terminal policies."""
from collections import Counter
import json
from pathlib import Path
import random
import sys
import time
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_program.common import ROOT


def run(job):
    source=json.loads(Path(job['source']).read_text());state=source['state']
    candidate_path=HERE/'candidates'/job.get('candidate','R1-memory')
    sys.path[:0]=[str(candidate_path/'scripts'),str(ROOT/'development/secret_hunter_mcgs')]
    from mcgs_init import initialize
    initialize()
    from mcgs_world import build
    from program_policy import decide as candidate
    try:from parent_policy import decide as frozen
    except ImportError:from y1_policy import decide as frozen
    from turn_routes import choose
    from continuation_cache import key
    import tactical_model as model
    from state_features import with_public_history
    from development.secret_hunter_tactics.run import opponent
    from actions import expand
    seed=41000000+source['source_seed']*1000+job['sample']
    rng=random.Random(seed);spec=source['opponent_spec'];o=state['opponent']
    cards=Counter(json.loads((ROOT/spec['deck']).read_text())['cards'])
    for c in o['board']+o.get('graveyard',[])+([o['weapon']] if o.get('weapon') else []):
        if cards[c['card_id']]>0:cards[c['card_id']]-=1
    bag=list(cards.elements());rng.shuffle(bag);n=o.get('hand_size',0);d=o.get('deck_remaining',0)
    if len(bag)<n+d:bag+=['GAME_005']*(n+d-len(bag))
    hand=bag[:n];deck=bag[n:n+d]
    scenario=job.get('scenario','natural')
    if scenario=='forced_coil' and job.get('strict_coil'):
        if not any(m['card_id']=='EX1_393' and m['health']==m['max_health'] and m['health']>1
                   and not any(m.get(k) for k in ('silenced','frozen','divine_shield','immune')) for m in o['board']):
            raise ValueError('No undamaged Amani stress window at root')
    if scenario=='no_coil':
        # Condition on no Coil available in the response hand or next draw,
        # retaining the sampled deck multiset whenever such a swap is possible.
        for index,c in enumerate(hand):
            if c=='EX1_302':
                swap=next((j for j,v in enumerate(deck[:-1]) if v!='EX1_302'),None)
                if swap is None:raise ValueError('no legal no-Coil conditional sample')
                hand[index],deck[swap]=deck[swap],hand[index]
        if deck and deck[-1]=='EX1_302':
            swap=next((j for j,v in enumerate(deck[:-1]) if v!='EX1_302'),None)
            if swap is None:raise ValueError('no legal no-Coil next draw')
            deck[-1],deck[swap]=deck[swap],deck[-1]
    elif scenario=='forced_coil' and 'EX1_302' not in hand:
        if 'EX1_302' not in deck:raise ValueError('No unspent Coil available in the sampled deck')
        j=deck.index('EX1_302')
        if hand:hand[0],deck[j]=deck[j],hand[0]
        elif job.get('force_next_draw'):deck[-1],deck[j]=deck[j],deck[-1]
        else:raise ValueError('Coil unavailable under public copy constraints')
    world=build(state,seed,opponent_hand=hand,opponent_deck=deck)
    world.game.random.seed(seed+17)
    base_cfg=json.loads((Y1/'config.json').read_text())
    cfg=json.loads((candidate_path/'config.json').read_text())
    if job['route']=='replan':cfg['continuation_memory']=False
    foe=opponent(spec);memory={};history={1:[],2:[]};start_turn=world.turn;trace=[];full=[];forced_used=False
    for event in source.get('public_history',[]):
        event=dict(event)
        if event.get('player') in (1,2):event['player']=1 if event['player']==source['seat'] else 2
        history[1].append(event)
    cursors={1:0,2:0}
    planned=[];expected=None;steps=0;response=None;end_turn_state=None
    own_deck=[c.id for c in world.player(1).deck]
    start=time.monotonic()
    while not world.over and steps<500 and world.turn<start_turn+80:
        seat,_=world.pending();s=world.view(seat)
        events=[v for e in world.events[cursors[seat]:] if (v:=e.view(seat)) is not None]
        cursors[seat]=len(world.events)
        s.update(player=seat,seq=steps+1,game_id='offline-public-case',timeout_s=2,events=events)
        history[seat].extend(s.get('events',[]));s=with_public_history(s,history[seat])
        intervention=seat==1 and world.turn==start_turn
        if intervention:
            route=job['route']
            if route in ('replan','committed'):
                action,info=candidate(s,cfg,memory=memory)
            elif route.startswith('diagnostic_'):
                from development.secret_hunter_turn_plans.diagnostic_routes import override
                action,info=candidate(s,{**cfg,'continuation_memory':False},memory=None)
                if info.get('reason')!='guaranteed_lethal':
                    replacement=override(s,route,memory,expand(s))
                    if replacement is not None:
                        action=replacement;info={'reason':'offline_reactive_diagnostic'}
            else:
                action,info=frozen(s,base_cfg)
                if info.get('reason')!='guaranteed_lethal':
                    if not planned or not model.supported(s) or expected!=key(model.prepare(s)):
                        selected,report=choose(s,cfg,time.monotonic()+.20,route)
                        planned=selected['sequence'] if selected else []
                    if planned and planned[0] in expand(s):
                        action=planned.pop(0)
                        successor=model.transition(model.prepare({**s,'planning_mode':'response'}),action) if action['type']!='end_turn' else None
                        expected=key(successor) if successor else None
            visible={c['entity_id']:c['card_id'] for side in ('you','opponent') for c in s[side]['board']+[s[side]['hero']]+s[side].get('hand',[])}
            trace.append({'seq':s.get('seq'),'turn':s['turn'],'action':action,
                          'card':visible.get(action.get('card')),'attacker':visible.get(action.get('attacker')),
                          'target':visible.get(action.get('target')),'reason':info.get('reason')})
        elif seat==1:action,_=frozen(s,base_cfg)
        else:
            response_view=s
            if scenario=='no_coil' and job.get('strict_no_coil') and world.turn==start_turn+1:
                coil_ids={c['entity_id'] for c in s['you']['hand'] if c['card_id']=='EX1_302'}
                response_view={**s,'legal_actions':[a for a in s['legal_actions']
                    if not (a['type']=='play_card' and a['card'] in coil_ids)]}
            action=foe.fn(response_view)
            if scenario=='forced_coil' and world.turn==start_turn+1 and not forced_used:
                coil=next((c for c in s['you']['hand'] if c['card_id']=='EX1_302'),None)
                amani=next((m for m in s['you']['board'] if m['card_id']=='EX1_393' and not m.get('silenced')
                            and (not job.get('strict_coil') or (m['health']==m['max_health'] and m['health']>1))),None)
                special={'type':'play_card','card':coil['entity_id'],'target':amani['entity_id']} if coil and amani else None
                if special in expand(s):action=special;forced_used=True
        accepted=world.step(seat,action)
        if not accepted.accepted:raise ValueError(('illegal offline intervention',seat,action,accepted))
        if intervention:end_turn_state=world.view(1)
        if job.get('trace'):full.append({'seat':seat,'turn':s['turn'],'state':s,'action':action})
        steps+=1
        if response is None and (world.over or world.turn>=start_turn+2):
            after=world.view(1);response={'survived':world.winner!=2,'hp':after['you']['hero']['health'],
                    'enemy_hp':after['opponent']['hero']['health'],'own_attack':sum(m['attack'] for m in after['you']['board']),
                    'enemy_attack':sum(m['attack'] for m in after['opponent']['board'])}
    return {'case':source['case'],'kind':source['kind'],'split':source['split'],'source_seed':source['source_seed'],
            'source_game':source['source_game'],'route':job['route'],'sample':job['sample'],'scenario':scenario,
            'candidate':job.get('candidate','R1-memory'),'terminal':world.over,'winner':world.winner,'win':int(world.winner==1),'sequence':trace,
            'strict_no_coil_response_control':bool(job.get('strict_no_coil') and scenario=='no_coil'),
            'end_tested_turn':end_turn_state,
            'after_response':response,'steps':steps,'seconds':time.monotonic()-start,'forced_coil_played':forced_used,
            'audit_hidden_hypothesis':{'own_deck':own_deck,'opponent_hand':hand,'opponent_deck':deck,'initial_rng_seed':seed+17},
            'public_features':source['public_features'],'full_trace':full,
            'scope':'Offline conditional hidden-card sample; only the tested own turn differs between paired routes. Frozen Y1 and original opponent policy thereafter, except the explicitly forced Coil response or strict no-Coil response control when flagged.'}


def main():
    job=json.loads(Path(sys.argv[1]).read_text())
    from development.secret_hunter_mcgs.train import atomic
    try:row=run(job)
    except Exception:
        import traceback
        row={'error':traceback.format_exc(),'job':job}
    atomic(Path(job['result']),row)


if __name__=='__main__':main()
