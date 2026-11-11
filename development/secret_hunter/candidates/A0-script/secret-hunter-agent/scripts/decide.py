"""Bounded preparation and verified model selection. Never calls another model or act."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from action_validator import legal, fallback
from budget import Budget

ROOT=Path(__file__).resolve().parents[1]


def read_state(path):
    state=json.loads(path.read_text())
    history=path.parent/'history.jsonl'
    if history.exists():
        from state_features import with_public_history
        state=with_public_history(state,[json.loads(s) for s in history.read_text().splitlines() if s])
    return state


def basic(state):
    if state['phase']=='deck_submission':
        from hs_arena.deck import load_deck
        d=load_deck(ROOT/'deck.json')
        return {'type':'submit_deck',**d.to_json()}
    return fallback(state)


def log(row):
    scratch=ROOT/'scratch';scratch.mkdir(exist_ok=True)
    with (scratch/'decisions.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',default='game/state.json')
    p.add_argument('--worker',action='store_true');p.add_argument('--deep',action='store_true')
    p.add_argument('--select',type=int);p.add_argument('--seq',type=int)
    p.add_argument('--reason',default='');p.add_argument('--action',help='Proposed action JSON, checked against current templates')
    p.add_argument('--fallback',action='store_true');args=p.parse_args()
    path=Path(args.state).resolve();s=read_state(path);cfg=json.loads((ROOT/'config.json').read_text())
    identity={'game_id':s.get('game_id'),'seq':s['seq']}
    if s['phase']=='game_over':print(json.dumps({**identity,'game_over':True}));return
    budget=Budget(s,cfg);started=time.monotonic()
    if args.worker:
        from secret_policy import analyze
        print(json.dumps(analyze(s,cfg,args.deep)));return
    scratch=ROOT/'scratch';scratch.mkdir(exist_ok=True);cache=scratch/'pending.json'
    if args.select is not None or args.action:
        old=json.loads(cache.read_text()) if cache.exists() else {}
        if args.seq!=s['seq'] or any(old.get(k)!=v for k,v in identity.items()):
            log({**identity,'event':'rejected_stale','requested_seq':args.seq})
            print(json.dumps({**identity,'refresh_required':True}));return
        if old.get('selected'):
            log({**identity,'event':'rejected_duplicate'})
            print(json.dumps({**identity,'duplicate':True,'refresh_required':True}));return
        action=old['candidates'][old['default_id']]['action'];status='adopted'
        try:
            proposed=json.loads(args.action) if args.action else next(c['action'] for c in old['candidates'] if c['id']==args.select)
            if not legal(s,proposed):raise ValueError('illegal proposal')
            if not budget.accepts_model():status='late_default'
            elif not cfg.get('model_authority',True):status='authority_disabled'
            else:action=proposed
        except (ValueError,StopIteration,TypeError):status='invalid_default'
        latest=json.loads(path.read_text())
        if latest['seq']!=s['seq'] or latest.get('game_id')!=s.get('game_id'):
            print(json.dumps({'refresh_required':True}));return
        old['selected']=True;cache.write_text(json.dumps(old))
        log({**identity,'event':'model_selection','status':status,'choice':args.select,'reason':args.reason[:240],
             'action':action,'different_from_default':action!=old['candidates'][old['default_id']]['action'],
             'publication_elapsed_s':time.time()-budget.published,'remaining_s':budget.remaining()})
        print(json.dumps({**identity,'action':action,'selection_status':status}));return
    action=basic(s);error=None
    result={'candidates':[{'id':0,'action':action,'plan':'legal_fallback'}],'default_id':0,'model_needed':False}
    if s['phase']!='deck_submission' and not args.fallback and budget.tool_limit(args.deep)>.08:
        try:
            command=[sys.executable,str(Path(__file__).resolve()),'--state',str(path),'--worker']
            if args.deep:command.append('--deep')
            proc=subprocess.run(command,capture_output=True,text=True,timeout=budget.tool_limit(args.deep),check=True)
            result=json.loads(proc.stdout)
            assert result['candidates'] and all(legal(s,c['action']) for c in result['candidates'])
        except (subprocess.SubprocessError,ValueError,AssertionError,OSError) as e:error=type(e).__name__
    if not budget.accepts_model():result['model_needed']=False
    result.update(identity,remaining_s=round(budget.remaining(),3),adoption_remaining_s=round(max(0,budget.adopt-time.monotonic()),3),
                  tool_elapsed_s=round(time.monotonic()-started,4),tool_error=error)
    if not result['model_needed']:result['action']=result['candidates'][result['default_id']]['action']
    cache.write_text(json.dumps(result))
    log({**result,'event':'prepared','phase':s['phase'],'deep':args.deep,
         'publication_elapsed_s':time.time()-budget.published,'has_client_mcp_env':bool(os.environ.get('HS_ARENA_MCP'))})
    print(json.dumps(result,separators=(',',':')))


if __name__=='__main__':main()
