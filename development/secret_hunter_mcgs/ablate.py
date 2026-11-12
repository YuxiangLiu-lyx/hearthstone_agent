"""Matched transition-cap ablations on the same original-deck public fixtures."""
import json,sys,time
from development.secret_hunter_mcgs.build import HERE,Y1,ROOT
sys.path[:0]=[str(HERE),str(Y1/'scripts')]
from development.secret_hunter_mcgs.replays import source_cases,translate
from mcgs_world import build
from mcgs_search import search
from program_policy import decide

def main():
    cfg=json.loads((Y1/'config.json').read_text());rows=[]
    variants={'UCT':{'graph':'uct','chance':'fixed'},'UCD-fixed':{'graph':'ucd','chance':'fixed'},
              'UCD-DPW':{'graph':'ucd','chance':'dpw'},'no-opponent-plays':{'opponent_plays':False},
              'own-turn-only':{'horizon':1},'filtered-rollout':{'rollout':'filtered'},'terminal-rollout':{'terminal':True}}
    for name,source,_ in source_cases(ROOT/'runs/krush-mcgs'):
        w=build(source['state'],991);translate(w);s=w.view(1);baseline=decide(s,cfg)[0]
        for variant,settings in variants.items():
            settings={'graph':'ucd','chance':'dpw','iterations':10000,'max_transitions':400,'horizon':3,**settings}
            r=search(s,{**cfg,**settings},baseline,time.monotonic()+20,seed=7721,max_transitions=400)
            rows.append({'case':name,'variant':variant,'baseline':baseline,'settings':settings,**r})
        print(name,flush=True)
    out={'transition_cap':400,'wall_ceiling_s':20,'results':rows,
         'scope':'Offline matched transition budget; actual transition/iteration counts reported, not full-match wins. Cold CLI separately uses the same 2-second envelope.'}
    (ROOT/'docs/secret_hunter_mcgs/ablations.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
