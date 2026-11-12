"""Archive compact engine action prefixes so counterfactual cases survive log cleanup."""
import gzip,json
from development.secret_hunter_program.common import ROOT,readlines,write
from hs_arena.engine import Engine
from hs_arena.deck import load_deck
D=ROOT/'docs/secret_hunter_response';cases=json.loads((D/'counterfactual-pilot-selection.json').read_text())+json.loads((D/'counterfactual-balanced-selection.json').read_text());seen=set();records=[]
for c in cases:
 r=c['row'];key=(r['game'],c['observation']['seq'])
 if key in seen:continue
 seen.add(key);src=ROOT/c['source'];seat=r['seat'];spec=next(o for o in json.loads((src/'config.json').read_text())['population'] if o['name']==r['opponent'])
 own=load_deck(ROOT/'development/secret_hunter_response/candidates/Y1/deck.json');other=load_deck(ROOT/spec['deck']);e=Engine(own if seat==1 else other,other if seat==1 else own,r['seed'],max_turns=180)
 obs={i:readlines(src/'games'/r['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};prefix=[]
 while True:
  p,_=e.pending();z=obs[p][idx[p]]
  if p==seat and z['state']['seq']==key[1]:break
  prefix.append({'player':p,'action':z['action']});assert e.step(p,z['action']).accepted;idx[p]+=1
 records.append({'game':r['game'],'seq':key[1],'actions':prefix})
with gzip.GzipFile(filename=str(D/'replay-prefixes.jsonl.gz'),mode='wb',mtime=0) as f:
 for r in records:f.write((json.dumps(r,separators=(',',':'))+'\n').encode())
print('Archived',len(records),'public-action prefixes')
