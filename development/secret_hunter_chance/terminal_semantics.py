"""Separate terminal payoff equivalence from raw post-game board representation."""
import json,sys
from development.secret_hunter_program.common import ROOT,write
D=ROOT/'docs/secret_hunter_chance';sys.path.insert(0,str(ROOT/'development/secret_hunter_chance/candidates/C2/scripts'))
rows=json.loads((D/'terminal-checks-v2.json').read_text())['cases']
checks=[]
for r in rows:
 p,a=r['predicted'],r['actual']
 if r['terminal']:
  assert p['opponent']['hp']<=0 and a['opponent']['hp']<=0 and p['you']['hp']>0 and a['you']['hp']>0
  residual=[x for x in a['opponent']['board'] if x[2]<=0]
  normalized={**a,'opponent':{**a['opponent'],'board':[x for x in a['opponent']['board'] if x[2]>0]}}
  assert p==normalized
  checks.append({'seed':r['seed'],'knives':r['knives'],'enemy_hp':r['enemy_hp'],'terminal_payoff_equal':True,'uncleared_corpses':len(residual)})
 else:assert r['equal']
write(D/'terminal-semantics.json',{'raw_exact_matches':sum(r['equal'] for r in rows),'n':len(rows),'nonterminal_exact':sum(not r['terminal'] and r['equal'] for r in rows),'terminal_payoff_equal':len(checks),'terminal_details':checks,'policy_changed':False,'reason':'Engine ends on hero death before cleaning some already dead minions. The projector cleans those bodies. Both score the same terminal win; no later real action is executed. Raw v2 differences remain archived. This does not claim complete terminal-trigger equivalence for every card.'})
print(json.dumps({k:v for k,v in json.loads((D/'terminal-semantics.json').read_text()).items() if k!='terminal_details'}))
