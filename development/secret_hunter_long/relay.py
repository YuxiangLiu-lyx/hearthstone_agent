"""Official course SkillSeat/ClientSeat; exact seq/action and timing audit."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from development.secret_hunter_long.study import ROOT,RUN
from development.secret_hunter_mcgs import train
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha,quantiles

def audit(folder,seat,mode):
    result_path=next(folder.glob('g_*/result.json'));game=result_path.parent;p=game/f'p{seat}'
    result=json.loads(result_path.read_text());calls=[json.loads(l) for l in (p/'seat/mcp_calls.jsonl').read_text().splitlines()] if (p/'seat/mcp_calls.jsonl').exists() else []
    decisions=[json.loads(l) for l in (p/'seat/scratch/decisions.jsonl').read_text().splitlines()] if (p/'seat/scratch/decisions.jsonl').exists() else []
    outputs={d['seq']:{'seq':d['seq'],'action':d['action']} for d in decisions};acts=[c for c in calls if c['tool']=='act']
    mismatches=[c for c in acts if c['arguments']!=outputs.get(c['arguments'].get('seq'))]
    states=[json.loads(f.read_text()) for f in (p/'decisions').glob('*.state.json')]
    normal={d['seq']:d for d in decisions if d['phase']!='deck_submission'};times=[];outside=[]
    for c in acts:
        seq=c['arguments']['seq']
        if seq in normal:
            elapsed=c['time']-(p/f'decisions/{seq:05d}.state.json').stat().st_mtime
            times.append(elapsed);outside.append(elapsed-normal[seq]['elapsed_s'])
    seatmeta=json.loads((p/'seat/seat.json').read_text()) if (p/'seat/seat.json').exists() else {}
    chain={'script_before_every_act':None,'actions_without_matching_script':None,'terminal_tool_reply_seen':False}
    if mode=='luna':
        ready=None;bad=[];model_acts=0
        for transcript in sorted((p/'seat').glob('session_*.jsonl')):
            for line in transcript.read_text().splitlines():
                event=json.loads(line)
                if event.get('type')!='item.completed':continue
                item=event.get('item',{})
                if item.get('type')=='command_execution' and any(x in item.get('command','') for x in ('scripts/decide.py','scripts/fallback.py')):
                    try:ready=json.loads(item.get('aggregated_output',''))
                    except ValueError:ready=None
                if item.get('type')=='mcp_tool_call':
                    reply=json.dumps(item.get('result',{}))
                    if 'GAME OVER' in reply:chain['terminal_tool_reply_seen']=True
                    if item.get('tool')=='act':
                        model_acts+=1
                        if item.get('arguments')!=ready:bad.append(item.get('arguments'))
                        ready=None
        chain.update(script_before_every_act=bool(model_acts and not bad),actions_without_matching_script=len(bad),model_act_calls=model_acts)
    else:
        chain['terminal_tool_reply_seen']=any('GAME OVER' in f.read_text(errors='replace') for f in (p/'seat').glob('*.err'))
    return {'mode':mode,'game_path':str(game),'seat':seat,'result':result,'decisions':len(decisions),'act_calls':len(acts),
       'wait_first':bool(calls and calls[0]['tool']=='wait'),'envelope_mismatches':len(mismatches),
       'game_over_published':any(s['phase']=='game_over' for s in states),
       'game_over_observed':chain['terminal_tool_reply_seen'],'model_chain':chain,
       'ordinary_fallbacks':sum(bool(d['info'].get('fallback')) for d in normal.values()),
       'worker_errors':sum(bool(d.get('worker_error')) for d in normal.values()),
       'internal_program_latency_s':quantiles([d['elapsed_s'] for d in normal.values()]),
       'publication_to_act_latency_s':quantiles(times),'outside_internal_program_latency_s':quantiles(outside),
       'course_stop':seatmeta.get('course_stops'),'model_id':seatmeta.get('model_id'),
       'timing_scope':'same-host state publication to MCP act; residual includes model/shell/Python startup/transport; not pure network timing'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--mode',choices=['luna','client'],required=True)
    p.add_argument('--seed',type=int,required=True);p.add_argument('--seat',type=int,default=1);a=p.parse_args()
    source=Path(a.candidate).resolve();original=fingerprint(source);db=train.connect(RUN)
    db.execute('CREATE TABLE IF NOT EXISTS auxiliary_games (key TEXT PRIMARY KEY,status TEXT,started REAL,finished REAL,result TEXT)');db.commit()
    key=f'{a.mode}-{a.seed}-s{a.seat}';old=db.execute('select * from auxiliary_games where key=?',(key,)).fetchone()
    if old:
        assert old['status']=='done','inspect incomplete auxiliary attempt, do not silently retry';print(old['result']);return
    count=db.execute('select count(*) from attempts').fetchone()[0]+db.execute('select count(*) from auxiliary_games').fetchone()[0]
    assert count<train.meta(db,'manifest')['limits']['full_games'] and time.time()<train.meta(db,'manifest')['deadline']
    env=os.environ.copy();binary=None
    if a.mode=='luna':
        binary=Path('/Users/liuyuxiang/.vscode/extensions/openai.chatgpt-26.1007.21434-darwin-arm64/bin/macos-aarch64/codex')
        assert binary.exists();bindir=RUN/'relay-bin';bindir.mkdir(exist_ok=True)
        link=bindir/'codex'
        if not link.exists():link.symlink_to(binary)
        # The native CLI locates codex-code-mode-host beside argv[0]. Use its
        # real directory, not a symlink directory lacking companion binaries.
        env['PATH']=str(binary.parent)+os.pathsep+env.get('PATH','')
    player=('skill:' if a.mode=='luna' else 'client:')+str(source);out=RUN/'relay'/key;out.parent.mkdir(exist_ok=True)
    cmd=[sys.executable,'-c','from hs_arena.cli import main; main()','play','--p1',player if a.seat==1 else 'greedy',
      '--p2',player if a.seat==2 else 'greedy','--games','1','--parallel','1','--seed',str(a.seed),'--out',str(out),
      '--keep-decisions','--max-turns','180','--timeout','180']
    train.atomic(out.with_suffix('.request.json'),{'command':cmd,'candidate_sha256':original,'model':'gpt-6-luna' if a.mode=='luna' else None,
      'effort':'medium' if a.mode=='luna' else None,'binary':str(binary),'binary_sha256':sha(binary) if binary else None})
    with db:db.execute('insert into auxiliary_games values (?,?,?,?,?)',(key,'running',time.time(),None,None))
    start=time.monotonic()
    try:
        proc=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=1800)
        out.with_suffix('.log').write_text(proc.stdout+proc.stderr)
        result=audit(out,a.seat,a.mode);result['command_returncode']=proc.returncode;result['wall_s']=time.monotonic()-start
        result['source_sha256']=original
        assert fingerprint(source)==original
        with db:db.execute("update auxiliary_games set status='done',finished=?,result=? where key=?",(time.time(),json.dumps(result),key))
        train.atomic(out.with_suffix('.audit.json'),result);print(json.dumps(result,indent=2))
    except Exception as exc:
        with db:db.execute("update auxiliary_games set status='error',finished=?,result=? where key=?",(time.time(),json.dumps({'error':repr(exc)}),key))
        raise

if __name__=='__main__':main()
