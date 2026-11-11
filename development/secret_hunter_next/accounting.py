"""Append-only attempt reservations; interrupted work is never silently refunded."""
import fcntl,json,time
from development.secret_hunter_program.common import ROOT,write
D=ROOT/'docs/secret_hunter_next'
def reserve(name,full=0,short=0,final=False):
    with (D/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads((D/'budget.json').read_text())
        assert name not in {r['name'] for r in b['runs']},name
        f=sum(r['full'] for r in b['runs']);s=sum(r['short'] for r in b['runs'])
        reserve_left=max(0,b['final_reserve']-sum(r['full'] for r in b['runs'] if r['final']))
        assert f+full+(0 if final else reserve_left)<=b['limits']['full_games']
        assert s+short<=b['limits']['short_branches']
        assert sum(r.get('elapsed_s',time.time()-r['started']) for r in b['runs'])<b['limits']['experiment_seconds']
        b['runs'].append({'name':name,'full':full,'short':short,'final':final,'started':time.time(),'status':'reserved'})
        write(D/'budget.json',b)
def finish(name,**details):
    with (D/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);b=json.loads((D/'budget.json').read_text());r=next(r for r in b['runs'] if r['name']==name)
        r.update(elapsed_s=time.time()-r['started'],status='completed',**details);write(D/'budget.json',b)
