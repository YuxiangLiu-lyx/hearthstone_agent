"""Resumable bounded paired continuation jobs, with failures kept separate."""
import argparse
import json
from pathlib import Path
import sys
import time
import signal
from development.secret_hunter_mcgs.supervision import GameProcess
from development.secret_hunter_mcgs.train import atomic
from development.secret_hunter_turn_plans.study import RUN,ROOT


def main():
    p=argparse.ArgumentParser();p.add_argument('--samples',type=int,default=4);p.add_argument('--workers',type=int,default=3)
    p.add_argument('--max-cases',type=int,default=0);p.add_argument('--output',default='continuations-v3')
    p.add_argument('--candidate',default='R4-canonical-cache');p.add_argument('--sources',default='mined')
    p.add_argument('--only-scenario',choices=['natural','no_coil','forced_coil']);p.add_argument('--strict-coil',action='store_true')
    p.add_argument('--force-next-draw',action='store_true')
    p.add_argument('--routes',nargs='+',help='Explicit diagnostic routes; never modifies candidate snapshots')
    args=p.parse_args()
    sources=sorted((RUN/args.sources).glob('*.json'));sources=[p for p in sources if p.name!='manifest.json']
    if args.max_cases:sources=sources[:args.max_cases]
    out=RUN/args.output;out.mkdir(exist_ok=True);jobs=[]
    routes={'trap':['replan','committed','preserve','keeper'],
            'knife_wolf':['replan','kill_juggler','kill_wolf','face'],
            'amani':['replan','highmane','trade_amani','taunt','bow_amani']}
    if args.routes:routes={k:args.routes for k in routes}
    for src in sources:
        c=json.loads(src.read_text())
        for sample in range(args.samples):
            for scenario in (['no_coil','natural','forced_coil'] if c['kind']=='amani' else ['natural']):
                if args.only_scenario and scenario!=args.only_scenario:continue
                for route in routes[c['kind']]:
                    name=f'{c["case"]}-{scenario}-{sample}-{route}'
                    result=out/(name+'.json')
                    if result.exists():continue
                    job={'source':str(src),'candidate':args.candidate,'strict_coil':args.strict_coil,'force_next_draw':args.force_next_draw,'route':route,'scenario':scenario,'sample':sample+(100 if c['split']=='validation' else 0),
                         'result':str(result),'trace':sample==0}
                    request=out/(name+'.request.json');atomic(request,job);jobs.append((request,result))
    atomic(out/'schedule.json',{'jobs_pending':len(jobs),'source_cases':len(sources),'sources':args.sources,'candidate':args.candidate,'samples':args.samples,'routes':routes})
    active={};index=0;completed=0;start=time.monotonic()
    stop=[]
    signal.signal(signal.SIGTERM,lambda *_:stop.append(True))
    signal.signal(signal.SIGINT,lambda *_:stop.append(True))
    try:
        while active or index<len(jobs):
            if stop or time.time()>json.loads((RUN/'manifest.json').read_text())['deadline']:break
            while index<len(jobs) and len(active)<args.workers:
                request,result=jobs[index];index+=1
                process=GameProcess([sys.executable,'-m','development.secret_hunter_turn_plans.rollout',str(request)],ROOT,result.with_suffix('.log'))
                active[index]=(process,result)
            time.sleep(.15)
            for ident,(process,result) in list(active.items()):
                if process.process.poll() is None and time.monotonic()-process.started<90:continue
                process.close();del active[ident];completed+=1
                if not result.exists():atomic(result,{'execution_error':'timeout_or_crash','score':None})
                if completed%12==0:print(json.dumps({'completed':completed,'scheduled':len(jobs),'elapsed_s':time.monotonic()-start}),flush=True)
    finally:
        for process,_ in active.values():process.close()
    print(json.dumps({'finished':completed,'scheduled':len(jobs),'elapsed_s':time.monotonic()-start}),flush=True)


if __name__=='__main__':main()
