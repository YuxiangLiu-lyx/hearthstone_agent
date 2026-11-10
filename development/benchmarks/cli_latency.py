"""Measure exact packaged CLI latency on recorded real observations, including interpreter startup."""
import argparse,json,random,statistics,subprocess,sys,tempfile,time
from pathlib import Path
from development.benchmarks.run import quantile

def main():
    p=argparse.ArgumentParser();p.add_argument('--skill',default='submission/hearthstone-agent')
    p.add_argument('--experiment',default='development/experiments/paladin-expanded');p.add_argument('--samples',type=int,default=100)
    p.add_argument('--out',default='development/reports/cli-latency.json');args=p.parse_args()
    games=[json.loads(l) for l in (Path(args.experiment)/'games.jsonl').read_text().splitlines()]
    rng=random.Random(382);rng.shuffle(games);states=[]
    for g in games[:20]:
        states.extend(json.loads(l)['state'] for l in Path(g['observations']).read_text().splitlines())
    states=rng.sample(states,min(args.samples,len(states)));times=[];errors=[]
    script=(Path(args.skill)/'scripts/decide.py').resolve()
    with tempfile.TemporaryDirectory() as tmp:
        state_path=Path(tmp)/'state.json'
        for s in states:
            state_path.write_text(json.dumps(s));t=time.perf_counter()
            r=subprocess.run([sys.executable,str(script),str(state_path)],capture_output=True,text=True,timeout=8)
            times.append(time.perf_counter()-t)
            if r.returncode or r.stderr:errors.append(r.stderr or str(r.returncode))
            assert json.loads(r.stdout)['seq']==s['seq']
    output={'samples':len(times),'mean_s':statistics.mean(times),'p95_s':quantile(times,.95),
            'p99_s':quantile(times,.99),'max_s':max(times),'errors':errors,'includes':'Python startup, policy worker, JSON and validation'}
    Path(args.out).write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))

if __name__=='__main__':main()
