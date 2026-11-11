"""Supervised Python policy. No model selection or network access."""
import time
START=time.monotonic()
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from action_validator import legal
from fallback import basic
ROOT=Path(__file__).resolve().parents[1]


def atomic(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value));temp.replace(path)


def worker(snapshot,checkpoint):
    from program_policy import decide
    data=json.loads(snapshot.read_text());state=data['state'];cfg=data['config']
    cfg['_deadline']=data['search_deadline']
    memory=data.get('memory',{})
    def publish(action,info):atomic(checkpoint,{'action':action,'info':info,'memory':memory})
    action,info=decide(state,cfg,publish,memory=memory)
    publish(action,info)


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--fallback',action='store_true');args=p.parse_args()
    scratch=ROOT/'scratch';scratch.mkdir(exist_ok=True)
    snapshot=scratch/'input.json';checkpoint=scratch/'best.json'
    if args.worker:worker(snapshot,checkpoint);return
    path=ROOT/'game/state.json'
    try:raw=json.loads(path.read_text());best=basic(raw)
    except (OSError,ValueError,KeyError,TypeError):
        print(json.dumps({'refresh_required':True,'reason':'invalid_current_observation'}));return
    if raw['phase']=='game_over':print(json.dumps({'game_over':True}));return
    info={'fallback':True,'reason':'prepared_fallback','nodes':0};error=None;cache_hit=False
    try:cfg=json.loads((ROOT/'config.json').read_text())
    except (OSError,ValueError):cfg={}
    state=raw
    deadline=START+min(1.8,max(.05,cfg.get('total_budget_s',2)-.2))
    # History is public and scoped by the host to this game. It is never persisted across games.
    history=path.parent/'history.jsonl'
    if history.exists() and raw['phase']=='main':
        from state_features import with_public_history
        try:
            # Incomplete history is optional evidence, never a reason to emit a stale action.
            events=[]
            if history.stat().st_size<=4_000_000:
                with history.open() as stream:
                    for line in stream:
                        if time.monotonic()>=START+.30:events=[];break
                        if line.strip():events.append(json.loads(line))
                state=with_public_history(raw,events)
            else:error='history_size_limit'
        except (OSError,ValueError,TypeError):error='history_parse_error'
    memory={}
    memory_path=scratch/'plan.json'
    if memory_path.exists():
        try:memory=json.loads(memory_path.read_text())
        except (OSError,ValueError):pass
    data={'state':state,'config':cfg,'memory':memory,'search_deadline':min(START+1.5,deadline-.1)}
    key=hashlib.sha256(json.dumps({'state':state,'config':cfg},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    cache=scratch/'cache.json'
    if cache.exists():
        try:
            old=json.loads(cache.read_text())
            if old['key']==key and legal(raw,old['action']):best=old['action'];info=old['info'];cache_hit=True
        except (OSError,ValueError,KeyError):pass
    if raw['phase']!='deck_submission' and not args.fallback and not cache_hit and time.monotonic()<deadline:
        atomic(snapshot,data);atomic(checkpoint,{'action':best,'info':info})
        process=None
        try:
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
            _,stderr=process.communicate(timeout=max(.001,deadline-time.monotonic()))
            if process.returncode:error='worker_exit_'+str(process.returncode)+': '+stderr[-300:]
        except subprocess.TimeoutExpired:
            error='worker_timeout';process.kill();process.communicate(timeout=.1)
        except (OSError,subprocess.SubprocessError) as exc:
            error=type(exc).__name__
            if process and process.poll() is None:process.kill();process.wait(timeout=.1)
        try:
            saved=json.loads(checkpoint.read_text())
            if legal(raw,saved['action']):
                best=saved['action'];info=saved['info'];atomic(memory_path,saved.get('memory',{}))
        except (OSError,ValueError,KeyError):pass
    try:latest=json.loads(path.read_text())
    except (OSError,ValueError):
        print(json.dumps({'refresh_required':True,'reason':'observation_changed_or_invalid'}));return
    if latest['seq']!=raw['seq'] or latest.get('game_id')!=raw.get('game_id'):
        print(json.dumps({'refresh_required':True}));return
    row={'game_id':raw.get('game_id'),'seq':raw['seq'],'phase':raw['phase'],'action':best,'info':info,
         'worker_error':error,'cache_hit':cache_hit,'elapsed_s':time.monotonic()-START,'fingerprint':key}
    with (scratch/'decisions.jsonl').open('a') as log:log.write(json.dumps(row)+'\n')
    if best is not None:atomic(cache,{'key':key,'action':best,'info':info})
    print(json.dumps({'seq':raw['seq'],'action':best},separators=(',',':')))
if __name__=='__main__':main()
