"""Cold end-to-end timing, cooperative and noncooperative failure checks."""
import argparse,json,shutil,subprocess,sys,tempfile,time,math
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines
from development.secret_hunter_dgm.accounting import reserve,finish

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='development/secret_hunter_dgm/candidates/M2');p.add_argument('--out',default='docs/secret_hunter_dgm/runtime-checks.json');a=p.parse_args()
    reserve('cold-'+Path(a.candidate).name,short=120)
    candidate=ROOT/a.candidate;sys.path.insert(0,str(candidate/'scripts'));from action_validator import legal
    folder=ROOT/'experiments/secret-hunter-dgm-c1-screen';states=[]
    for r in readlines(folder/'results.jsonl')[:20]:
        states.extend(x['state'] for x in readlines(folder/'games'/r['game']/f'p{r["seat"]}/observations.jsonl'))
    mainstates=[s for s in states if s['phase']=='main'];mainstates.sort(key=lambda s:len(s['you']['board'])*len(s['opponent']['board'])+len(s['you']['hand']),reverse=True)
    cases=[]
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)/'skill';shutil.copytree(candidate,root,ignore=shutil.ignore_patterns('__pycache__','scratch','game'));(root/'game').mkdir()
        statepath=root/'game/state.json';cfg=json.loads((root/'config.json').read_text());code=(root/'scripts/program_policy.py').read_text()
        def run(s,tag,emergency=False):
            statepath.write_text(json.dumps(s));start=time.monotonic()
            proc=subprocess.run([sys.executable,'scripts/fallback.py' if emergency else 'scripts/decide.py'],cwd=root,capture_output=True,text=True,timeout=3)
            elapsed=time.monotonic()-start;assert proc.returncode==0,proc.stderr
            result=json.loads(proc.stdout)
            if s['phase']=='game_over':assert result['game_over'];valid=True
            elif s['phase']=='deck_submission':valid=result['action']['type']=='submit_deck' and result['action']['cards']==json.loads((root/'deck.json').read_text())['cards']
            else:valid=result['seq']==s['seq'] and legal(s,result['action'])
            assert valid,(tag,result)
            logs=readlines(root/'scratch/decisions.jsonl');last=logs[-1] if logs and tag!='emergency' else {}
            cases.append({'tag':tag,'elapsed_s':elapsed,'valid':valid,'action':result.get('action'),'worker_error':last.get('worker_error'),'cache_hit':last.get('cache_hit'),'info':last.get('info')})
            return result
        for n,s in enumerate(mainstates[:60]):
            s={**s,'game_id':'cold-'+str(n)};run(s,'cold_crowded' if n<10 else 'cold_normal')
    times=sorted(c['elapsed_s'] for c in cases);normal=sorted(c['elapsed_s'] for c in cases if c['tag'].startswith('cold'))
    def stats(xs):return {str(q):xs[min(len(xs)-1,math.ceil(len(xs)*q)-1)] for q in [.5,.95,.99,1]}
    result={'cases':len(cases),'all_latency_s':stats(times),'cold_latency_s':stats(normal),'over_2s':sum(x>2 for x in times),'illegal':sum(not c['valid'] for c in cases),'details':cases}
    finish('cold-'+Path(a.candidate).name,actual_short=len(cases));write(ROOT/a.out,result);print(json.dumps({k:v for k,v in result.items() if k!='details'}))
if __name__=='__main__':main()
