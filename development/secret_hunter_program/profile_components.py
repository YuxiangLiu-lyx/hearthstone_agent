"""Cold worker component profile on saved public observations."""
import json,subprocess,sys,tempfile,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines,quantiles
from development.secret_hunter_program.accounting import record_cases

CODE='''import time
start=time.monotonic()
import json,sys
from pathlib import Path
stdlib=time.monotonic()
state=json.loads(Path(sys.argv[1]).read_text());cfg=json.loads(Path(sys.argv[2]).read_text())
parsed=time.monotonic()
sys.path.insert(0,sys.argv[3])
from program_policy import decide
loaded=time.monotonic()
a,info=decide(state,cfg)
decided=time.monotonic()
output=json.dumps({'seq':state['seq'],'action':a})
serialized=time.monotonic()
print(json.dumps({'stdlib_s':stdlib-start,'parse_s':parsed-stdlib,'policy_import_s':loaded-parsed,'decision_s':decided-loaded,'serialize_s':serialized-decided,'inside_s':serialized-start,'nodes':info.get('nodes',0)}))
'''

def main():
    src=ROOT/'development/secret_hunter_program/release/secret-hunter-program';folder=ROOT/'experiments/program-p0-development';states=[]
    for r in readlines(folder/'results.jsonl')[:8]:states.extend(z['state'] for z in readlines(folder/'games'/r['game']/f'p{r["seat"]}/observations.jsonl') if z['state']['phase']=='main')
    states.sort(key=lambda s:len(s['you']['hand'])+len(s['you']['board'])*len(s['opponent']['board']),reverse=True)
    rows=[]
    with tempfile.TemporaryDirectory() as t:
        path=Path(t)/'public.json'
        for s in states[:30]:
            path.write_text(json.dumps(s));start=time.monotonic();p=subprocess.run([sys.executable,'-c',CODE,str(path),str(src/'config.json'),str(src/'scripts')],capture_output=True,text=True,check=True,timeout=2)
            elapsed=time.monotonic()-start;r=json.loads(p.stdout);r['process_end_to_end_s']=elapsed;r['startup_and_exit_s']=elapsed-r['inside_s'];rows.append(r)
    report={'n':len(rows),'components':{k:quantiles([r[k] for r in rows]) for k in rows[0]},'details':rows,'scope':'Fresh Python worker process components, including imports. Full supervised CLI timings are measured separately; this does not include the parent process or host relay.'}
    record_cases('cold-worker-component-profiles',len(rows));write(ROOT/'docs/secret_hunter_program/component-profile.json',report);print(json.dumps({'n':len(rows),'p95':{k:v['p95'] for k,v in report['components'].items()}}))
if __name__=='__main__':main()
