"""Mine public contexts from completed original-deck games; labels remain offline."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import RUN
sys.path.insert(0,str(Y1/'scripts'))
from development.secret_hunter_turn_plans.routes import context,public_features


def main():
    source=Path('/Users/liuyuxiang/.codex/worktrees/hearthstone-mcgs-20261112/runs/krush-mcgs')
    db=sqlite3.connect(f'file:{source}/ledger.sqlite?mode=ro',uri=True)
    selected=[];counts=Counter();hits={k:set() for k in ('trap','knife_wolf','amani')};seen=set();read_games=0;missing=0
    rows=db.execute("select batch,result,opponent from tasks where candidate='Y1' and status='done' and phase='development' and batch like 'gen-%' order by seed,seat")
    for batch,raw,spec in rows:
        row=json.loads(raw)
        if row.get('harness_error') or not row.get('game'):continue
        path=source/'batches'/batch/'Y1'/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl'
        if not path.exists():missing+=1;continue
        split='train' if int(hashlib.sha256(str(row['seed']).encode()).hexdigest()[:8],16)%5<3 else 'validation'
        read_games+=1
        history=[]
        with path.open() as stream:
            for line in stream:
                d=json.loads(line);s=d['state']
                history.extend(s.get('events',[]))
                for kind in context(s):
                    hits[kind].add(row['game']);key=(kind,row['seed'])
                    bucket=(kind,split,row['score'])
                    if key in seen or counts[bucket]>=3:continue
                    if s['you']['mana']<2:continue
                    enemy={m['card_id'] for m in s['opponent']['board']}
                    if kind=='trap' and 'EX1_556' not in enemy:continue
                    if kind=='knife_wolf' and not {'NEW1_019','EX1_162'}<=enemy:continue
                    if kind=='amani' and s['opponent']['hero']['hero_class']!='WARLOCK':continue
                    counts[bucket]+=1;seen.add(key)
                    selected.append({'case':f'{kind}-{len(selected):03d}','kind':kind,'split':split,
                        'source_seed':row['seed'],'source_game':row['game'],'seat':row['seat'],
                        'source_outcome':row['score'],'opponent_spec':json.loads(spec),'state':s,
                        'original_action':d['action'],'public_features':public_features(s),'public_history':list(history),'source_path':str(path)})
        if len(selected)>=36:break
    out=RUN/'mined';out.mkdir(parents=True,exist_ok=True)
    for row in selected:(out/(row['case']+'.json')).write_text(json.dumps(row,indent=2)+'\n')
    summary={'read_games':read_games,'missing_historical_traces':missing,'context_hit_games':{k:len(v) for k,v in hits.items()},
             'selected':len(selected),'buckets':{str(k):v for k,v in counts.items()},
             'grouping':'SHA256(source seed) mod 5; both seats, all opponents and adjacent states stay in the same split. One case per kind/source seed.',
             'scope':'Original-deck local proxy games. Historical results are audit labels only.'}
    (out/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
