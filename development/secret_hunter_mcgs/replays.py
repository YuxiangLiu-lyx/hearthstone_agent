"""Paired conditional continuations of published student views and Krush translations.

All scenario cards are offline labels/hypotheses. Policies receive only Engine.view.
A plan is a reactive rule for the remaining turn, not a frozen random-outcome tape.
"""
from collections import Counter
import copy
import json
from pathlib import Path
import random
import sys
import time
from development.secret_hunter_mcgs.build import HERE,Y1
sys.path[:0]=[str(HERE),str(Y1/'scripts')]
from mcgs_init import initialize
initialize()
from mcgs_world import build,clone
from mcgs_search import rollout_action,reward,search,rank
from development.secret_hunter_mcgs.cases import ROOT,DECK
from actions import expand
from hearthstone.enums import Zone
from hs_arena.cards import load


def source_cases(run):
    rows=[json.loads(l) for l in (run/'submission2/decisions.jsonl').read_text().splitlines()]
    specs=[('wolf','bot2_03',7,['y1','face','wolf_then_face','all_trade']),
           ('tracking','bot2_03',22,['y1','companion_now','highmane_later']),
           ('amani','astra_02',22,['y1','face','amani_trade']),
           ('coin','bot1_02',4,['y1','coin_juggler','save_coin'])]
    return [(name,next(r for r in rows if suffix in r['source_game'] and r['state']['seq']==seq),plans) for name,suffix,seq,plans in specs]


def translate(world):
    """Replace the two Arcane Shot slots with Misdirection/Krush, preserving zones.

    This is a synthetic transfer fixture, not a claim the C2 game used this deck.
    Recompute legal views through the engine after replacement.
    """
    p=world.player(1);replacements=iter(['EX1_533','EX1_543']);changed=[]
    for zone in ('hand','deck','graveyard'):
        for card in list(getattr(p,zone)):
            if card.id!='DS1_185':continue
            target=next(replacements);old_id=card.entity_id;old_zone=card.zone;card.zone=Zone.SETASIDE
            world.game.manager.counter+=1;card.entity_id=world.game.manager.counter
            c=p.card(target,zone=old_zone);c.entity_id=old_id
            changed.append({'old':'DS1_185','new':target,'zone':zone,'entity_id':old_id})
    world._mark_seen()
    assert len(changed)==2,changed
    # Full original multiset includes spent, held, board and remaining cards;
    # generated Hounds are excluded from the collectible deck audit.
    canonical=Counter(json.loads(DECK.read_text())['cards'])
    actual=Counter(c.id for c in list(p.hand)+list(p.deck)+list(p.graveyard)+list(p.field)+list(p.secrets)+([p.weapon] if p.weapon else []) if c.id in load())
    assert actual==canonical,(actual-canonical,canonical-actual)
    return changed


def condition(world,kind,seed):
    """Replace only hypothetical hidden cards, keeping observed hand/deck sizes."""
    q=world.player(2);rng=random.Random(seed);pool=load();cls=q.hero.data.card_class.name
    desired=['DS1_175','EX1_531','CS2_171'][:len(q.hand)] if kind=='beasts' else []
    if kind=='coil':desired=[]
    seen=Counter(c.id for c in list(q.field)+list(q.graveyard)+([q.weapon] if q.weapon else []))
    nhand=len(q.hand);ndeck=len(q.deck)
    for c in list(q.hand)+list(q.deck):c.zone=Zone.SETASIDE
    reserve=Counter(desired)
    if kind=='coil':reserve['EX1_302']+=1
    available=[]
    for cid,c in pool.items():
        if c['card_class'] not in ('NEUTRAL',cls):continue
        copies=(1 if c['rarity']=='LEGENDARY' else 2)-seen[cid]-reserve[cid]
        available.extend([cid]*max(0,copies))
    rng.shuffle(available)
    while len(desired)<nhand:desired.append(available.pop())
    deck=[available.pop() for _ in range(ndeck-int(kind=='coil'))]
    if kind=='coil':deck.append('EX1_302')
    for cid in desired:q.card(cid,zone=Zone.HAND)
    for cid in deck:q.card(cid,zone=Zone.DECK)
    if kind=='no_coil':
        for c in list(q.hand)+list(q.deck):
            if c.id=='EX1_302':
                z=c.zone;c.zone=Zone.SETASIDE;q.card(available.pop(),zone=z)
    world.game.random.seed(seed)


def plan_action(state,name,cfg,rng):
    actions=expand(state);y,o=state['you'],state['opponent']
    if name=='y1':
        from program_policy import decide
        return decide(state,cfg)[0]
    if name in ('companion_now','highmane_later') and state['phase']=='choice':
        cid='NEW1_031' if name=='companion_now' else 'EX1_534'
        options=next(t for t in state['legal_actions'] if t['type']=='choose')['options']
        c=next(c for c in options if c['card_id']==cid)
        return {'type':'choose','options':[c['entity_id']]}
    attacks=[a for a in actions if a['type']=='attack']
    if name in ('face','wolf_then_face','all_trade','amani_trade') and attacks:
        priority={'wolf_then_face':'DS1_175','amani_trade':'EX1_393'}.get(name)
        if priority:
            targets={m['entity_id'] for m in o['board'] if m['card_id']==priority}
            a=next((a for a in attacks if a['target'] in targets),None)
            if a:return a
        if name=='all_trade':
            a=next((a for a in attacks if a['target']!=o['hero']['entity_id']),None)
            if a:return a
        a=next((a for a in attacks if a['target']==o['hero']['entity_id']),None)
        if a:return a
    if name=='coin_juggler':
        for cid in ('NEW1_019','GAME_005'):
            ids={c['entity_id'] for c in y['hand'] if c['card_id']==cid}
            a=next((a for a in actions if a.get('card') in ids),None)
            if a:return a
    if name=='save_coin':
        ids={c['entity_id'] for c in y['hand'] if c['card_id']=='GAME_005'}
        ranked=[a for _,a in rank(state,cfg) if a.get('card') not in ids]
        if ranked:return ranked[0]
    if name=='companion_now':
        ids={c['entity_id'] for c in y['hand'] if c['card_id']=='NEW1_031'}
        a=next((a for a in actions if a.get('card') in ids),None)
        if a:return a
    return rollout_action(state,cfg,rng)


