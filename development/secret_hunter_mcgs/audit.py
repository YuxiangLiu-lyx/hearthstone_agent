"""Freeze audit and cached-card equivalence; no simulator files are modified."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from development.secret_hunter_mcgs.build import ROOT,HERE,Y1
from development.secret_hunter_dgm.deck_guard import check

def cache_digest(mode):
    if mode=='cache':
        from development.secret_hunter_mcgs.mcgs_init import initialize
        initialize()
    from hs_arena._fp import init_engine
    cards=init_engine();data={}
    def safe(v):
        if callable(v):return {'callable':v.__module__+'.'+v.__qualname__}
        if isinstance(v,dict):return {str(k):safe(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [safe(x) for x in v]
        return v
    for cid,c in cards.db.items():
        data[cid]={'tags':safe(c.tags),'dbf_id':c.dbf_id,'hero_power':c.hero_power,
                   'requirements':safe(c.requirements),'entourage':c.entourage,
                   'name':c.name,'description':c.description}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def main():
    if len(sys.argv)>1:
        start=time.monotonic();digest=cache_digest(sys.argv[1]);print(json.dumps({'mode':sys.argv[1],'digest':digest,'seconds':time.monotonic()-start}));return
    results=[json.loads(subprocess.check_output([sys.executable,'-m','development.secret_hunter_mcgs.audit',mode],text=True)) for mode in ('original','cache')]
    assert results[0]['digest']==results[1]['digest'],results
    import hs_arena
    installed=Path(hs_arena.__file__).parent
    frozen=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text())['installed_files']
    for path,digest in frozen.items():assert hashlib.sha256((installed/path).read_bytes()).hexdigest()==digest,path
    decks={p.name:check(p) for p in (HERE/'candidates').iterdir() if p.is_dir()}
    check(Y1)
    result={'card_cache_equivalence':results,'installed_course_files_unchanged':len(frozen),'deck_guards':decks}
    (ROOT/'docs/secret_hunter_mcgs/integrity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
