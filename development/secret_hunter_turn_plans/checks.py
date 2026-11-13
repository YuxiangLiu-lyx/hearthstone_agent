"""Course-engine differential checks and complete CLI public-turn replays."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import RUN,ROOT
sys.path[:0]=[str(HERE/'candidates/R4-canonical-cache/scripts'),str(ROOT/'development/secret_hunter_mcgs')]
from mcgs_init import initialize
initialize()
from development.secret_hunter_mcgs.cases import fixture
from mcgs_world import build
from hearthstone.enums import Zone
from actions import legal
import tactical_model as model
import public_response as reply
import plan_cache as legacy
import continuation_cache as corrected


def decorate(world,seat,seq,history):
    state=world.view(seat)
    state.update(player=seat,seq=seq,game_id='public-replay',timeout_s=2,events=[])
    return state


def main():
    results={};differentials=[]
    for cards in [('EX1_556',),('EX1_029',),('EX1_393',),('EX1_556','EX1_162','CS2_171')]:
        e=fixture(enemy=cards,mana=5);p,q=e.player(1),e.player(2)
        p.card('EX1_610',zone=Zone.SECRET)
        if cards[0]=='EX1_556':q.field[0].damage=1
        state=e.view(1);a={'type':'attack','attacker':q.field[0].entity_id,'target':p.hero.entity_id}
        expected=reply.attack(reply.prepare_reply(model.prepare(state)),a)
        e.step(1,{'type':'end_turn'});assert e.step(2,a).accepted;actual=e.view(1)
        def summary(s):return {'hp':s['you']['hero']['health'],'enemy_hp':s['opponent']['hero']['health'],
                              'board':[(m['card_id'],m['attack'],m['health']) for m in s['opponent']['board']]}
        assert summary(expected)==summary(actual)
        differentials.append({'enemy':cards,'prediction':summary(expected),'engine':summary(actual)})
    results['existing_trap_model_retested']=differentials
    e=fixture(hand=['EX1_029','EX1_080'],mana=3);s=decorate(e,1,1,[])
    first,second=s['you']['hand'];sequence=[{'type':'play_card','card':first['entity_id'],'position':0},
                                          {'type':'play_card','card':second['entity_id'],'position':1}]
    cfg={'_deadline':time.monotonic()+5};old={};new={}
    legacy.save(s,cfg,sequence,old,time.monotonic()+2)
    assert corrected.save(s,cfg,sequence,new,time.monotonic()+2)==1
    assert e.step(1,sequence[0]).accepted;s2=decorate(e,1,2,[]);cfg2={**cfg,'_deadline':time.monotonic()+6}
    assert legacy.take(s2,cfg2,old) is None
    changed=copy.deepcopy(s2);changed['you']['hero']['health']-=1
    stale,reason=corrected.take(changed,cfg2,copy.deepcopy(new));assert stale is None and reason=='public_state_changed'
    action,reason=corrected.take(s2,cfg2,new);assert action==sequence[1] and legal(s2,action)
    results['cache_regression']={'legacy':'invalidated by per-invocation _deadline','corrected_action':action,
                                 'stale_state_rejected':True,'legal':True}
    replays=[]
    names=['trap-008','knife_wolf-006','amani-003']
    for name in names:
        source=json.loads((RUN/'mined'/f'{name}.json').read_text())
        for arm in ['Y1','R0-trap-reference','R4-canonical-cache']:
            candidate=Y1 if arm=='Y1' else HERE/'candidates'/arm
            world=build(source['state'],701);start=world.turn;history=[];cursor=0;sequence=[]
            with tempfile.TemporaryDirectory(prefix='krush-turn-cli-') as tmp:
                root=Path(tmp)/'skill';shutil.copytree(candidate,root,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
                (root/'game').mkdir()
                for index in range(30):
                    if world.over or world.turn!=start:break
                    s=decorate(world,1,index+1,history)
                    events=[v for ev in world.events[cursor:] if (v:=ev.view(1)) is not None];cursor=len(world.events)
                    s['events']=events;history.extend(events)
                    (root/'game/state.json').write_text(json.dumps(s));(root/'game/history.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in history))
                    before=time.monotonic()
                    proc=subprocess.run([sys.executable,'scripts/decide.py'],cwd=root,capture_output=True,text=True,timeout=2.1,check=True)
                    elapsed=time.monotonic()-before;out=json.loads(proc.stdout);assert out['seq']==s['seq'] and legal(s,out['action']) and elapsed<2
                    info=json.loads((root/'scratch/decisions.jsonl').read_text().splitlines()[-1])
                    assert not info.get('worker_error')
                    assert world.step(1,out['action']).accepted
                    sequence.append({'action':out['action'],'elapsed_s':elapsed,'reason':info['info'].get('reason'),'routes':info['info'].get('turn_routes')})
                assert world.over or world.turn!=start
                # Exercise the actual deployment entrypoint's ordered deck output.
                deck_state={'phase':'deck_submission','seq':100,'game_id':'deck-audit'}
                (root/'game/state.json').write_text(json.dumps(deck_state))
                out=json.loads(subprocess.check_output([sys.executable,'scripts/decide.py'],cwd=root,text=True))
                assert out['action']['cards']==json.loads((Y1/'deck.json').read_text())['cards']
            replays.append({'source':name,'arm':arm,'sequence':sequence,'final_public_state':world.view(1),'deck_submission_exact':True})
    results['reconstructed_public_replays']=replays
    results['limitation']='The unavailable 0066a30 replay inputs cannot be reproduced. These are newly mined original-deck public cases, explicitly separate from prior claims.'
    dest=ROOT/'docs/secret_hunter_turn_plans';dest.mkdir(parents=True,exist_ok=True)
    (dest/'mechanisms-and-cli-replays.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'differentials':len(differentials),'cache_regression_passed':True,'full_cli_turn_replays':len(replays),
                      'calls':sum(len(r['sequence']) for r in replays),'max_seconds':max(x['elapsed_s'] for r in replays for x in r['sequence'])}))


if __name__=='__main__':main()
