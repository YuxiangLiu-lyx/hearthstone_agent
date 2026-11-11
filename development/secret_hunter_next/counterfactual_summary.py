"""Paired within-state sample uncertainty, never pooled as recovered matches."""
import random,statistics,json
from development.secret_hunter_program.common import ROOT,readlines,write
D=ROOT/'docs/secret_hunter_next';rows=readlines(D/'counterfactual-v2.jsonl');out=[]
for case in sorted(rows,key=lambda c:c['game']):
 original=next((a for a in case['alternatives'] if a['action']==case['original_action']),None)
 comparisons=[]
 if original:
  for other in case['alternatives']:
   delta=[b['win']-a['win'] for a,b in zip(original['outcomes'],other['outcomes'])]
   rng=random.Random(771);samples=sorted(statistics.mean(rng.choices(delta,k=len(delta))) for _ in range(10000))
   comparisons.append({'action':other['action'],'win_rate':other['win_rate'],'gain_vs_original':statistics.mean(delta),'sample_bootstrap_95':[samples[250],samples[9749]],'random_samples':len(delta)})
 out.append({'game':case['game'],'seq':case['seq'],'turn':case['turn'],'opponent':case['source_opponent'],'split':case['split'],'original_modelled':original is not None,'original_action':case['original_action'],'comparisons':comparisons,'causal_status':'Six conditional future samples only; source loss recovery is not established. Best-alternative selection is adaptive.'})
write(D/'counterfactual-summary.json',{'cases':out,'source_cases':24,'terminal_rollouts':432,'uncertainty':'Within-state resampling is descriptive with only six random samples and fixed existing private hands; it is not a generalization CI or a posterior over hidden decks.','confirmed_repaired_original_losses':0})
print('Summarized',len(out),'cases')
