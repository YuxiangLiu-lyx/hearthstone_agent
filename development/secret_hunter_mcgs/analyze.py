"""Freeze inspectable pilot tables and an actual full-CLI harmed-win trajectory."""
import json
from pathlib import Path
from development.secret_hunter_mcgs.build import ROOT


def main():
    run=ROOT/'runs/krush-mcgs';docs=ROOT/'docs/secret_hunter_mcgs'
    reports={name:json.loads((run/'batches'/name/'report.json').read_text())
             for name in ('pilot-100','pilot-101','pilot-102','cli-103')}
    (docs/'pilot-results.json').write_text(json.dumps(reports,indent=2)+'\n')
    records=json.loads((docs/'ablations.json').read_text())['results'];ablation=[]
    for variant in dict.fromkeys(r['variant'] for r in records):
        rs=[r for r in records if r['variant']==variant]
        ablation.append({'variant':variant,'cases':len(rs),'transitions':sum(r['metrics']['transitions'] for r in rs),
            'states':sum(r['unique_states'] for r in rs),'transpositions':sum(r['transpositions'] for r in rs),
            'chance_samples':sum(r['metrics'].get('chance_samples',0) for r in rs),
            'completed_horizons':sum(r['metrics'].get('iterations',0) for r in rs),
            'cross_turn':sum(r['metrics'].get('cross_turn',0) for r in rs),
            'terminal':sum(r['metrics'].get('terminal',0) for r in rs),'changed':sum(r['changed'] for r in rs)})
    (docs/'ablation-summary.json').write_text(json.dumps(ablation,indent=2)+'\n')
    parent=run/'batches/cli-103'
    rows={name:[json.loads(l) for l in (parent/name/'results.jsonl').read_text().splitlines()]
          for name in ('Y1','M5-dpw')}
    key=lambda r:(r['seed'],r['opponent'],r['seat'])
    baselines={key(r):r for r in rows['Y1']}
    for new in rows['M5-dpw']:
        old=baselines[key(new)]
        if old['score']!=1 or new['score']!=0:continue
        traces={name:[json.loads(l) for l in (parent/name/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl').read_text().splitlines()]
                for name,r in [('Y1',old),('M5-dpw',new)]}
        pairs=list(zip(traces['Y1'],traces['M5-dpw']))
        divergence=next((i for i,(a,b) in enumerate(pairs) if a['action']!=b['action']),None)
        if divergence is None:continue
        result={'source_group':key(new),'execution':'full_cli','baseline_result':old,'candidate_result':new,
                'first_action_divergence_index':divergence,'first_divergence':{name:t[divergence] for name,t in traces.items()},
                'full_student_view_trajectories':traces,
                'scope':'Actual paired full games; random streams can diverge after different actions. One case is not causal proof.'}
        (run/'evidence/mcgs-harmed-win.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('full_student_view_trajectories','first_divergence','baseline_result','candidate_result')}));break
    print(json.dumps(ablation))


if __name__=='__main__':main()
