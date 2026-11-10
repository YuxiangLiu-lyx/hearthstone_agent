"""Reproducible small deck neighborhood, evaluated in actual engine games.

This writes candidates and screening results; it NEVER promotes them automatically.
Use independent validation after selecting a candidate, not the screening seeds again.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from hs_arena.cards import load
from hs_arena.deck import validate_deck_data

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',default='submission/hearthstone-agent')
    p.add_argument('--out',default='development/experiments/local-search');p.add_argument('--seeds',type=int,default=8)
    p.add_argument('--start',type=int,default=4000);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args();root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    byname={c['name']:c['id'] for c in load().values()}
    mutations={
        'baseline':[],
        'tirion-cairne':[("Guardian of Kings","Tirion Fordring"),("Guardian of Kings","Cairne Bloodhoof")],
        'early-zoo':[("Guardian of Kings","Knife Juggler"),("Guardian of Kings","Knife Juggler")],
        'more-draw':[("Silver Hand Knight","Gnomish Inventor"),("Silver Hand Knight","Gnomish Inventor")],
        'more-burst':[("Sen'jin Shieldmasta","Blessing of Might"),("Sen'jin Shieldmasta","Blessing of Might")],
    }
    summary=[]
    for name,swaps in mutations.items():
        candidate=root/'candidates'/name
        shutil.copytree(args.source,candidate,ignore=shutil.ignore_patterns('__pycache__'))
        deck=json.loads((candidate/'deck.json').read_text())
        for old,new in swaps:
            deck['cards'].remove(byname[old]);deck['cards'].append(byname[new])
        assert not validate_deck_data(deck)
        (candidate/'deck.json').write_text(json.dumps(deck,indent=2))
        out=root/name
        command=[sys.executable,'-m','development.benchmarks.run','--candidate',str(candidate),
                 '--population','development/opponents/expanded.json','--out',str(out),'--start',str(args.start),
                 '--seeds',str(args.seeds),'--workers',str(args.workers)]
        with open(root/f'{name}.log','w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
        data=json.loads((out/'summary.json').read_text());summary.append({'name':name,'swaps':swaps,'summary':data})
        print(name,data['wins'],data['games'],flush=True)
    (root/'screening.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':main()
