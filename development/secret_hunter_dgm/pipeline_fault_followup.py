"""Preserve the prior failure; record subprocess lifecycle before safe test cleanup."""
import json,os,signal,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
from development.secret_hunter_dgm.accounting import reserve,finish
C=ROOT/'development/secret_hunter_dgm/release/secret-hunter-program';D=ROOT/'docs/secret_hunter_dgm'
reserve('pipeline-fault-followup',short=120,final=True)
rows=readlines(ROOT/'experiments/secret-hunter-dgm-y1-retain/results.jsonl');r=rows[0]
zs=readlines(ROOT/'experiments/secret-hunter-dgm-y1-retain/games'/r['game']/f'p{r["seat"]}'/'observations.jsonl');state=next(z['state'] for z in zs if z['state']['phase']=='main')
records=[]
with tempfile.TemporaryDirectory() as t:
 p=Path(t)/'skill';shutil.copytree(C,p,ignore=shutil.ignore_patterns('__pycache__','game','scratch'));(p/'game').mkdir()
 (p/'scripts/program_policy.py').write_text('import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n')
 for i in range(8):
  s=state|{'game_id':'fault-followup-'+str(i)};(p/'game/state.json').write_text(json.dumps(s));start=time.monotonic()
  proc=subprocess.Popen([sys.executable,'scripts/decide.py'],cwd=p,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  time.sleep(.15);(p/'game/state.json').write_text(json.dumps(s|{'seq':s['seq']+1}));timeout=False;out='';err=''
  try:out,err=proc.communicate(timeout=3)
  except subprocess.TimeoutExpired:
   timeout=True;os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate(timeout=2)
  elapsed=time.monotonic()-start
  try:result=json.loads(out)
  except ValueError:result={}
  records.append({'elapsed_s':elapsed,'outer_timeout':timeout,'returncode':proc.returncode,'refresh_required':result.get('refresh_required',False),'stale_action':result.get('action') is not None,'stderr':err[-500:]})
  write(D/'pipeline-fault-followup.json',{'earlier_failure_retained':True,'cases':records,'observed_over_2s':sum(x['elapsed_s']>2 for x in records),'cold_start_included':True})
finish('pipeline-fault-followup',actual_short=len(records));print(json.dumps({'latency':quantiles([r['elapsed_s'] for r in records]),'correct_refresh':sum(r['refresh_required'] for r in records),'n':len(records),'earlier_failure':'Not erased; resource/scheduling cause unproven without instrumentation of original child.'}))
