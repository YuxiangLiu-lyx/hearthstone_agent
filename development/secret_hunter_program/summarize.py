"""Archive actual outcomes, latency, hashes and budget usage without rerunning matches."""
from collections import Counter
from datetime import datetime,timezone
import fcntl,json
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha,write
from development.secret_hunter_program.common import readlines,quantiles
from development.benchmarks.run import fingerprint


def measurements(folder,rows):
    times=[];nodes=[];search_times=[];reasons=Counter();errors=Counter();fallback=0;over=0;unsupported=0;bounded=0;nmain=0
    for r in rows:
        for line in (folder/'games'/r['game']/f'p{r["seat"]}/observations.jsonl').read_text().splitlines():
            z=json.loads(line);info=z['info'];times.append(z['elapsed_s']);nodes.append(info.get('nodes',0));reasons[info.get('reason','unknown')]+=1
            if info.get('error'):errors[info['error']]+=1
            fallback+=bool(info.get('fallback'));over+=z['elapsed_s']>2
            if z['state']['phase']=='main':
                nmain+=1;unsupported+=not info.get('lethal',{}).get('supported',False)
                turn=info.get('turn_search',{});bounded+=turn.get('bounded_out',False)
                if 'elapsed_s' in turn:search_times.append(turn['elapsed_s'])
    return {'latency_s':quantiles(times),'nodes':quantiles(nodes),'turn_search_latency_s':quantiles(search_times),'reasons':dict(reasons),'policy_errors':dict(errors),'fallbacks':fallback,'over_2s':over,'main_decisions':nmain,'lethal_coverage_rejected':unsupported,'turn_search_bounded':bounded}


def reproduction(original='experiments/program-f1-confirmation',repeated='experiments/program-zip-reproduction',output='docs/secret_hunter_program/reproduction.json'):
    a=ROOT/original;b=ROOT/repeated
    key=lambda r:(r['opponent'],r['seed'],r['seat'])
    aa={key(r):r for r in readlines(a/'results.jsonl')};bb={key(r):r for r in readlines(b/'results.jsonl')};details=[]
    for k,r in bb.items():
        original=aa[k]
        def actions(folder,row):return [x['action'] for x in readlines(folder/'games'/row['game']/f'p{row["seat"]}/observations.jsonl')]
        x,y=actions(a,original),actions(b,r)
        details.append({'opponent':k[0],'seed':k[1],'seat':k[2],'same_outcome':original['score']==r['score'],'identical_actions':x==y,'actions_original':len(x),'actions_reproduced':len(y)})
    result={'games':len(details),'same_outcomes':sum(r['same_outcome'] for r in details),'identical_action_traces':sum(r['identical_actions'] for r in details),'details':details,'scope':'Previously observed seeds; reproducibility check, excluded from final win-rate inference.'}
    write(ROOT/output,result);return result


def main():
    p=ROOT/'docs/secret_hunter_program/budget.json';ledger=json.loads(p.read_text());reports={}
    for r in ledger['runs']:
        folder=ROOT/r['out'];config=json.loads((folder/'config.json').read_text());rows=readlines(folder/'results.jsonl')
        if r['mode']=='python':
            assert len(rows)==r['reserved'],r['out'];assert fingerprint(ROOT/config['candidate'])==config['candidate_sha256']
            report=measurements(folder,rows);summary=json.loads((folder/'summary.json').read_text())
            report.update(summary=summary,candidate=config['candidate'],candidate_sha256=config['candidate_sha256'],config_sha256=sha(ROOT/config['candidate']/'config.json'),deck_sha256=config['deck_sha256'],opponent_sha256=config['manifest_sha256'],hypothesis=config['hypothesis'])
            reports[r['out']]=report;r.update(completed=len(rows),status='completed')
        elif r['mode']=='client':
            results=[json.loads(g.read_text()) for g in (folder/'games').glob('*/result.json')];r.update(completed=len(results),status='completed' if len(results)==r['reserved'] else 'running')
        else:r.update(completed=len(rows),status='completed' if len(rows)==r['reserved'] else 'running')
    ledger['full_games_completed']=sum(r['completed'] for r in ledger['runs']);ledger['full_games_reserved']=sum(r['reserved'] for r in ledger['runs']);ledger['short_continuations_used']=sum(r['count'] for r in ledger['short_continuations'])
    ledger['updated_utc']=datetime.now(timezone.utc).isoformat();ledger['elapsed_wall_seconds']=(datetime.now(timezone.utc)-datetime.fromisoformat(ledger['started_utc'])).total_seconds()
    # A locked read/merge preserves any separately recorded short cases during archival.
    with (p.parent/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);live=json.loads(p.read_text());ledger['short_continuations']=live['short_continuations'];ledger['short_continuations_used']=sum(r['count'] for r in live['short_continuations']);write(p,ledger)
    write(ROOT/'docs/secret_hunter_program/experiments.json',reports)
    rep=reproduction();
    if (ROOT/'experiments/program-f2-zip-reproduction/summary.json').exists():reproduction('experiments/program-f2-confirmation','experiments/program-f2-zip-reproduction','docs/secret_hunter_program/f2-reproduction.json')
    print(json.dumps({'full_completed':ledger['full_games_completed'],'full_reserved':ledger['full_games_reserved'],'short_cases':ledger['short_continuations_used'],'reproduction_outcomes':rep['same_outcomes'],'reproduction_actions':rep['identical_action_traces'],'runs':len(reports)}))
    for name in ['experiments/program-b1-confirmation','experiments/program-f1-confirmation']:print(name,json.dumps({k:v for k,v in reports[name].items() if k in ('latency_s','nodes','policy_errors','fallbacks','over_2s','lethal_coverage_rejected','main_decisions')}))
if __name__=='__main__':main()
