"""New, isolated teacher-informed experiments. No model/API calls or old budget mutation."""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import statistics
import traceback

from development.benchmarks.run import fingerprint, wilson
from development.secret_hunter_program.common import ROOT, sha, write, quantiles
from development.secret_hunter_tactics.run import worker as play


def worker(task):
    candidate, spec, seed, seat, out, mode = task
    try:
        row = play(task)
        path = Path(out)/'games'/row['game']/f'p{seat}'/'observations.jsonl'
        observations = [json.loads(line) for line in path.read_text().splitlines()]
        infos = [r.get('info',{}) for r in observations]
        row['policy_errors'] = [i['error'] for i in infos if i.get('error')]
        row['fallbacks'] = sum(bool(i.get('fallback')) for i in infos)
        row['over_2s'] = sum(r['elapsed_s']>2 for r in observations)
        row['decision_times'] = [r['elapsed_s'] for r in observations]
        row['group'] = spec.get('group',spec['name'])
        row['public_only'] = all(not any(k in r['state'] for k in ('seed','rng','opponent_id','opponent_name','engine'))
                                 and not any(k in (r['state'].get('opponent') or {}) for k in ('hand','deck'))
                                 for r in observations)
        return row
    except Exception:
        return {'opponent':spec['name'],'group':spec.get('group',spec['name']),'seed':seed,'seat':seat,
                'score':0,'harness_error':traceback.format_exc()}


def aggregate(rows):
    good=[r for r in rows if 'harness_error' not in r]
    wins=sum(r['score'] for r in good)
    draws=sum(r['result'].get('winner') is None for r in good)
    return {'n':len(rows),'wins':wins,'losses':len(good)-wins-draws,'draws_or_voids':draws,
            'win_rate':wins/len(rows) if rows else None,'wilson95_descriptive':wilson(wins,len(rows)),
            'harness_errors':len(rows)-len(good),
            'illegal':sum(r['result']['illegal_counts'].get(str(r['seat']),0) for r in good),
            'timeouts':sum(r['result']['timeouts'].get(str(r['seat']),0) for r in good),
            'forfeits':sum(r['result']['reason'].startswith('forfeit') for r in good),
            'opponent_errors':sum(len(r.get('opponent_errors',[])) for r in good),
            'policy_errors':sum(len(r['policy_errors']) for r in good),
            'fallbacks':sum(r['fallbacks'] for r in good),'over_2s':sum(r['over_2s'] for r in good),
            'public_input_violations':sum(not r['public_only'] for r in good)}


def summarize(rows):
    groups=defaultdict(list);opponents=defaultdict(list)
    for r in rows:
        groups[r['group']].append(r);opponents[r['opponent']].append(r)
    result={'all':aggregate(rows),'by_group':{k:aggregate(v) for k,v in groups.items()},
            'by_opponent':{k:aggregate(v) for k,v in opponents.items()},
            'latency_s':quantiles([t for r in rows for t in r.get('decision_times',[])])}
    # Equal weight per teacher family avoids over-weighting Astra merely by adding proxies.
    result['teacher_family_macro']=statistics.mean(v['win_rate'] for v in result['by_group'].values())
    result['by_actual_first']={str(first):aggregate([r for r in rows if 'result' in r and (r['first_player']==r['seat'])==first]) for first in (True,False)}
    return result


def snapshot(population):
    return {o['name']:{'deck':sha(ROOT/o['deck']),
                       'policy':fingerprint(ROOT/o['policy']) if o.get('policy') else None}
            for o in population}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate',required=True)
    parser.add_argument('--population',default='development/teacher_eval/core.json')
    parser.add_argument('--out',required=True)
    parser.add_argument('--start',type=int,required=True)
    parser.add_argument('--seeds',type=int,required=True)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--split',choices=['development','confirmation','guardrail'],required=True)
    args=parser.parse_args()
    assert args.seeds>0 and args.workers>0
    assert (args.start>=100000)==(args.split!='development')
    pop=json.loads((ROOT/args.population).read_text())
    assert len({o['name'] for o in pop})==len(pop)
    output=ROOT/args.out
    output.mkdir(parents=True,exist_ok=False)
    deps={p:sha(ROOT/p) for p in ('development/teacher_eval/run.py','development/secret_hunter_tactics/run.py',
          'development/opponents/population.py','development/opponents/search.py','development/benchmarks/run.py')}
    manifest={**vars(args),'candidate_sha256':fingerprint(ROOT/args.candidate),
              'population_sha256':sha(ROOT/args.population),'population':pop,'opponent_versions':snapshot(pop),
              'code_sha256':deps,'planned_games':len(pop)*args.seeds*2,
              'scope':'Local proxies derived from teacher evidence, NOT real Astra or official resubmission.'}
    write(output/'config.json',manifest)
    tasks=[(str(ROOT/args.candidate),o,seed,seat,str(output),'python')
           for o in pop for seed in range(args.start,args.start+args.seeds) for seat in (1,2)]
    rows=[]
    # One candidate per invocation/process pool: same-named candidate modules never cross arms.
    with ProcessPoolExecutor(max_workers=args.workers) as pool,(output/'results.jsonl').open('w') as log:
        futures=[pool.submit(worker,t) for t in tasks]
        for future in as_completed(futures):
            row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            if len(rows)%24==0 or len(rows)==len(tasks):
                print(f"{len(rows)}/{len(tasks)} wins={sum(r['score'] for r in rows)}",flush=True)
    assert fingerprint(ROOT/args.candidate)==manifest['candidate_sha256']
    assert snapshot(pop)==manifest['opponent_versions']
    assert all(sha(ROOT/p)==v for p,v in deps.items())
    report=summarize(rows)
    write(output/'summary.json',report)
    print(json.dumps(report,indent=2))
    assert not any(report['all'][k] for k in ('harness_errors','illegal','timeouts','forfeits','opponent_errors',
                    'policy_errors','fallbacks','over_2s','public_input_violations')), 'Inspect reliability failures'


if __name__=='__main__':
    main()
