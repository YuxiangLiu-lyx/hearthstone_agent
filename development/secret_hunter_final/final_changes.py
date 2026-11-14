"""Post-freeze attribution of actual CLI changes; never used to retune code."""
from collections import Counter
import json
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train
from development.secret_hunter_final.counterfactual import visible


def main():
    challenger=json.loads((RUN/'final-freeze.json').read_text())['arms'][1];out={}
    for batch in ['final-core','final-guard']:
        rows={a:{(r['opponent'],r['seed'],r['seat']):r for line in (RUN/'batches'/batch/a/'results.jsonl').read_text().splitlines() if (r:=json.loads(line))} for a in ['B',challenger]}
        assert rows['B'].keys()==rows[challenger].keys()
        counts=Counter();changes=[];flips=[]
        for key,base in rows['B'].items():
            logs={}
            for a in rows:
                r=rows[a][key];p=RUN/'batches'/batch/a/'games'/r['game']/f'p{r["seat"]}/observations.jsonl'
                logs[a]=[json.loads(x) for x in p.read_text().splitlines()]
            proof=sum(z['info'].get('lethal',{}).get('proof')=='visible_burn_and_steady_shot_only' for z in logs[challenger])
            counts['narrow_proof_calls']+=proof;counts['narrow_proof_games']+=bool(proof)
            first=None
            for left,right in zip(logs['B'],logs[challenger]):
                if visible(left['state'])!=visible(right['state']):kind='upstream_state_divergence'
                elif left['action']!=right['action']:
                    if left['state']['phase']=='mulligan':kind='mulligan'
                    elif right['info'].get('lethal',{}).get('proof')=='visible_burn_and_steady_shot_only':kind='narrow_lethal'
                    else:kind='other_same_state_action'
                else:continue
                first={'kind':kind,'seq':left['state']['seq'],'baseline_action':left['action'],'candidate_action':right['action'],
                       'baseline_reason':left['info'].get('reason'),'candidate_reason':right['info'].get('reason'),
                       'baseline_time_bounded':left['info'].get('turn_search',{}).get('stop_reason')=='time',
                       'candidate_time_bounded':right['info'].get('turn_search',{}).get('stop_reason')=='time'}
                break
            candidate=rows[challenger][key]
            if first:
                counts[first['kind']]+=1
                changes.append({'key':key,'baseline_score':base['score'],'candidate_score':candidate['score'],'first_difference':first})
            if base['score']!=candidate['score']:
                assert first,(batch,key,'outcome changed with identical observations/actions')
                flips.append(changes[-1])
        out[batch]={'games_per_arm':len(rows['B']),'coverage':dict(counts),'changed_games':changes,'flips_and_regressions':flips,
                    'scope':'First observed divergence attribution only; later causal effects can interact. Timing-bound flags are diagnostics, not proof of timing causation.'}
    train.atomic(ROOT/'docs/secret_hunter_final/final-action-changes.json',out)
    print(json.dumps({b:{'coverage':v['coverage'],'outcome_changes':len(v['flips_and_regressions'])} for b,v in out.items()}))


if __name__=='__main__':main()
