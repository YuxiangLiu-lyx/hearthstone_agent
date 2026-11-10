"""Check real model actions against the stateless policy and actual printed CLI results."""
import argparse,json
from pathlib import Path
from development.benchmarks.run import load_policy

def main():
    p=argparse.ArgumentParser();p.add_argument('experiment');p.add_argument('--skill',default='submission/hearthstone-agent')
    p.add_argument('--out',required=True);args=p.parse_args()
    policy,_=load_policy(args.skill);config_path=Path(args.skill)/'config.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else {}
    results=[]
    for folder in sorted(Path(args.experiment).glob('*/p*/decisions')):
        transcript=folder.parent/'seat/session_1.jsonl'
        printed={}
        if transcript.exists():
            for line in transcript.read_text().splitlines():
                event=json.loads(line);item=event.get('item',{})
                if event.get('type')!='item.completed' or item.get('type')!='command_execution':continue
                if 'scripts/decide.py' not in item.get('command',''):continue
                for output in item.get('aggregated_output','').splitlines():
                    try:r=json.loads(output)
                    except ValueError:continue
                    if isinstance(r,dict) and 'seq' in r and 'action' in r:printed[r['seq']]=r['action']
        n=0;exact=0;cli_relay=0;diff=[]
        for f in sorted(folder.glob('*.action.json')):
            state=json.loads(f.with_name(f.name.replace('.action.json','.state.json')).read_text())
            action=json.loads(f.read_text())['action']
            if state['phase']=='deck_submission':continue
            expected=policy.decide(state,config);n+=1
            exact+=expected==action
            cli_relay+=printed.get(state['seq'])==action
            if action!=expected:diff.append({'seq':state['seq'],'actual':action,'expected':expected,
                                            'printed_action':printed.get(state['seq'])})
        results.append({'path':str(folder),'decisions':n,'exact_policy_matches':exact,
                        'script_invoked_and_relayed':cli_relay,'differences':diff})
    output={'experiment':args.experiment,'skill':args.skill,'games_and_seats':results,
            'decisions':sum(r['decisions'] for r in results),'exact_policy_matches':sum(r['exact_policy_matches'] for r in results),
            'script_invoked_and_relayed':sum(r['script_invoked_and_relayed'] for r in results)}
    Path(args.out).write_text(json.dumps(output,indent=2));print(json.dumps({k:v for k,v in output.items() if k!='games_and_seats'},indent=2))

if __name__=='__main__':main()
