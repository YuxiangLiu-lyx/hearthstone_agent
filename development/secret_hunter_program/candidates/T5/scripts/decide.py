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
    def publish(action,info):atomic(checkpoint,{'action':action,'info':info})
    action,info=decide(state,cfg,publish)
    publish(action,info)


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--fallback',action='store_true');args=p.parse_args()
    scratch=ROOT/'scratch';scratch.mkdir(exist_ok=True)
    snapshot=scratch/'input.json';checkpoint=scratch/'best.json'
    if args.worker:worker(snapshot,checkpoint);return
    path=ROOT/'game/state.json';raw=json.loads(path.read_text());best=basic(raw)
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
        state=with_public_history(raw,[json.loads(line) for line in history.read_text().splitlines() if line])
    data={'state':state,'config':cfg}
    key=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
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
            if legal(raw,saved['action']):best=saved['action'];info=saved['info']
        except (OSError,ValueError,KeyError):pass
    latest=json.loads(path.read_text())
    if latest['seq']!=raw['seq'] or latest.get('game_id')!=raw.get('game_id'):
        print(json.dumps({'refresh_required':True}));return
    row={'game_id':raw.get('game_id'),'seq':raw['seq'],'phase':raw['phase'],'action':best,'info':info,
         'worker_error':error,'cache_hit':cache_hit,'elapsed_s':time.monotonic()-START,'fingerprint':key}
    with (scratch/'decisions.jsonl').open('a') as log:log.write(json.dumps(row)+'\n')
    if best is not None:atomic(cache,{'key':key,'action':best,'info':info})
    print(json.dumps({'seq':raw['seq'],'action':best},separators=(',',':')))
if __name__=='__main__':main()
