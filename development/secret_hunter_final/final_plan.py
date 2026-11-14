"""Seal a larger holdout before opening it, without changing promotion rules."""
import argparse
import json
import time
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train


def main():
    p=argparse.ArgumentParser();p.add_argument('--core-seeds',type=int,default=100);a=p.parse_args()
    db=train.connect(RUN);assert not train.meta(db,'final_opened',False)
    assert not (RUN/'final-freeze.json').exists()
    assert 40<=a.core_seeds<=100
    total=3024+2*(12*a.core_seeds+224)+6;assert total<=6000
    path=RUN/'final-plan-amendment.json';assert not path.exists()
    data={'created':time.time(),'original_final_core':[41400000,41400039],
          'seeds':{'final_core':[41400000,41400000+a.core_seeds-1],'final_guard':[41500000,41500007]},
          'planned_full_attempts':total,'planned_development_attempts':3024,
          'final_games_per_arm':12*a.core_seeds+224,'auxiliary_full_games_reserved':6,
          'reason':'Before any final outcome: the second development block has zero mulligan exposure. Increase independent final seed groups to measure the rare rule; keep one challenger and all original promotion thresholds.',
          'no_final_opened':True,'promotion_unchanged':train.meta(db,'manifest')['promotion']}
    train.atomic(path,data);train.atomic(ROOT/'docs/secret_hunter_final/final-plan-amendment.json',data)
    print(json.dumps(data))


if __name__=='__main__':main()
