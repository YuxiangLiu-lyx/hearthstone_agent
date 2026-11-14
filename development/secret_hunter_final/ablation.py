"""Strict paired decomposition and observed mechanism coverage on development."""
import json
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import paired


def main():
    db=train.connect(RUN);result={}
    for batch in ['dev-core','dev-guard','dev2-core','dev2-guard']:
        d=json.loads((RUN/'batches'/batch/'report.json').read_text());arms=list(d['arms'])
        rows={a:[json.loads(x) for x in (RUN/'batches'/batch/a/'results.jsonl').read_text().splitlines()] for a in arms}
        combo='ML2' if 'ML2' in arms else 'ML';lethal='L2' if 'L2' in arms else 'L'
        comparisons={}
        for a,b in [('B','M'),('B',lethal),('B',combo),('M',combo)]:
            comparisons[f'{a} -> {b}']={'all':paired(rows[a],rows[b])}
            if 'core' in batch:comparisons[f'{a} -> {b}']['primary']=paired(rows[a],rows[b],groups=['astra','bot2'],equal_groups=True)
        coverage={}
        for arm in arms:
            games=0;calls=0;mulligans=[]
            for r in rows[arm]:
                file=RUN/'batches'/batch/arm/'games'/r['game']/f'p{r["seat"]}/observations.jsonl'
                logs=[json.loads(x) for x in file.read_text().splitlines()];n=0
                for z in logs:
                    if z['info'].get('lethal',{}).get('proof')=='visible_burn_and_steady_shot_only':n+=1
                    if z['state']['phase']=='mulligan':mulligans.append({'key':[r['opponent'],r['seed'],r['seat']],'action':z['action'],'actual_first':r['first_player']==r['seat']})
                games+=bool(n);calls+=n
            coverage[arm]={'narrow_lethal_calls':calls,'narrow_lethal_games':games,'mulligans':mulligans}
        base={tuple(x['key']):x for x in coverage['B']['mulligans']}
        for arm,summary in coverage.items():
            changed=[x for x in summary.pop('mulligans') if x['action']!=base[tuple(x['key'])]['action']]
            summary['changed_mulligan_games']=len(changed);summary['changed_mulligan_first']=sum(x['actual_first'] for x in changed)
            summary['changed_mulligan_keys']=[x['key'] for x in changed]
        result[batch]={'comparisons':comparisons,'coverage':coverage}
    train.atomic(ROOT/'docs/secret_hunter_final/ablation.json',result)
    print(json.dumps({b:{k:{'wins':[v['all']['a_wins'],v['all']['b_wins']],'flip_regression':[v['all']['b_only_wins'],v['all']['a_only_wins']]} for k,v in d['comparisons'].items()} for b,d in result.items()}))


if __name__=='__main__':main()
