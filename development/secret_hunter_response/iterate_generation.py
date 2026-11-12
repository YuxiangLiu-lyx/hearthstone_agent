"""Repair unfair baseline endpoint coverage diagnosed from a paired loss."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_response';W=ROOT/'development/secret_hunter_response';a=json.loads((D/'candidates.json').read_text())
for child,parent in [('B3','B2'),('C3','C2')]:
 dest=W/'candidates'/child;shutil.copytree(W/'candidates'/parent,dest,ignore=shutil.ignore_patterns('__pycache__','scratch'))
 cfg=json.loads((dest/'config.json').read_text());cfg.update(version='response-'+child,parent=parent);write(dest/'config.json',cfg)
 p=dest/'scripts/response_search.py';s=p.read_text();needle="    front=[(s,[])];seen=set();all_ends=[];nodes=0"
 insert="""    card=next((c for c in state['you']['hand'] if c['entity_id']==baseline.get('card')), {})
    if card.get('card_id')=='GAME_005':
        knives=any(x['card_id']=='NEW1_019' and not x.get('silenced') for x in state['you']['board'])
        if any(state['you']['mana']<c['cost']<=state['you']['mana']+1 and
               (c['card_id'] in ('NEW1_031','NEW1_019') or (knives and (c['type']=='MINION' or c['card_id']=='EX1_538')))
               for c in state['you']['hand']):
            return [],{'reason':'coin_followup_outside_deterministic_coverage','nodes':0}
"""
 assert needle in s;s=s.replace(needle,insert+needle)
 # Deduplication must retain root attribution, or a baseline prefix may only
 # survive as a dominated incomplete endpoint after its good suffix was merged.
 needle="                key=m.signature(q)\n                if key in seen:continue\n                seen.add(key);nxt.append((value(q,cfg),q,path+[a]))"
 assert needle in s;s=s.replace(needle,"                key=(json.dumps((path+[a])[0],sort_keys=True),m.signature(q))\n                if key in seen:continue\n                seen.add(key);nxt.append((value(q,cfg),q,path+[a]))")
 p.write_text(s);a[child]={'parent_ids':[parent],'status':'provisional','hypothesis':'Preserve baseline root attribution during state reuse and inherit the Coin/random-followup coverage guard.','evidence':'960100 Bot2-trade seat 1 seq 4: C2 compared Coin/end against Explosive Trap, missing Y1 Coin/Companion continuation.','source_sha256':fingerprint(dest)}
write(D/'candidates.json',a)
