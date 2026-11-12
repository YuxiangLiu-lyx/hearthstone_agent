"""Atomic attempt and wall-time reservations; no refund for interrupted attempts."""
import fcntl,json,os,time
from development.secret_hunter_program.common import ROOT
D=ROOT/'docs/secret_hunter_face_validation'
def save(b):
 p=D/'budget.tmp';p.write_text(json.dumps(b,indent=2)+'\n');os.replace(p,D/'budget.json')
def reserve(name,full=0,short=0,final=False,seconds=600):
 with (D/'budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads((D/'budget.json').read_text())
  assert name not in {r['name'] for r in b['runs']},name
  f=sum(r['full'] for r in b['runs']);s=sum(r['short'] for r in b['runs'])
  reserve_left=max(0,b['final_reserve']-sum(r['full'] for r in b['runs'] if r['final']))
  elapsed=sum(r.get('elapsed_s',r['reserved_seconds']) for r in b['runs'])
  time_left=max(0,b['final_time_reserve']-sum(r.get('elapsed_s',r['reserved_seconds']) for r in b['runs'] if r['final']))
  assert f+full+(0 if final else reserve_left)<=b['limits']['full_games']
  assert s+short<=b['limits']['short_branches']
  assert elapsed+seconds+(0 if final else time_left)<=b['limits']['experiment_seconds']
  b['runs'].append({'name':name,'full':full,'short':short,'final':final,'reserved_seconds':seconds,'started':time.time(),'status':'reserved','pid':os.getpid()});save(b)
def finish(name,**details):
 with (D/'budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads((D/'budget.json').read_text());r=next(r for r in b['runs'] if r['name']==name)
  r.update(elapsed_s=time.time()-r['started'],status='completed',**details);save(b)
  assert r['elapsed_s']<=r['reserved_seconds'],'Wall reservation exceeded; stop scheduling'

def fail(name,evidence,ended=None):
 """Close failed experiment accounting while retaining all reservations."""
 with (D/'budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads((D/'budget.json').read_text());r=next(r for r in b['runs'] if r['name']==name)
  r.update(elapsed_s=max(0,(ended or time.time())-r['started']),status='failed',failure=evidence);save(b)
