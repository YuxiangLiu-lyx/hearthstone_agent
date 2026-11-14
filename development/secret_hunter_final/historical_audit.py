"""Reaggregate prior final rows; never count old seeds as new evidence."""
import argparse
import json
from pathlib import Path
import shutil
from development.secret_hunter_final.study import ROOT,RUN
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import sha
from development.teacher_eval.run import summarize
from development.teacher_eval.compare import paired


def main():
    p=argparse.ArgumentParser();p.add_argument('--prior',type=Path,default=Path('/Users/liuyuxiang/.codex/worktrees/hearthstone-turn-plans-20261112/runs/turn-plans-20261112'));a=p.parse_args()
    dest=RUN/'historical-aggregate';dest.mkdir(exist_ok=True);out={'scope':'Historical reference only; no new games or independent seed groups','batches':{},'files':{}}
    for batch in ['final-core','final-guard']:
        rows={}
        for arm in ['Y1','engine-trap-v2','E2-finish-minions']:
            saved=dest/f'{batch}-{arm}.jsonl';source=a.prior/'batches'/batch/arm/'results.jsonl'
            if not saved.exists():shutil.copy2(source,saved)
            rows[arm]=[json.loads(x) for x in saved.read_text().splitlines()]
            out['files'][str(saved.relative_to(ROOT))]=sha(saved)
        out['batches'][batch]={'arms':{arm:summarize(rs) for arm,rs in rows.items()},
            'Y1_to_B':paired(rows['Y1'],rows['engine-trap-v2']),
            'B_to_E2':paired(rows['engine-trap-v2'],rows['E2-finish-minions'])}
        if batch=='final-core':
            early=[];late=[]
            for r in rows['engine-trap-v2']:
                if r['group']!='astra' or r['score']:continue
                source=a.prior/'batches'/batch/'engine-trap-v2/games'/r['game']/f'p{r["seat"]}/observations.jsonl'
                saved=dest/'astra-loss-logs'/f'{r["game"]}-p{r["seat"]}.jsonl'
                if not saved.exists():
                    if not source.exists():continue
                    saved.parent.mkdir(exist_ok=True);shutil.copy2(source,saved)
                logs=[json.loads(x) for x in saved.read_text().splitlines()]
                maximum=max(z['state']['you']['max_mana'] for z in logs if z['state']['phase']=='main')
                (early if maximum<9 else late).append({'opponent':r['opponent'],'seed':r['seed'],'seat':r['seat'],'max_mana':maximum,'log':str(saved.relative_to(ROOT)),'log_sha256':sha(saved)})
            out['prior_astra_losses']={'before_nine':early,'reached_nine':late,'missing':50-len(early)-len(late)}
    train.atomic(ROOT/'docs/secret_hunter_final/historical-aggregate.json',out)
    print(json.dumps({b:{arm:[v['all']['wins'],v['all']['n']] for arm,v in block['arms'].items()} for b,block in out['batches'].items()}))
    print(json.dumps({'prior_astra_before_nine':len(out['prior_astra_losses']['before_nine']),'missing':out['prior_astra_losses']['missing']}))


if __name__=='__main__':main()
