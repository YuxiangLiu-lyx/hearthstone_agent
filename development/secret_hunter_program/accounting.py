"""Single locked ledger for matches and short continuations."""
import fcntl,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def record_cases(name,count):
    p=ROOT/'docs/secret_hunter_program/budget.json'
    with (p.parent/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);x=json.loads(p.read_text())
        assert sum(r['count'] for r in x['short_continuations'])+count<=x['limits']['short_continuations']
        x['short_continuations'].append({'name':name,'count':count});p.write_text(json.dumps(x,indent=2)+'\n')
