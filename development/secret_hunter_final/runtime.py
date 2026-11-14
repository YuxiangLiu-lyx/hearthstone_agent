"""Actual CLI phases, fault fallback, stale sequence and terminal protocol checks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
from development.secret_hunter_final.study import HERE,RUN,ROOT
from development.secret_hunter_mcgs.runtime import probe
from development.secret_hunter_program.common import quantiles
from development.secret_hunter_mcgs import train

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);a=p.parse_args()
    source=Path(a.candidate).resolve()
    sys.path.insert(0,str(source/'scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()
    from development.secret_hunter_mcgs.cases import fixture
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    from hs_arena.skill.mcp_server import act
    from action_validator import legal
    records=[];states=[]
    manifest=json.loads((RUN/'early-sources/manifest.json').read_text())
    for cid in manifest['cases']:
        states.append(json.loads((RUN/'early-sources'/(cid+'.json')).read_text())['state'])
    states.sort(key=lambda s:len(s['you']['board'])*len(s['opponent']['board'])+len(s['you']['hand']),reverse=True)
    for s in states[:8]:records.append(probe(source,s,'cold'))
    with ThreadPoolExecutor(max_workers=3) as pool:
        records.extend(pool.map(lambda i:probe(source,states[i],'concurrent'),range(3)))
    found=set()
    for seed in range(10):
        e=Engine(load_deck(source/'deck.json'),load_deck(ROOT/'development/teacher_eval/decks/astra-doubled.json'),seed)
        first=e.first_player==1
        if first in found:continue
        found.add(first);s=e.view(1);s.update(seq=1,player=1,game_id='mulligan-check')
        r=probe(source,s,'mulligan-first' if first else 'mulligan-second');records.append(r)
        assert e.step(1,r['action']).accepted
        if len(found)==2:break
    e=fixture(hand=['DS1_184'],mana=3);card=e.view(1)['you']['hand'][0]
    assert e.step(1,{'type':'play_card','card':card['entity_id']}).accepted
    s=e.view(1);assert s['phase']=='choice';s.update(seq=77,player=1,game_id='choice-check')
    r=probe(source,s,'tracking-choice');records.append(r);assert e.step(1,r['action']).accepted
    e=fixture(mana=1);e.player(1).used_mana=1;s=e.view(1);s.update(seq=88,player=1,game_id='end-check')
    r=probe(source,s,'only-end-turn');records.append(r);assert r['action']=={'type':'end_turn'} and e.step(1,r['action']).accepted
    e=fixture(own=['NEW1_019'],enemy=['CS2_200','CS2_200'],hand=['EX1_538'],mana=3)
    s=e.view(1);s.update(seq=89,player=1,game_id='random-check')
    r=probe(source,s,'juggler-hounds');records.append(r);assert e.step(1,r['action']).accepted
    hang='import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n'
    crash='def decide(*args,**kwargs):\n raise RuntimeError("injected crash")\n'
    publish='import time\nfrom secret_policy import rank\ndef decide(state,config,publish=None,**kwargs):\n a=rank(state,config)[0][1]\n publish(a,{"fallback":False,"reason":"published_before_hang"})\n time.sleep(20)\n'
    for tag,body in [('hang',hang),('crash',crash),('published_hang',publish)]:
        records.append(probe(source,states[0],tag,body))
    for i in range(4):records.append(probe(source,states[0],'stale-'+str(i),hang,stale=True))
    records.append(probe(source,{'phase':'game_over','seq':999},'game_over'))
    with tempfile.TemporaryDirectory(prefix='stale-host-') as tmp:
        box=Path(tmp);(box/'state.json').write_text(json.dumps({'seq':2,'phase':'main'}));(box/'state.txt').write_text('pending seq 2')
        reply=act(box,{'seq':1,'action':{'type':'end_turn'}})
        stale_host='nothing submitted' in reply and not (box/'action.json').exists()
        assert stale_host
    ordinary=[r for r in records if r['tag'] not in ('hang','crash','published_hang') and not r['tag'].startswith('stale')]
    data={'candidate':str(source),'calls':len(records),'invalid':sum(not r['valid'] for r in records),
          'over_2s':sum(r['elapsed_s']>2 for r in records),'ordinary_fallbacks':sum(bool(r['fallback']) for r in ordinary),
          'ordinary_latency_s':quantiles([r['elapsed_s'] for r in ordinary]),
          'all_including_fault_latency_s':quantiles([r['elapsed_s'] for r in records]),
          'injected_fault_fallbacks':sum(bool(r['fallback']) for r in records if r['tag'] in ('hang','crash','published_hang')),
          'actual_host_stale_seq_rejected':stale_host,'records':records,
          'course_hard_limit_s':180,'engineering_full_python_cli_target_s':2,
          'luna_relay':'not measured: local codex launcher fails ENOENT for its vendor binary; no model substitute'}
    train.atomic(ROOT/'docs/secret_hunter_final/runtime.json',data)
    print(json.dumps({k:v for k,v in data.items() if k!='records'}))
    assert data['invalid']==data['over_2s']==data['ordinary_fallbacks']==0

if __name__=='__main__':main()
