"""Descriptive opening/card exposure on seen development games only."""
import collections,json,time
from development.secret_hunter_astra_sprint.study import RUN,ROOT
from development.secret_hunter_astra_sprint import ledger

def main():
    db=ledger.connect(RUN);groups=collections.defaultdict(collections.Counter);cases=[]
    for batch in ('diagnostic-dev','round1-recall'):
        for q in db.execute("select result from tasks where batch=? and candidate='DARCL2' and status='done'",(batch,)):
            r=json.loads(q[0]);assert 62150000<=r['seed']<62160000
            if r['group']!='astra':continue
            folder=RUN/'batches'/batch/'DARCL2'/'games'/r['game'];logs=[json.loads(z) for z in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()]
            opening=next(z for z in logs if z['state']['phase']=='mulligan');mains=[z for z in logs if z['state']['phase']=='main'];c=groups[r['opponent'],int(r['score'])];c['games']+=1
            hand=opening['state']['you']['hand'];ids={x['entity_id']:x for x in hand}
            arc=any(x['card_id']=='DS1_185' for x in hand);low=any(x.get('type')=='MINION' and x['cost']<=2 for x in hand)
            c['arcane_initial']+=arc;c['arcane_plus_low_minion']+=arc and low
            per={};unaffordable=set();unused=set();seen=set();played=set()
            for z in mains:
                s=z['state'];y=s['you'];t=y['max_mana'];per[t]=s
                seen.update(x['card_id'] for x in y['hand'])
                if z['action']['type']=='play_card':
                    card=next(x for x in y['hand'] if x['entity_id']==z['action']['card']);played.add(card['card_id'])
                if 2<=t<=5 and not y['board']:
                    for x in y['hand']:
                        if x['cost']>y['mana']:unaffordable.add(x['card_id'])
            for t in (2,3,4,5):
                if t in per:
                    c[f'reached_T{t}']+=1;c[f'empty_at_end_T{t}']+=not per[t]['you']['board']
            for cid in seen:c['drawn_'+cid]+=1
            for cid in played:c['played_'+cid]+=1
            for cid in seen-played:c['never_played_'+cid]+=1
            for cid in unaffordable:c['empty_board_unaffordable_'+cid]+=1
            if arc:
                cases.append({'batch':batch,'seed':r['seed'],'opponent':r['opponent'],'seat':r['seat'],'actual_first':r['first_player']==r['seat'],'win':r['score'],'low_minion':low,
                    'opening':opening,'early':[z for z in mains if z['state']['you']['max_mana']<=3]})
    result={'created':time.time(),'scope':'Seen full development only; descriptive exposure is not a causal card/mulligan comparison.',
        'groups':{f'{k[0]}:win{k[1]}':dict(v) for k,v in groups.items()},'arcane_openings':cases}
    ledger.atomic(RUN/'opening-resource-diagnosis.json',result)
    for k,v in groups.items():print(k,{x:y for x,y in v.items() if not x.startswith(('drawn_','played_','never_played_','empty_board_unaffordable_'))})
    print('arcane loss sources',[(r['seed'],r['opponent'],r['seat'],r['low_minion']) for r in cases if not r['win']])
if __name__=='__main__':main()
