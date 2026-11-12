"""Full CLI cold starts, concurrent processes, failures and stale observation tests."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from development.secret_hunter_mcgs.build import ROOT,HERE,Y1
from development.secret_hunter_program.common import quantiles


def probe(candidate,state,tag='cold',injection=None,stale=False):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/'skill';shutil.copytree(candidate,root,ignore=shutil.ignore_patterns('__pycache__','game','scratch'))
        (root/'game').mkdir();path=root/'game/state.json'
        state={**state,'game_id':tag+'-'+str(time.monotonic_ns())};path.write_text(json.dumps(state))
        if injection:(root/'scripts/program_policy.py').write_text(injection)
        start=time.monotonic();proc=subprocess.Popen([sys.executable,'scripts/decide.py'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if stale:
            while not (root/'scratch/input.json').exists() and proc.poll() is None and time.monotonic()-start<1:
                time.sleep(.002)
            path.write_text(json.dumps({**state,'seq':state['seq']+1}))
        out,err=proc.communicate(timeout=3);elapsed=time.monotonic()-start
        assert proc.returncode==0,(out,err)
        answer=json.loads(out)
        logs=root/'scratch/decisions.jsonl'
        row=json.loads(logs.read_text().splitlines()[-1]) if logs.exists() else {}
        if stale:valid=bool(answer.get('refresh_required')) and not answer.get('action')
        elif state['phase']=='game_over':valid=answer.get('game_over')
        else:
            sys.path.insert(0,str(candidate/'scripts'))
            from action_validator import legal
            valid=legal(state,answer.get('action'))
        return {'candidate':candidate.name,'tag':tag,'elapsed_s':elapsed,'valid':bool(valid),
                'worker_error':row.get('worker_error'),'fallback':row.get('info',{}).get('fallback'),
                'mcgs':row.get('info',{}).get('mcgs'), 'action':answer.get('action'),
                'refresh_required':answer.get('refresh_required',False)}


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--candidate');parser.add_argument('--out',default='docs/secret_hunter_mcgs/runtime.json');args=parser.parse_args()
    rows=[json.loads(l) for l in (ROOT/'runs/krush-mcgs/submission2/decisions.jsonl').read_text().splitlines()]
    states=[r['state'] for r in rows if r['state']['phase']=='main' and 2<=r['state']['you']['max_mana']<=6 and r['state']['opponent']['board']]
    states.sort(key=lambda s:len(s['you']['board'])*len(s['opponent']['board'])+len(s['you']['hand']),reverse=True)
    original=[]
    for path in (ROOT/'runs/krush-mcgs/batches/pilot-102/M5-dpw/games').glob('*/p*/observations.jsonl'):
        original.extend(r['state'] for line in path.read_text().splitlines() if (r:=json.loads(line))['state']['phase']=='main' and 2<=r['state']['you']['max_mana']<=6 and r['state']['opponent']['board'])
    original.sort(key=lambda s:len(s['you']['board'])*len(s['opponent']['board'])+len(s['you']['hand']),reverse=True)
    selected=states[:6]+(original[:6] if original else states[::max(1,len(states)//6)][:6])
    records=[]
    for name in ([Path(args.candidate).name] if args.candidate else ('Y1','M3-uct','M3-fixed','M3-dpw','M4-particles')):
        c=ROOT/args.candidate if args.candidate else Y1 if name=='Y1' else HERE/'candidates'/name
        for s in selected:records.append(probe(c,s))
        print(json.dumps({'candidate':name,'cold':quantiles([r['elapsed_s'] for r in records if r['candidate']==name])}),flush=True)
    candidate=ROOT/args.candidate if args.candidate else HERE/'candidates/M4-particles';s=selected[0]
    with ThreadPoolExecutor(max_workers=4) as pool:
        records+=list(pool.map(lambda n:probe(candidate,selected[n],'concurrent'),range(4)))
    hang='import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n'
    crash='def decide(*args,**kwargs):\n raise RuntimeError("injected crash")\n'
    published='import time\nfrom secret_policy import rank\ndef decide(state,config,publish=None,**kwargs):\n a=rank(state,config)[0][1]\n publish(a,{"fallback":False,"reason":"published_before_hang"})\n time.sleep(20)\n'
    for tag,body in [('hang',hang),('crash',crash),('published_hang',published)]:records.append(probe(candidate,s,tag,body))
    for c in (Y1,candidate):
        for i in range(4):records.append(probe(c,s,'stale-'+str(i),hang,stale=True))
    records.append(probe(candidate,{'phase':'game_over','seq':999},'game_over'))
    summary={'n':len(records),'invalid':sum(not r['valid'] for r in records),'over_2s':sum(r['elapsed_s']>2 for r in records),
             'all_latency_s':quantiles([r['elapsed_s'] for r in records]),
             'by_candidate':{name:quantiles([r['elapsed_s'] for r in records if r['candidate']==name and r['tag']=='cold']) for name in {r['candidate'] for r in records}},
             'ordinary_fallbacks':sum(bool(r['fallback']) for r in records if r['tag'] in ('cold','concurrent')),
             'records':records,'scope':'Cold CLI ablations share the 2s envelope; direct-call full games are separately reported.'}
    (ROOT/args.out).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='records'}))
    assert summary['invalid']==0
if __name__=='__main__':main()
