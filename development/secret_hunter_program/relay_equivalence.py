"""Verify the F2 correction and replay F1 relay decisions from public histories."""
import json,sys
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha,write,readlines
from development.secret_hunter_program.accounting import record_cases
sys.path.insert(0,str(ROOT/'development/secret_hunter_program/release-F2/secret-hunter-program/scripts'))
from program_policy import decide
from state_features import with_public_history


def main():
    old=ROOT/'development/secret_hunter_program/release/secret-hunter-program';new=ROOT/'development/secret_hunter_program/release-F2/secret-hunter-program'
    files=[p for p in old.rglob('*') if p.is_file() and '__pycache__' not in p.parts];changed=[str(p.relative_to(old)) for p in files if sha(p)!=sha(new/p.relative_to(old))]
    assert sorted(changed)==['config.json','scripts/tactical_model.py']
    a=json.loads((old/'config.json').read_text());b=json.loads((new/'config.json').read_text())
    for k in ['version','parent']:a.pop(k);b.pop(k)
    assert a==b
    text=(old/'scripts/tactical_model.py').read_text().replace('"NEW1_032": (4, 2, True, False)','"NEW1_032": (4, 4, False, True)').replace('"NEW1_034": (4, 4, False, True)','"NEW1_034": (4, 2, True, False)')
    assert text==(new/'scripts/tactical_model.py').read_text()
    cfg=json.loads((new/'config.json').read_text());details=[];folder=ROOT/'experiments/program-final-relay-smoke'
    for r in readlines(folder/'results.jsonl'):
        seat=folder/'games'/r['game']/f'p{r["seat"]}';calls={c['arguments']['seq']:c['arguments']['action'] for c in readlines(seat/'seat/mcp_calls.jsonl') if c['tool']=='act'};history=[]
        for path in sorted((seat/'decisions').glob('*.state.json')):
            state=json.loads(path.read_text());history.extend(state.get('events',[]))
            if state['seq'] not in calls:continue
            state=with_public_history(state,history);action,info=decide(state,cfg)
            details.append({'game':r['game'],'seq':state['seq'],'equal':action==calls[state['seq']],'f2_action':action,'f1_actual':calls[state['seq']]})
    record_cases('f2-replay-of-77-public-relay-decisions',len(details))
    result={'changed_files':changed,'decision_and_relay_functions_unchanged':True,'cases':len(details),'identical_actions':sum(r['equal'] for r in details),'details':details,
        'limitation':'The exact F2 ZIP was not run through the model host; the two-game cap was already reached. This public-state replay plus identical active code supports interface equivalence, not a third smoke game.'}
    write(ROOT/'docs/secret_hunter_program/f2-relay-equivalence.json',result);print(json.dumps({k:v for k,v in result.items() if k!='details'}))
if __name__=='__main__':main()
