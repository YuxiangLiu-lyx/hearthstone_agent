"""Screen only starting hands, never outcomes; retain both seats for every hit."""
import json
import sys
from development.secret_hunter_final.study import HERE,RUN,ROOT
from development.secret_hunter_mcgs import train
from development.secret_hunter_mcgs.mcgs_init import initialize
from hs_arena.engine import Engine
from hs_arena.deck import load_deck

def main():
    initialize();out=[]
    for pool,start,seeds in [('core',41310000,240),('guardrail',41311000,120)]:
        pop=json.loads((ROOT/f'development/teacher_eval/{pool}.json').read_text())
        selected=[];records=[]
        for spec in pop:
            other=load_deck(ROOT/spec['deck'])
            if str(other.hero_class)!='WARLOCK':continue
            own=load_deck(HERE/'candidates/B/deck.json')
            for seed in range(start,start+seeds):
                pair=[]
                for seat in (1,2):
                    e=Engine(own,other,seed) if seat==1 else Engine(other,own,seed)
                    s=e.view(seat);hand=s['you']['hand']
                    hit=any(c['card_id']=='EX1_610' for c in hand) and not any(c['type']=='MINION' and c['cost']<=2 for c in hand)
                    pair.append({'key':[spec['name'],seed,seat],'hit':hit,'first':e.first_player==seat,
                                 'hand':[c['card_id'] for c in hand]})
                records.extend(pair)
                if any(r['hit'] for r in pair):selected.extend(r['key'] for r in pair)
        train.atomic(RUN/f'conditional-{pool}.json',selected)
        report={'pool':pool,'start':start,'seeds':seeds,'sampled_hands':len(records),
                'hit_hands':sum(r['hit'] for r in records),'selected_games_per_arm':len(selected),'records':records,
                'selection':'Opening only; if either seat hits, run both seats for that opponent/seed.'}
        train.atomic(RUN/f'conditional-{pool}-sampling.json',report)
        out.append({k:v for k,v in report.items() if k!='records'})
    print(json.dumps(out))

if __name__=='__main__':main()
