"""Finite, preregistered Zoo deck screen. Original policies and decks are immutable."""
import json,shutil,subprocess,sys
from pathlib import Path
from hs_arena.cards import load
from hs_arena.deck import validate_deck_data
ROOT=Path('development/experiments/zoo-v7-screen')
SOURCE=Path('development/candidates/v6-zoo-guide')
MUTATIONS={
 'baseline':[],
 'giants':[('Mortal Coil','Sea Giant')]*2,
 'giants-yeti':[('Mortal Coil','Sea Giant')]*2+[('Abusive Sergeant','Chillwind Yeti')]*2,
 'giants-guard':[('Mortal Coil','Sea Giant')]*2+[('Abusive Sergeant',"Sen'jin Shieldmasta")]*2,
 'resilient':[('Mortal Coil','Cairne Bloodhoof'),('Mortal Coil','Silver Hand Knight')]+[('Abusive Sergeant','Chillwind Yeti')]*2,
 'draw':[('Mortal Coil','Gnomish Inventor')]*2+[('Abusive Sergeant','Chillwind Yeti')]*2,
 'midrange':[('Mortal Coil',"Sen'jin Shieldmasta")]*2+[('Abusive Sergeant','Chillwind Yeti')]*2,
 'tokens':[('Mortal Coil','Imp Master')]*2+[('Abusive Sergeant','Sea Giant')]*2,
}

def main():
 ROOT.mkdir(parents=True,exist_ok=False)
 byname={c['name']:c['id'] for c in load().values()}
 population=json.loads(Path('development/opponents/expanded.json').read_text())+json.loads(Path('development/opponents/holdout3.json').read_text())
 Path('development/opponents/zoo-research.json').write_text(json.dumps(population,indent=2)+'\n')
 plan={'source':str(SOURCE),'mutations':MUTATIONS,'screen_seeds':[7000,7007],
       'validation_seeds':[7100,7123],'reserved_holdout_seeds':[100400,100439],
       'population':'development/opponents/zoo-research.json',
       'selection':'screen deck alternatives, validate finalists and policy ablations; freeze one challenger before holdout',
       'holdout_comparison':'v6 baseline versus frozen final challenger; no extra sampling based on significance'}
 (ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 summaries=[]
 for name,swaps in MUTATIONS.items():
  candidate=ROOT/'candidates'/name
  shutil.copytree(SOURCE,candidate,ignore=shutil.ignore_patterns('__pycache__'))
  deck=json.loads((candidate/'deck.json').read_text())
  for old,new in swaps:deck['cards'].remove(byname[old]);deck['cards'].append(byname[new])
  assert not validate_deck_data(deck)
  (candidate/'deck.json').write_text(json.dumps(deck,indent=2)+'\n')
  cmd=[sys.executable,'-m','development.benchmarks.run','--candidate',str(candidate),'--population',plan['population'],
       '--out',str(ROOT/name),'--start','7000','--seeds','8','--workers','4','--split','train']
  with (ROOT/f'{name}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  s=json.loads((ROOT/name/'summary.json').read_text());summaries.append({'name':name,'swaps':swaps,'summary':s})
  print(name,s['wins'],s['games'],flush=True)
  (ROOT/'screening.json').write_text(json.dumps(summaries,indent=2)+'\n')
if __name__=='__main__':main()
