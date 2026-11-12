"""Cold end-to-end timing, cooperative and noncooperative failure checks."""
import argparse,json,shutil,subprocess,sys,tempfile,time,math
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.common import readlines
from development.secret_hunter_response.accounting import reserve,finish

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='development/secret_hunter_dgm/candidates/M2');p.add_argument('--out',default='docs/secret_hunter_response/runtime-checks.json');a=p.parse_args()
    reserve('runtime-'+Path(a.candidate).name,short=120)
    candidate=ROOT/a.candidate;sys.path.insert(0,str(candidate/'scripts'));from action_validator import legal
    folder=ROOT/'experiments/secret-hunter-response-y1-response-data';states=[]
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
        s={**mainstates[0],'game_id':'cache-test'};first=run(s,'cache_initial');second=run(s,'cache_repeat');assert first==second and cases[-1]['cache_hit']
        changed={**s,'seq':s['seq']+1};run(changed,'new_seq');assert not cases[-1]['cache_hit']
        changed={**s,'game_id':'different-game'};run(changed,'new_game');assert not cases[-1]['cache_hit']
        for tag,body in [('worker_hang','import time\ndef decide(*args, **kwargs):\n time.sleep(20)\n'),('worker_crash','def decide(*args, **kwargs):\n raise RuntimeError("injected crash")\n')]:
            (root/'scripts/program_policy.py').write_text(body);run({**s,'game_id':tag},tag);assert cases[-1]['worker_error']
            if tag=='worker_hang':assert cases[-1]['worker_error']=='worker_timeout' and cases[-1]['elapsed_s']>=1.7
            else:assert 'injected crash' in cases[-1]['worker_error']
        (root/'scripts/program_policy.py').write_text('import time\nfrom secret_policy import rank\ndef decide(state,config,publish=None,**kwargs):\n action=rank(state,config)[0][1]\n publish(action,{"fallback":False,"reason":"published_before_hang","nodes":0})\n time.sleep(20)\n')
        run({**s,'game_id':'saved-best'},'saved_best_on_timeout');assert cases[-1]['worker_error']=='worker_timeout' and cases[-1]['info']['reason']=='published_before_hang'
        (root/'scripts/program_policy.py').write_text(code)
        tiny=cfg|{'total_budget_s':.06,'search_soft_s':0};(root/'config.json').write_text(json.dumps(tiny));run({**s,'game_id':'tiny'},'tiny_budget')
        (root/'config.json').write_text(json.dumps(cfg));run(s,'emergency',True)
        run({'phase':'deck_submission','seq':0,'game_id':'deck'},'deck_submission')
        run({'phase':'game_over','seq':99,'game_id':'over'},'game_over')
        history=root/'game/history.jsonl'
        history.write_text('\n'.join(json.dumps({'event':'turn_start','turn':1,'player':1}) for _ in range(35000)))
        run({**s,'game_id':'long-history'},'long_history')
        history.write_text('{broken json\n')
        run({**s,'game_id':'malformed-history'},'malformed_history')
        assert cases[-1]['worker_error']=='history_parse_error'
        history.unlink()
        statepath.write_text('{invalid')
        start=time.monotonic();proc=subprocess.run([sys.executable,'scripts/decide.py'],cwd=root,capture_output=True,text=True,timeout=3)
        assert proc.returncode==0 and json.loads(proc.stdout)['refresh_required']
        cases.append({'tag':'malformed_state_requests_refresh','elapsed_s':time.monotonic()-start,'valid':True})
        # Malformed action IDs must never compare equal to valid integer identifiers.
        for bad in [True,40.0,'40']:
            assert not legal({'phase':'main','legal_actions':[{'type':'play_card','card':40}]},{'type':'play_card','card':bad})
    times=sorted(c['elapsed_s'] for c in cases);normal=sorted(c['elapsed_s'] for c in cases if c['tag'].startswith('cold'))
    def stats(xs):return {str(q):xs[min(len(xs)-1,math.ceil(len(xs)*q)-1)] for q in [.5,.95,.99,1]}
    result={'cases':len(cases),'all_latency_s':stats(times),'cold_latency_s':stats(normal),'over_2s':sum(x>2 for x in times),'illegal':sum(not c['valid'] for c in cases),'details':cases}
    finish('runtime-'+Path(a.candidate).name,actual_short=len(cases));write(ROOT/a.out,result);print(json.dumps({k:v for k,v in result.items() if k!='details'}))
if __name__=='__main__':main()