def continue_plan(world,plan,scenario,seed,trace=False):
    rng=random.Random(seed+991);cfg=json.loads((Y1/'config.json').read_text())
    start=world.turn;line=[];checkpoint=None;steps=0
    while not world.over and steps<600 and world.turn<start+70:
        seat,_=world.pending();s=world.view(seat)
        policy={**cfg,'_opponent':seat==2,'opponent_plays':scenario!='visible_only'}
        a=plan_action(s,plan,policy,rng) if seat==1 and world.turn==start else rollout_action(s,policy,rng)
        before=len(world.events);result=world.step(seat,a)
        assert result.accepted,(a,result)
        if trace:
            line.append({'turn':s['turn'],'seat':seat,'state':s,'action':a,
                         'events':[v for ev in world.events[before:] if (v:=ev.view(1)) is not None]})
        steps+=1
        if checkpoint is None and (world.over or world.turn>=start+2):
            s=world.view(1);checkpoint={'survived':world.winner!=2,'hp':s['you']['hero']['health'],
                'enemy_hp':s['opponent']['hero']['health'],'own_attack':sum(m['attack'] for m in s['you']['board']),
                'enemy_attack':sum(m['attack'] for m in s['opponent']['board'])}
    return {'win':int(world.winner==1),'terminal':world.over,'winner':world.winner,'steps':steps,
            'after_response':checkpoint,'trace':line}


def main():
    run=ROOT/'runs/krush-mcgs';out=run/'continuations-v2';out.mkdir(exist_ok=True)
    cfg=json.loads((Y1/'config.json').read_text());results=[];decisions=[];charged=0
    for name,row,plans in source_cases(run):
        scenarios=['visible_only','beasts'] if name=='wolf' else ['no_coil','coil'] if name=='amani' else ['sampled']
        # Selection samples 0..3 and validation samples 100..107 are disjoint.
        for seed in list(range(4))+list(range(100,108)):
            world=build(row['state'],20000+seed);changes=translate(world)
            for scenario in scenarios:
                w=clone(world,30000+seed);condition(w,scenario,30000+seed)
                for plan in plans:
                    charged+=1
                    r=continue_plan(clone(w,40000+seed),plan,scenario,50000+seed,trace=seed==100)
                    r.update(case=name,plan=plan,scenario=scenario,sample=seed,split='selection' if seed<100 else 'validation',
                             source_game=row['source_game'],source_seq=row['state']['seq'],original_action=row['original_action'],translation=changes)
                    if r['trace']:
                        path=out/f'{name}-{scenario}-{plan}-trace.json';path.write_text(json.dumps(r,indent=2)+'\n')
                        r['trace_path']=str(path.relative_to(ROOT));r['trace']=[]
                    results.append(r)
        # Offline reference versus the transition-limited fast search on the same public point.
        public=world.view(1);baseline=rank(public,cfg)[0][1]
        for label,cap,seconds in [('fast',350,2),('reference',4000,20)]:
            r=search(public,{**cfg,'graph':'ucd','chance':'dpw','max_transitions':cap,'iterations':500},baseline,time.monotonic()+seconds,seed=71)
            decisions.append({'case':name,'budget':label,**r})
        print(json.dumps({'case':name,'completed_continuations':charged}),flush=True)
    (out/'results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in results))
    (out/'search.json').write_text(json.dumps(decisions,indent=2)+'\n')
    summary=[]
    for name,_,plans in source_cases(run):
        for scenario in sorted({r['scenario'] for r in results if r['case']==name}):
            for plan in plans:
                rs=[r for r in results if r['case']==name and r['scenario']==scenario and r['plan']==plan and r['split']=='validation']
                summary.append({'case':name,'scenario':scenario,'plan':plan,'n':len(rs),'wins':sum(r['win'] for r in rs),
                    'survival':sum(bool(r['after_response']['survived']) for r in rs)/len(rs),
                    'mean_own_attack':sum(r['after_response']['own_attack'] for r in rs)/len(rs),
                    'mean_enemy_attack':sum(r['after_response']['enemy_attack'] for r in rs)/len(rs),
                    'terminal':sum(r['terminal'] for r in rs)})
    (ROOT/'docs/secret_hunter_mcgs/continuations.json').write_text(json.dumps({'attempts':charged,'groups':summary,'scope':'Synthetic original-deck translations of C2 development views; conditional hypotheses, not actual hidden cards or independent full games.'},indent=2)+'\n')
    print(json.dumps({'continuations':charged,'summary':summary}))
if __name__=='__main__':main()
