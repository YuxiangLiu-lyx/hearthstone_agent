"""Descriptive exposure and exact damage attribution; no counterfactual claims."""
import argparse
from collections import Counter,defaultdict
import json
from development.secret_hunter_long.study import RUN,HERE
from development.secret_hunter_mcgs.train import atomic,connect

TESTED=('EX1_543','DS1_185','EX1_162','EX1_066','EX1_533','EX1_008','EX1_010')
def inspect_game(row,batch,arm):
    folder=RUN/'batches'/batch/arm/'games'/row['game']
    logs=[json.loads(l) for l in (folder/f"p{row['seat']}"/'observations.jsonl').read_text().splitlines()]
    events=[json.loads(l) for l in (folder/'replay.jsonl').read_text().splitlines()]
    mull=next(r for r in logs if r['state']['phase']=='mulligan')
    cards={};mana_turns={};last={};damage=defaultdict(Counter);coin=[];turn_actions=defaultdict(list)
    for rec in logs:
        s=rec['state'];a=rec.get('action') or {};y=s.get('you') or {};o=s.get('opponent') or {}
        if s['phase']=='main':
            mana=y['max_mana'];mana_turns.setdefault(mana,rec);last[mana]=rec
            turn_actions[mana].append(a)
        for c in y.get('hand',[]):
            cid=c['card_id'];eid=c['entity_id']
            if cid not in TESTED:continue
            v=cards.setdefault(eid,{'card_id':cid,'entity':eid,'initial':False,'replaced':False,'received_after_mulligan':False,'first_playable':None,'plays':[]})
            if s['phase']=='mulligan':v.update(initial=True,replaced=eid in a.get('replace',[]))
            elif s['phase']=='main':
                v['received_after_mulligan']=True
                if c.get('playable') and v['first_playable'] is None:v['first_playable']={'turn':s['turn'],'mana_turn':y['max_mana'],'seq':s['seq']}
                if a.get('type')=='play_card' and a.get('card')==eid:
                    v['plays'].append({'turn':s['turn'],'mana_turn':y['max_mana'],'seq':s['seq'],'target':a.get('target')})
        if a.get('type')=='play_card':
            c=next((c for c in y.get('hand',[]) if c['entity_id']==a.get('card')),None)
            if c and c['card_id']=='GAME_005':coin.append({'seq':s['seq'],'mana_turn':y['max_mana'],'turn':s['turn']})
    for e in events:
        if e['event']=='damage' and e.get('source'):
            src=e['source'];cid=src.get('card_id')
            if src.get('entity_id') in cards:
                damage[cid]['enemy_hero' if e['player']!=row['seat'] and str(e.get('card_id','')).startswith('HERO_') else 'enemy_minion' if e['player']!=row['seat'] else 'friendly']+=e.get('amount',0)
    max_mana=max(mana_turns,default=0)
    opening={}
    for t in (1,2,3):
        first=mana_turns.get(t);end=last.get(t)
        if first:
            y=first['state']['you'];o=first['state']['opponent'];ey=end['state']['you']
            opening[str(t)]={'start_attack':sum(m['attack'] for m in y['board']),'start_hp':y['hero']['health'],
                'enemy_attack':sum(m['attack'] for m in o['board']), 'start_board':len(y['board']),
                'end_board':len(ey['board']),'end_attack':sum(m['attack'] for m in ey['board']),
                'end_unused_mana':ey['mana'],'end_hp':ey['hero']['health']}
    return {'key':[row['opponent'],row['seed'],row['seat']],'win':row['score'],'group':row['group'],
       'actual_first':row['first_player']==row['seat'],'duration_mana':max_mana,'duration_band':'<=5' if max_mana<=5 else '6-8' if max_mana<=8 else '9+',
       'cards':list(cards.values()),'damage':{k:dict(v) for k,v in damage.items()},'opening':opening,'coin':coin,
       'mulligan':{'hand':[c['card_id'] for c in mull['state']['you']['hand']],'action':mull['action']},
       'game_path':str(folder),'last_action':logs[-1]['action']}

def summarize(games):
    result={'n':len(games),'wins':sum(g['win'] for g in games),'cards':{},'opening':{}}
    for cid in TESTED:
        cs=[c for g in games for c in g['cards'] if c['card_id']==cid]
        result['cards'][cid]={'initial_copies':sum(c['initial'] for c in cs),'replaced_copies':sum(c['replaced'] for c in cs),
            'received_copies':sum(c['received_after_mulligan'] for c in cs),'ever_playable_copies':sum(c['first_playable'] is not None for c in cs),
            'played_copies':sum(bool(c['plays']) for c in cs),'play_mana_turns':dict(Counter(p['mana_turn'] for c in cs for p in c['plays'])),
            'first_playable_mana_turns':dict(Counter(c['first_playable']['mana_turn'] for c in cs if c['first_playable'] is not None)),
            'first_play_delay_mana_turns':dict(Counter(c['plays'][0]['mana_turn']-c['first_playable']['mana_turn'] for c in cs if c['plays'] and c['first_playable'] is not None)),
            'games_received':sum(any(c['card_id']==cid and c['received_after_mulligan'] for c in g['cards']) for g in games),
            'games_played':sum(any(c['card_id']==cid and c['plays'] for c in g['cards']) for g in games),
            'wins_when_played':sum(g['win'] for g in games if any(c['card_id']==cid and c['plays'] for c in g['cards'])),
            'damage':dict(sum((Counter(g['damage'].get(cid,{})) for g in games),Counter()))}
    for t in ('1','2','3'):
        ts=[g['opening'][t] for g in games if t in g['opening']]
        result['opening'][t]={'observed':len(ts),'board_by_end':sum(x['end_board']>0 for x in ts),
            'start_attack_mean':sum(x['start_attack'] for x in ts)/len(ts) if ts else None,
            'hp_mean':sum(x['start_hp'] for x in ts)/len(ts) if ts else None}
    return result

def run(batch):
    db=connect(RUN);b=db.execute('select * from batches where id=?',(batch,)).fetchone();out={}
    for arm in json.loads(b['arms']):
        rows=[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done'",(batch,arm))]
        games=[inspect_game(r,batch,arm) for r in rows if not r.get('harness_error')]
        atomic(RUN/'analysis'/f'{batch}-{arm}-games.json',games)
        out[arm]={'all':summarize(games),'by_opponent':{v:summarize([g for g in games if g['key'][0]==v]) for v in sorted({g['key'][0] for g in games})},
            'by_actual_first':{str(v):summarize([g for g in games if g['actual_first']==v]) for v in (True,False)},
            'by_duration':{v:summarize([g for g in games if g['duration_band']==v]) for v in ('<=5','6-8','9+')}}
    atomic(RUN/'analysis'/f'{batch}.json',out)
    print(json.dumps({a:{'games':d['all']['n'],'wins':d['all']['wins'],'tested_cards':d['all']['cards']} for a,d in out.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');run(p.parse_args().batch)
