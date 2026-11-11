"""Compare every actual MCP act with the Python log for the same sequence."""
import argparse,json
from collections import Counter
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines,quantiles


def audit(game,seat):
    folder=game/f'p{seat}';logs=readlines(folder/'seat/scratch/decisions.jsonl');calls=readlines(folder/'seat/mcp_calls.jsonl')
    byseq={r['seq']:r for r in logs};details=[]
    for c in calls:
        if c.get('tool')!='act':continue
        n=c['arguments']['seq'];action=c['arguments']['action'];record=byseq.get(n)
        p=folder/'decisions'/f'{n:05d}.state.json';state=json.loads(p.read_text()) if p.exists() else {}
        elapsed=c['time']-(state['deadline_epoch_s']-state['timeout_s']) if 'deadline_epoch_s' in state else None
        details.append({'seq':n,'phase':state.get('phase'),'actual':action,'script':record.get('action') if record else None,'exact':bool(record and record['action']==action),'publication_to_act_s':elapsed})
    meta=json.loads((folder/'seat/seat.json').read_text()) if (folder/'seat/seat.json').exists() else {}
    result=json.loads((game/'result.json').read_text())
    return {'game':str(game.relative_to(ROOT)),'result':result,'model':meta.get('model_id'),'effort':meta.get('effort'),'usage':meta.get('usage'),
        'decisions':len(details),'relay_deviations':sum(not d['exact'] for d in details),'worker_errors':dict(Counter(r['worker_error'] for r in logs if r.get('worker_error'))),
        'fallbacks':sum(r['info'].get('fallback',False) for r in logs if r['phase']!='deck_submission'),
        'program_latency_s':quantiles([r['elapsed_s'] for r in logs]),'publication_to_act_s':quantiles([d['publication_to_act_s'] for d in details if d['publication_to_act_s'] is not None]),'details':details}


def main():
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--out',required=True);a=p.parse_args();folder=ROOT/a.folder
    rows=readlines(folder/'results.jsonl')
    games=[(folder/'games'/r['game'],r['seat']) for r in rows] if rows else [(g,1) for g in (folder/'games').glob('*') if (g/'result.json').exists()]
    reports=[audit(g,seat) for g,seat in games]
    report={'games':len(reports),'decisions':sum(r['decisions'] for r in reports),'relay_deviations':sum(r['relay_deviations'] for r in reports),'reports':reports}
    write(ROOT/a.out,report);print(json.dumps({k:v for k,v in report.items() if k!='reports'}))
if __name__=='__main__':main()
