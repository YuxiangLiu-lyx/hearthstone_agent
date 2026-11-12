"""Allocate paired terminal continuations to fresh public disagreement states."""
import json
import sys
from development.secret_hunter_mcgs.build import HERE,Y1

def run(db,folder,batch,hard):
    from development.secret_hunter_mcgs.train import meta,setmeta,atomic
    sys.path[:0]=[str(HERE),str(Y1/'scripts')]
    from development.secret_hunter_mcgs.replays import build,clone,continue_plan
    from program_policy import decide
    cfg=json.loads((Y1/'config.json').read_text());reports=[]
    # Deduplicate by whole source seed and tactical action kind; retain a harmed win.
    selected=[];seen=set()
    for h in sorted(hard,key=lambda h:h['candidate_score']-h['baseline_score']):
        group=(h['key'][0],h['decision']['action']['type'])
        if group in seen:continue
        seen.add(group);selected.append(h)
        if len(selected)==2:break
    for index,h in enumerate(selected):
        state=h['decision']['state'];baseline=decide(state,cfg)[0];new=h['decision']['action']
        for sample in range(4):
            for label,action in [('y1',baseline),('candidate',new)]:
                path=folder/'paired_continuations'/f'{batch}-{index}-{sample}-{label}.json'
                if path.exists():continue
                count=meta(db,'continuations',0)
                if count>=meta(db,'manifest')['limits']['continuations']:return
                setmeta(db,'continuations',count+1)
                row={'source_group':h['key'],'source_game':state.get('game_id'),'seq':state['seq'],
                     'sample':sample,'arm':label,'action':action,'attempt':count+1,
                     'scope':'Conditional public-compatible particles, matched future seed; complete cheap common continuation after forced first action.'}
                try:
                    world=build(state,90100+sample);world.game.random.seed(90200+sample)
                    assert world.step(1,action).accepted
                    row.update(continue_plan(world,'follow','sampled',90300+sample,trace=sample==0))
                except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
                atomic(path,row);reports.append({k:v for k,v in row.items() if k!='trace'})
    atomic(folder/'paired_continuations'/f'{batch}-summary.json',reports)
    setmeta(db,'next_experiment',{'batch':batch,'failure_archive':str(folder/'hard_cases'/f'{batch}.json'),
        'proposal':'Inspect paired losses: separate poor response particles from cutoff value error; keep a fixed-transition UCT parent.',
        'requires_code_agent':True,'autonomous_configuration_evaluation_continues':True})
