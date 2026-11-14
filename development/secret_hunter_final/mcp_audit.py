"""Six resumable official no-model MCP games against the exact released ZIP."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from development.secret_hunter_final.study import ROOT,RUN
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import quantiles
from development.benchmarks.run import fingerprint


def audit(folder,seat):
    game=next(folder.glob('g_*/result.json')).parent
    result=json.loads((game/'result.json').read_text())
    p=game/f'p{seat}'
    calls=[json.loads(x) for x in (p/'seat/mcp_calls.jsonl').read_text().splitlines()]
    decisions=[json.loads(x) for x in (p/'seat/scratch/decisions.jsonl').read_text().splitlines()]
    outputs={d['seq']:{'seq':d['seq'],'action':d['action']} for d in decisions}
    acts=[c for c in calls if c['tool']=='act']
    assert len(acts)==len(outputs)
    assert calls[0]['tool']=='wait'
    for c in acts:
        envelope=c['arguments']
        assert envelope==outputs[envelope['seq']]
        assert json.loads((p/f'decisions/{envelope["seq"]:05d}.action.json').read_text())==envelope
    finals=[json.loads(f.read_text()) for f in (p/'decisions').glob('*.state.json')]
    assert any(s['phase']=='game_over' for s in finals)
    logs='\n'.join(f.read_text(errors='replace') for f in (p/'seat').glob('*.err'))
    assert 'GAME OVER' in logs
    assert not any(result['illegal_counts'].values()) and not any(result['timeouts'].values())
    assert 'forfeit' not in result['reason'] and not result.get('engine_error')
    normal=[d for d in decisions if d['phase']!='deck_submission']
    assert not any(d['worker_error'] or d['info'].get('fallback') for d in normal)
    return {'game_path':str(game.relative_to(ROOT)),'seat':seat,'result':result,
            'decisions':len(decisions),'all_seq_action_envelopes_identical':True,
            'wait_first':True,'game_over_observed':True,
            'ordinary_fallbacks':0,'worker_errors':0,
            'internal_program_times_s':[d['elapsed_s'] for d in normal],
            'timing_scope':'Internal decide.py elapsed excludes Python startup. Full subprocess latency is measured in final-core/final-guard; no per-action Luna relay measurement.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);a=p.parse_args()
    source=Path(a.candidate).resolve();original=fingerprint(source)
    db=train.connect(RUN)
    db.execute('CREATE TABLE IF NOT EXISTS auxiliary_games (key TEXT PRIMARY KEY, status TEXT, started REAL, finished REAL, result TEXT)')
    db.commit();records=[]
    for seed in range(41600000,41600003):
        for seat in (1,2):
            key=f'mcp-{seed}-s{seat}';out=RUN/'mcp'/key
            old=db.execute('select * from auxiliary_games where key=?',(key,)).fetchone()
            if old and old['status']=='done':records.append(json.loads(old['result']));continue
            # A partially launched official game is not silently retried.
            assert old is None, ('Inspect incomplete auxiliary attempt before retry',key)
            assert db.execute('select count(*) from attempts').fetchone()[0]+db.execute('select count(*) from auxiliary_games').fetchone()[0]<6000
            assert time.time()<train.meta(db,'manifest')['deadline']
            with db:db.execute('insert into auxiliary_games values (?,?,?,?,?)',(key,'running',time.time(),None,None))
            player='client:'+str(source)
            args=[sys.executable,'-c','from hs_arena.cli import main; main()','play',
                  '--p1',player if seat==1 else 'greedy','--p2',player if seat==2 else 'greedy',
                  '--games','1','--parallel','1','--seed',str(seed),'--out',str(out),
                  '--keep-decisions','--max-turns','180']
            out.parent.mkdir(parents=True,exist_ok=True)
            start=time.monotonic()
            try:
                proc=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=300)
                out.with_suffix('.log').write_text(proc.stdout+proc.stderr)
                assert proc.returncode==0,proc.stderr
                record=audit(out,seat);record['command_wall_s']=time.monotonic()-start
                record['source_sha256']=original
                with db:db.execute('update auxiliary_games set status="done",finished=?,result=? where key=?',(time.time(),json.dumps(record),key))
                records.append(record)
                print(json.dumps({'key':key,'winner':record['result']['winner'],'calls':record['decisions']}),flush=True)
            except Exception:
                with db:db.execute('update auxiliary_games set status="error",finished=? where key=?',(time.time(),key))
                raise
    assert fingerprint(source)==original
    summary={'games':len(records),'wins':sum(r['result']['winner']==r['seat'] for r in records),
             'actual_first_games':sum(r['result']['first_player']==r['seat'] for r in records),
             'decisions':sum(r['decisions'] for r in records),'envelope_mismatches':0,'illegal':0,'timeouts':0,'forfeits':0,
             'internal_program_latency_s':quantiles([t for r in records for t in r['internal_program_times_s']]),
             'scope':'Official wait → Python decide.py → act transport, no model. These six games are protocol checks, not the frozen proxy evaluation or Luna validation.',
             'records':records}
    train.atomic(ROOT/'docs/secret_hunter_final/mcp-audit.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='records'}))


if __name__=='__main__':main()
