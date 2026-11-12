"""Budgeted isolated arm runner; preserves errors, both seats and exact schedules."""
import argparse,json,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
from development.teacher_eval.run import worker,summarize,snapshot
from development.secret_hunter_response.accounting import reserve,finish

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--name',required=True)
    p.add_argument('--population',choices=['core','guardrail'],default='core');p.add_argument('--start',type=int,required=True);p.add_argument('--seeds',type=int,required=True)
    p.add_argument('--workers',type=int,default=6);p.add_argument('--final',action='store_true');a=p.parse_args()
    assert 1<=a.workers<=6
    from development.secret_hunter_dgm.deck_guard import check
    src=ROOT/a.candidate;check(src);dest=ROOT/'experiments'/('secret-hunter-response-'+a.name)
    popfile=ROOT/f'development/teacher_eval/{a.population}.json';pop=json.loads(popfile.read_text());n=len(pop)*2*a.seeds
    freeze=json.loads((ROOT/'docs/secret_hunter_response/freeze.json').read_text())['populations'][a.population]
    assert sha(popfile)==freeze['sha256'] and snapshot(pop)==freeze['opponents']
    assert not dest.exists()
    if a.final:
        frozen=json.loads((ROOT/'docs/secret_hunter_response/final-freeze.json').read_text())
        assert src.name in frozen['arms_'+a.population]
        assert fingerprint(src)==frozen['source_hashes'][src.name]
        expected_start=961000 if a.population=='core' else 962000
        assert a.start==expected_start and a.seeds==(80 if a.population=='core' else 20)
    else:assert all(960000<=s<960900 for s in range(a.start,a.start+a.seeds))
    reserve(a.name,full=n,final=a.final,seconds=1800);dest.mkdir()
    manifest={**vars(a),'candidate_sha256':fingerprint(src),'population_sha256':sha(popfile),'opponent_versions':snapshot(pop),'population':pop,'planned_games':n,'split':'confirmation' if a.final else 'development'}
    write(dest/'config.json',manifest)
    tasks=[(str(src),o,s,i,str(dest),'python') for o in pop for s in range(a.start,a.start+a.seeds) for i in (1,2)];rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool,(dest/'results.jsonl').open('w') as f:
        fs=[pool.submit(worker,t) for t in tasks]
        for future in as_completed(fs):
            r=future.result();rows.append(r);f.write(json.dumps(r)+'\n');f.flush()
            if len(rows)%48==0:print(a.name,len(rows),n,flush=True)
    assert len({(r['opponent'],r['seed'],r['seat']) for r in rows})==n
    assert fingerprint(src)==manifest['candidate_sha256'] and snapshot(pop)==freeze['opponents']
    report=summarize(rows);g=report['by_group'];report['primary']=.5*g['astra']['win_rate']+.5*g['bot2']['win_rate'] if 'astra' in g else None
    # Audit both players, not just the policy seat.
    report['both_sides_illegal']=sum(sum(r.get('result',{}).get('illegal_counts',{}).values()) for r in rows)
    report['both_sides_timeouts']=sum(sum(r.get('result',{}).get('timeouts',{}).values()) for r in rows)
    write(dest/'summary.json',report);finish(a.name,completed=len(rows),wins=report['all']['wins'])
    check(src)
    print(json.dumps({'name':a.name,'all':report['all'],'primary':report['primary'],'opponents':{k:v['wins'] for k,v in report['by_opponent'].items()},'latency':report['latency_s']}),flush=True)
if __name__=='__main__':main()
