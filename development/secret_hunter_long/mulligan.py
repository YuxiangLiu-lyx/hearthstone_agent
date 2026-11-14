"""Actual-engine opening subsets; source selection uses public opening only."""
import argparse
from collections import Counter
import hashlib
import json
import sys
from development.secret_hunter_long.study import HERE,RUN,ROOT
from development.secret_hunter_long.cfqueue import reserve
from development.secret_hunter_mcgs.train import atomic

def setup(arm):
    sys.path.insert(0,str(HERE/'candidates'/arm/'scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()

def features(s):
    hand=s['you']['hand'];ids=Counter(c['card_id'] for c in hand);hc=s['opponent']['hero']['hero_class']
    low=[c for c in hand if c['type']=='MINION' and c['cost']<=2]
    return {'second':int(len(hand)==4),'warlock':int(hc=='WARLOCK'),'hunter':int(hc=='HUNTER'),
        'pressure':int(hc in ('WARLOCK','HUNTER','PALADIN','SHAMAN')),'low':len(low),
        'ones':sum(c['type']=='MINION' and c['cost']==1 for c in hand),
        'keeper':ids['EX1_080'],'explosive':ids['EX1_610'],'bow':ids['EX1_536'],
        'juggler':ids['NEW1_019'],'hyena':ids['EX1_531'],'hounds':ids['EX1_538'],
        'arcane':ids['DS1_185'],'secrets':sum(ids[c] for c in ('EX1_610','EX1_611','EX1_554','EX1_533'))}

def options(s):
    from tactics_rank import mulligan
    base=mulligan(s);f=features(s);hand=s['you']['hand'];ids=[c['entity_id'] for c in hand]
    kept=set(ids)-set(base['replace']);choices={'baseline':base,'all_replace':{'type':'mulligan','replace':ids}}
    def change(name,cid,keep):
        cs=[c['entity_id'] for c in hand if c['card_id']==cid]
        if not cs:return
        k=set(kept)
        if keep:k.add(cs[0])
        else:k.difference_update(cs)
        choices[name]={'type':'mulligan','replace':[i for i in ids if i not in k]}
    if f['explosive'] and f['warlock'] and not f['low']:change('trap_no_low','EX1_610',True)
    if f['bow'] and f['second'] and f['low']:
        change('keep_coin_bow','EX1_536',True);change('drop_coin_bow','EX1_536',False)
    if f['hounds'] and (f['juggler'] or f['hyena']):
        change('keep_combo_hounds','EX1_538',True);change('drop_combo_hounds','EX1_538',False)
    if f['keeper'] and f['secrets']:
        k=kept-{c['entity_id'] for c in hand if c['card_id'] in ('EX1_610','EX1_611','EX1_554','EX1_533')}
        choices['drop_keeper_secret']={'type':'mulligan','replace':[i for i in ids if i not in k]}
    if f['arcane'] and (f['warlock'] or f['hunter']):
        change('keep_arcane','DS1_185',True);change('drop_arcane','DS1_185',False)
    return choices

def mine(arm,start,seeds,mode,cap):
    setup(arm)
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    pop=json.loads((ROOT/'development/teacher_eval/core.json').read_text())
    sources=[];counts=Counter();tested=0
    for seed in range(start,start+seeds):
        for spec in pop:
            for seat in (1,2):
                decks={seat:load_deck(HERE/'candidates'/arm/'deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
                e=Engine(decks[1],decks[2],seed,max_turns=180);s=e.view(seat);tested+=1
                f=features(s);opts=options(s)
                hit=[k for k,v in opts.items() if k not in ('baseline','all_replace') and v!=opts['baseline']]
                counts.update(hit)
                if mode=='matched' and not hit:continue
                cid=f'm-{arm}-{seed}-{spec["name"]}-s{seat}'
                source={'case':cid,'arm':arm,'seed':seed,'seat':seat,'opponent_spec':spec,'state':s,
                    'features':f,'split':'validation' if seed%5 in (0,1) else 'train','opening_hand':[(c['entity_id'],c['card_id']) for c in s['you']['hand']],
                    'options':opts,'mode':mode,'public_triggers':hit}
                sources.append(source)
    # Fair seed spread rather than first-N games: rotate independent seed groups.
    grouped={seed:[s for s in sources if s['seed']==seed] for seed in sorted({s['seed'] for s in sources})}
    for seed,group in grouped.items():
        offset=seed%len(group);grouped[seed]=group[offset:]+group[:offset]
    chosen=[]
    for i in range(max((len(v) for v in grouped.values()),default=0)):
        for group in grouped.values():
            if i<len(group) and len(chosen)<cap:chosen.append(group[i])
    jobs=[]
    for src in chosen:
        atomic(RUN/'mulligan-sources'/(src['case']+'.json'),src)
        ids=[x[0] for x in src['opening_hand']]
        actions={}
        for name,action in src['options'].items():actions.setdefault(tuple(action['replace']),[]).append(name)
        if mode=='exhaustive':
            for mask in range(1<<len(ids)):actions.setdefault(tuple(x for i,x in enumerate(ids) if mask&(1<<i)),[]).append(f'mask{mask}')
        # Expanded sample uses baseline/all + at most three representative alternatives.
        if mode=='matched':actions=dict(list(actions.items())[:5])
        for ix,(replace,names) in enumerate(actions.items()):
            jobs.append((src['case']+f'-a{ix}',{'case':src['case'],'replace':list(replace),'aliases':names,'arm':arm}))
    manifest={'arm':arm,'mode':mode,'start':start,'seeds':seeds,'openings_examined':tested,
        'public_trigger_counts':dict(counts),'eligible':len(sources),'selected':len(chosen),
        'selected_seed_groups':len({s['seed'] for s in chosen}),'cases':[s['case'] for s in chosen],
        'jobs':len(jobs),'selection':'v2: public own opening, public enemy class, actual first/second only; seed round-robin cap and opponent/seat rotation',
        'outcome_scope':'conditional matched sample, not whole-pool win rate'}
    atomic(RUN/'mulligan-sources'/f'manifest-{arm}-{start}.json',manifest);reserve('mulligan',jobs)
    print(json.dumps(manifest))

def execute(job):
    setup(job['arm'])
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    from development.secret_hunter_tactics.run import opponent
    from program_policy import decide
    from action_validator import legal
    from state_features import with_public_history
    src=json.loads((RUN/'mulligan-sources'/(job['case']+'.json')).read_text());seat=src['seat'];spec=src['opponent_spec']
    decks={seat:load_deck(HERE/'candidates'/job['arm']/'deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
    e=Engine(decks[1],decks[2],src['seed'],max_turns=180)
    s=e.view(seat);assert [(c['entity_id'],c['card_id']) for c in s['you']['hand']]==[tuple(x) for x in src['opening_hand']]
    cfg=json.loads((HERE/'candidates'/job['arm']/'config.json').read_text());foe=opponent(spec)
    # Engine requests player 1's mulligan before player 2's, independent of
    # the eventual first player. Preserve that exact protocol and RNG order.
    if e.pending()[0]!=seat:
        other=e.pending()[0];os=e.view(other);assert os['phase']=='mulligan'
        oa=foe.fn(os);assert legal(os,oa) and e.step(other,oa).accepted
    assert e.step(seat,{'type':'mulligan','replace':job['replace']}).accepted
    trace=[];opening={};first_play={};post_hand=None
    for step in range(700):
        if e.over:break
        active,_=e.pending();s=e.view(active);history=[v for ev in e.events if (v:=ev.view(active)) is not None]
        s.update(player=active,seq=step+1,game_id='offline-opening',timeout_s=2,events=[]);s=with_public_history(s,history)
        if active==seat:
            action,info=decide(s,cfg);assert not info.get('error')
            if s['phase']=='main':
                y=s['you'];o=s['opponent'];t=str(y['max_mana'])
                if post_hand is None:post_hand=[(c['entity_id'],c['card_id']) for c in y['hand']]
                if t not in opening and int(t)<=3:opening[t]={'hp':y['hero']['health'],'board_attack':sum(x['attack'] for x in y['board']),'board':len(y['board']),'enemy_attack':sum(x['attack'] for x in o['board'])}
                if action['type']=='play_card':
                    card=next(c for c in y['hand'] if c['entity_id']==action['card']);first_play.setdefault(str(card['entity_id']),y['max_mana'])
                if action['type']=='end_turn' and int(t)<=3:opening[t].update(end_board=len(y['board']),end_attack=sum(x['attack'] for x in y['board']),unused_mana=y['mana'])
        else:action=foe.fn(s)
        assert legal(s,action)
        trace.append({'seat':active,'turn':s['turn'],'action':action})
        assert e.step(active,action).accepted
    assert e.over,'nonterminal opening continuation'
    return {'case':src['case'],'source_seed':src['seed'],'seat':seat,'opponent':spec['name'],'split':src['split'],
        'features':src['features'],'win':int(e.winner==seat),'winner':e.winner,'terminal':True,
        'post_mulligan_hand':post_hand,'opening':opening,'first_play_mana_turn':first_play,'trace':trace,
        'rng_note':'same initial engine seed; actual mulligan replacement count may change all later draws/RNG consumption'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--start',type=int,required=True)
    p.add_argument('--seeds',type=int,required=True);p.add_argument('--mode',choices=['exhaustive','matched'],default='matched');p.add_argument('--cap',type=int,default=160)
    a=p.parse_args();mine(a.arm,a.start,a.seeds,a.mode,a.cap)
