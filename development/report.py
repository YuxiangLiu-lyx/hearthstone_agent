"""Generate auditable summaries from on-disk real results; never fills pending outcomes."""
import json
import statistics
from pathlib import Path
from development.benchmarks.run import quantile

ROOT=Path(__file__).resolve().parents[1]

def main():
    exp=ROOT/'development/experiments';report=ROOT/'development/reports'
    summaries={str(p.parent.relative_to(exp)):json.loads(p.read_text()) for p in sorted(exp.rglob('summary.json'))}
    integrations={}
    for folder in sorted(exp.glob('integration-*')):
        games=[];latencies=[];usage=[]
        for p in sorted(folder.glob('*/game.json')):
            game=p.parent;result_path=game/'result.json'
            if not result_path.exists():
                games.append({'game':game.name,'status':'pending'});continue
            r=json.loads(result_path.read_text());games.append(r)
            for seat in (1,2):
                calls=game/f'p{seat}/seat/mcp_calls.jsonl'
                seat_json=game/f'p{seat}/seat/seat.json'
                if seat_json.exists():usage.append(json.loads(seat_json.read_text()).get('usage',{}))
                if not calls.exists():continue
                for line in calls.read_text().splitlines():
                    c=json.loads(line)
                    if c.get('tool')!='act':continue
                    seq=c.get('arguments',{}).get('seq')
                    sp=game/f'p{seat}/decisions/{seq:05d}.state.json'
                    if not sp.exists():continue
                    s=json.loads(sp.read_text());latencies.append(c['time']-(s['deadline_epoch_s']-s['timeout_s']))
        completed=[g for g in games if g.get('status')!='pending']
        integrations[folder.name]={'games':games,'completed':len(completed),
            'forfeits':sum(g['reason'].startswith('forfeit') for g in completed),
            'illegal':sum(sum(g['illegal_counts'].values()) for g in completed),
            'timeouts':sum(sum(g['timeouts'].values()) for g in completed),
            'decision_latency_mean_s':statistics.mean(latencies) if latencies else None,
            'decision_latency_p95_s':quantile(latencies,.95),'decision_latency_max_s':max(latencies,default=None),
            'token_usage':{key:sum(u.get(key,0) for u in usage) for key in ('input_tokens','cached_input_tokens','output_tokens')}}
    output={'benchmark_runs':summaries,'total_python_games':sum(s['attempted'] for s in summaries.values()),
            'python_illegal':sum(s['illegal'] for s in summaries.values()),
            'python_timeouts':sum(s['timeouts'] for s in summaries.values()),
            'python_early_exits':sum(s['early_exits'] for s in summaries.values()),
            'python_void_or_errors':sum(s['void_or_errors'] for s in summaries.values()),
            'integration':integrations,
            'warning':'Do not pool different experiments into a generalization win rate. Training and holdout are reported separately.'}
    (report/'benchmark_summary.json').write_text(json.dumps(output,indent=2))
    model={'recommended_local_model':'luna','haiku_status':'claude executable absent from PATH; not tested',
           'course_submission':'not submitted','integration':integrations,
           'note':'Python timings exclude process/model overhead. MCP latencies use action-call timestamps minus published decision start.'}
    (report/'model_integration.json').write_text(json.dumps(model,indent=2))
    print(json.dumps({k:v for k,v in output.items() if k not in ('benchmark_runs','integration')},indent=2))
    print('integration status',{k:(v['completed'],v['forfeits']) for k,v in integrations.items()})

if __name__=='__main__':main()
