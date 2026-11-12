"""Replay two full positive/negative conditional plan divergences with engine events."""
import json
from development.secret_hunter_mcgs.replays import *

def main():
    folder=ROOT/'runs/krush-mcgs';saved=[]
    for name,scenario,sample,alternative in [('wolf','beasts',102,'wolf_then_face'),('amani','coil',100,'amani_trade')]:
        _,source,_=next(x for x in source_cases(folder) if x[0]==name)
        world=build(source['state'],20000+sample);changes=translate(world)
        w=clone(world,30000+sample);condition(w,scenario,30000+sample)
        outputs={}
        for plan in ('y1',alternative):
            outputs[plan]=continue_plan(clone(w,40000+sample),plan,scenario,50000+sample,trace=True)
        result={'case':name,'scenario':scenario,'sample':sample,'source_game':source['source_game'],
                'source_seq':source['state']['seq'],'source_original_action':source['original_action'],
                'translation':changes,'plans':outputs,'public_start':world.view(1),
                'scope':'Conditional illustrative continuation, not a separate full-game benchmark. The opponent rollout is fallible.'}
        path=folder/'evidence'/f'{name}-{sample}.json';path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(result,indent=2)+'\n');saved.append(str(path.relative_to(ROOT)))
    print(json.dumps(saved))
if __name__=='__main__':main()
