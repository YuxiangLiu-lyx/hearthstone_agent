"""Small mandatory paired terminal replay before a newly initialized pilot."""
from development.secret_hunter_mcgs.replays import source_cases,build,translate,condition,clone,continue_plan


def run(db,folder):
    from development.secret_hunter_mcgs.train import meta,setmeta,atomic
    for name,row,plans in source_cases(folder):
        scenario={'wolf':'beasts','amani':'coil'}.get(name,'sampled')
        world=build(row['state'],20100);translate(world);condition(world,scenario,30100)
        for plan in (plans[0],plans[-1]):
            path=folder/'pilot-replays'/f'{name}-{plan}.json'
            if path.exists():continue
            count=meta(db,'continuations',0)
            if count>=meta(db,'manifest')['limits']['continuations']:return
            setmeta(db,'continuations',count+1)
            result=continue_plan(clone(world,40100),plan,scenario,50100,trace=True)
            result.update(case=name,scenario=scenario,plan=plan,attempt=count+1)
            atomic(path,result)
