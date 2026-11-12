"""Isolated stale-observation plus hung-worker checks with process-group cleanup."""
import argparse,json,os,signal,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write,quantiles
from development.secret_hunter_response.accounting import reserve,finish

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--name',required=True);a=p.parse_args()
 reserve(a.name,short=12,seconds=90);state=json.loads((ROOT/'docs/secret_hunter_response/turn-starts.json').read_text())[0]['observation'];records=[]
 with tempfile.TemporaryDirectory() as t:
  root=Path(t)/'skill';shutil.copytree(ROOT/a.candidate,root,ignore=shutil.ignore_patterns('__pycache__','game','scratch'));(root/'game').mkdir()
  (root/'scripts/program_policy.py').write_text('import time\ndef decide(*args,**kwargs):\n time.sleep(20)\n')
  original=(root/'scripts/decide.py').read_text()
  for n in range(8):
   instrumented=n>=4
   if instrumented:
    (root/'scripts/decide.py').write_text(original.replace('START=time.monotonic()',"START=time.monotonic()\nimport os as _probe_os\nwith open('entry-probe.txt','a') as _probe:\n _probe.write(str(START)+' '+str(_probe_os.getpid())+'\\n')"))
   s=state|{'game_id':a.name+'-'+str(n)};(root/'game/state.json').write_text(json.dumps(s));start=time.monotonic()
   proc=subprocess.Popen([sys.executable,'scripts/decide.py'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
   time.sleep(.15);(root/'game/state.json').write_text(json.dumps(s|{'seq':s['seq']+1}));outer=False
   try:out,err=proc.communicate(timeout=2.5)
   except subprocess.TimeoutExpired:
    outer=True;os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate(timeout=2)
   elapsed=time.monotonic()-start
   try:answer=json.loads(out)
   except ValueError:answer={}
   entries=(root/'entry-probe.txt').read_text().splitlines() if instrumented else []
   parent_entry=next((float(x.split()[0]) for x in entries if x.split()[1]==str(proc.pid)),None)
   records.append({'instrumented':instrumented,'elapsed_s':elapsed,'python_entry_delay_s':parent_entry-start if parent_entry else None,'refresh_required':answer.get('refresh_required',False),'stale_action':answer.get('action') is not None,'outer_timeout':outer,'returncode':proc.returncode,'stderr':err[-300:]})
   write(ROOT/'docs/secret_hunter_response'/ (a.name+'.json'),{'candidate':a.candidate,'cases':records,'latency_s':quantiles([r['elapsed_s'] for r in records]),'prior_failure':'The historical Y1 concurrent-load timeout remains recorded; this independent rerun does not erase it.','independent_run':'No match/continuation worker pool was active during this test.'})
 finish(a.name,actual_short=len(records));assert all(r['refresh_required'] and not r['stale_action'] and not r['outer_timeout'] and r['elapsed_s']<2 for r in records),records
 print(json.dumps({'name':a.name,'cases':len(records),'max_s':max(r['elapsed_s'] for r in records),'stale_actions':0,'outer_timeouts':0}))
if __name__=='__main__':main()
