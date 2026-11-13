"""Count actual end-turn omissions, rather than treating every trap board as one."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
from development.secret_hunter_turn_plans.study import RUN


def main():
    old=Path('/Users/liuyuxiang/.codex/worktrees/hearthstone-mcgs-20261112/runs/krush-mcgs')
    db=sqlite3.connect(f'file:{old}/ledger.sqlite?mode=ro',uri=True)
    counts=Counter();games=set();cases=[];seen=set();buckets=Counter()
    for batch,raw,spec in db.execute("select batch,result,opponent from tasks where candidate='Y1' and status='done' and phase='development' and batch like 'gen-%' order by seed,seat"):
        row=json.loads(raw)
        if row.get('harness_error') or not row.get('game'):continue
        path=old/'batches'/batch/'Y1'/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl'
        if not path.exists():continue
        counts['games_read']+=1;history=[]
        for line in path.read_text().splitlines():
            d=json.loads(line);s=d['state'];history.extend(s.get('events',[]))
            if s['phase']!='main' or d['action'].get('type')!='end_turn':continue
            counts['end_turns']+=1
            available=[c for c in s['you']['hand'] if c['type']=='MINION' and c['cost']<=s['you']['mana']]
            if not available or len(s['you']['board'])>=7:continue
            counts['end_with_affordable_minion']+=1
            if not any(c['card_id']=='EX1_080' for c in available):continue
            counts['end_with_keeper']+=1;games.add(row['game'])
            trap=any(c['card_id']=='EX1_610' for c in s['you'].get('secrets',[]))
            death=any(m.get('deathrattle') for m in s['opponent']['board'])
            counts['keeper_with_active_trap']+=int(trap);counts['keeper_with_deathrattle']+=int(death)
            split='train' if int(hashlib.sha256(str(row['seed']).encode()).hexdigest()[:8],16)%5<3 else 'validation'
            if row['seed'] in seen or buckets[(split,row['score'])]>=4:continue
            seen.add(row['seed']);buckets[(split,row['score'])]+=1
            cases.append({'case':f'completion-{len(cases):03d}','kind':'trap','split':split,
                          'source_seed':row['seed'],'source_game':row['game'],'seat':row['seat'],
                          'source_outcome':row['score'],'opponent_spec':json.loads(spec),'state':s,
                          'original_action':d['action'],'public_history':list(history),
                          'public_features':{},'source_path':str(path),'active_trap':trap,'enemy_deathrattle':death})
    dest=RUN/'mined-completion';dest.mkdir(exist_ok=True)
    for r in cases:(dest/(r['case']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
    summary={'counts':dict(counts),'games_with_keeper_omission':len(games),'cases':len(cases),
             'buckets':{str(k):v for k,v in buckets.items()},
             'limitation':'An affordable minion at end-turn is an opportunity, not proof that playing it is better.'}
    (dest/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
