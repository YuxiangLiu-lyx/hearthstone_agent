"""Offline sparse logistic ablations with seed-grouped fit/calibration/test sets.

These fitted coefficients are research artifacts and must never enter a skill ZIP.
Response categories are independent Bernoulli events, not exclusive hidden hands.
"""
import collections,gzip,hashlib,json,math,random,time
from pathlib import Path
from hs_arena.cards import load
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.data import LABELS,BUFF
D=ROOT/'docs/secret_hunter_response'; C=load()
def sigmoid(z):return 1/(1+math.exp(-max(-30,min(30,z))))
def card_tags(cid):
 c=C[cid];text=c.get('text','').lower();damage='damage' in text
 return [float(c['type']=='MINION' or cid in {'EX1_538','CS2_027','CS2_022'}),float(cid in BUFF),float('TAUNT' in c.get('mechanics',[]) or cid in {'EX1_093','EX1_058','DS1_070'}),float((damage or 'destroy' in text) and c['type']=='SPELL'),float(damage and c['type']=='SPELL' and ('hero' in text or 'minion' not in text)),0.]
def prior(f,bigram):
 viable={cid for cid,c in C.items() if c['card_class'] in ('NEUTRAL',f['hero_class']) and c['cost']<=f['mana'] and c['type'] in ('MINION','SPELL','WEAPON')}
 totals=collections.Counter()
 for shown in f['shown_cards']:
  for cid,n in bigram.get(shown,{}).items():
   if cid in viable:totals[cid]+=n
 denom=sum(totals.values())
 return [sum(n*card_tags(cid)[k] for cid,n in totals.items())/denom if denom else 0 for k in range(len(LABELS))]
def features(f,mode,bigram):
 cls=f['hero_class'];mana=min(10,f['mana']);x={'bias':1.,'class:'+cls:1.,'class_mana:'+cls+':'+str(mana):1.}
 if mode in ('state','history','history_bigram'):
  x.update({'hand':f['hand_size']/10,'own_hand':f['own_hand_size']/10,'own_hp':f['own_health']/30,'enemy_hp':f['enemy_health']/30,'own_weapon':f['own_weapon']/5,'enemy_weapon':f['enemy_weapon']/5,'secrets':len(f['own_secrets'])/3})
  for side in ('own','enemy'):
   b=f[side+'_board'];x.update({side+'_count':len(b)/7,side+'_attack':sum(m['attack'] for m in b)/20,side+'_health':sum(m['health'] for m in b)/25,side+'_fragile':sum(m['health']<=2 for m in b)/7,side+'_taunts':sum(bool(m['taunt']) for m in b)/7})
   for m in b:x['board:'+side+':'+m['card_id']]=1
  x['mana_hand']=mana*f['hand_size']/50
 if mode in ('history','history_bigram'):
  x.update({'cheap_history':min(10,f['cheap_minions_played'])/10,'face_history':min(12,f['face_attacks'])/12,'trade_history':min(12,f['other_attacks'])/12})
  for cid in f['shown_cards']:x['shown:'+cid]=1.
 if mode in ('bigram','history_bigram'):
  for k,v in zip(LABELS,prior(f,bigram)):x['prior:'+k]=v
 return x

def fit(data,mode,bigram):
 records=[(features(r['features'],mode,bigram),[r['labels'][k] for k in LABELS]) for r in data];weights=[collections.defaultdict(float) for _ in LABELS];rng=random.Random(117)
 for epoch in range(35):
  rng.shuffle(records);eta=.04/(1+epoch*.07)
  for x,ys in records:
   for w,y in zip(weights,ys):
    err=sigmoid(sum(w[k]*v for k,v in x.items()))-y
    for k,v in x.items():w[k]-=eta*(err*v+.001*w[k])
 return [dict(w) for w in weights]
def predict(w,r,mode,bigram,t=1):
 x=features(r['features'],mode,bigram)
 return [sigmoid(sum(a.get(k,0)*v for k,v in x.items())/t) for a in w]
def metrics(rs,ps):
 result={}
 for i,k in enumerate(LABELS):
  n=len(rs);ys=[r['labels'][k] for r in rs];p=[z[i] for z in ps];bins=[]
  for b in range(5):
   indices=[j for j,q in enumerate(p) if min(4,int(q*5))==b]
   if indices:bins.append({'n':len(indices),'predicted':sum(p[j] for j in indices)/len(indices),'observed':sum(ys[j] for j in indices)/len(indices)})
  result[k]={'n':n,'positives':sum(ys),'brier':sum((a-b)**2 for a,b in zip(p,ys))/n,'log_loss':-sum(y*math.log(max(1e-9,q))+(1-y)*math.log(max(1e-9,1-q)) for q,y in zip(p,ys))/n,'ece5':sum(b['n']*abs(b['predicted']-b['observed']) for b in bins)/n,'bins':bins}
 return {'n':len(rs),'macro_brier':sum(v['brier'] for v in result.values())/len(LABELS),'macro_ece5':sum(v['ece5'] for v in result.values())/len(LABELS),'labels':result}
def main():
 from development.secret_hunter_response.accounting import reserve,finish
 reserve('calibration',short=0,seconds=600)
 p=Path('/tmp/hunter-response-sources/predator/Bigramms/bigramm_3-2018-10-2017.json.gz');j=json.load(gzip.open(p));b={cid:{r['cardId']:r['numOcc'] for r in values if r['cardId'] in C} for entry in j['bigramMap'] for cid,values in entry.items() if cid in C}
 write(D/'bigram-filtered-offline.json',b)
 rows=readlines(D/'opponent_replies.jsonl');tr=[r for r in rows if r['audit']['seed']%5 in (2,3,4)];cal=[r for r in rows if r['audit']['seed']%5==1];test=[r for r in rows if r['audit']['seed']%5==0]
 assert not ({r['audit']['seed'] for r in tr}&{r['audit']['seed'] for r in cal+test})
 results={};models={}
 for mode in ('baseline','state','history','bigram','history_bigram'):
  w=fit(tr,mode,b);temperature=min((.75,1.,1.25,1.5,2.),key=lambda t:metrics(cal,[predict(w,r,mode,b,t) for r in cal])['macro_brier'])
  ps=[predict(w,r,mode,b,temperature) for r in test];results[mode]={'temperature_from_calibration':temperature,'test':metrics(test,ps),'by_proxy':{name:metrics([r for r in test if r['audit']['opponent']==name],[z for r,z in zip(test,ps) if r['audit']['opponent']==name]) for name in sorted({r['audit']['opponent'] for r in test})},'early_turns':metrics([r for r in test if 2<=r['audit']['own_turn']<=4],[z for r,z in zip(test,ps) if 2<=r['audit']['own_turn']<=4])}
  models[mode]={'weights':w,'temperature':temperature};print(mode,results[mode]['test']['macro_brier'],results[mode]['test']['macro_ece5'],flush=True)
 transfer={}
 for name in sorted({r['audit']['opponent'] for r in test}):
  subset=[r for r in test if r['audit']['opponent']==name];transfer[name]={}
  for mode in ('baseline','history'):
   w=fit([r for r in tr if r['audit']['opponent']!=name],mode,b)
   transfer[name][mode]=metrics(subset,[predict(w,r,mode,b) for r in subset])
 audit={'source_fields':list(j),'source_card_ids':len(j['cardIds']),'course_card_ids':len(C),'intersection':len(set(j['cardIds'])&C.keys()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'class_allowed':{cls:sum(c['card_class'] in (cls,'NEUTRAL') and cid in j['cardIds'] for cid,c in C.items()) for cls in ('WARLOCK','HUNTER','MAGE')},'meaning':'Card co-occurrence counts; neither hand membership nor next-turn probabilities. Filter course pool, class and mana before each feature calculation.'}
 write(D/'calibration.json',{'fit_n':len(tr),'calibration_n':len(cal),'test_n':len(test),'fit_seeds':sorted({r['audit']['seed'] for r in tr}),'calibration_seeds':sorted({r['audit']['seed'] for r in cal}),'test_seeds':sorted({r['audit']['seed'] for r in test}),'results':results,'leave_one_proxy_out':transfer,'bigram_audit':audit,'limitations':['Labels mean publicly performed events, not hidden possession.','Co-occurring labels must not be normalized into mutually exclusive probabilities.','Only 8 seed groups in test; proxy generalization remains limited.','Learned coefficients and external counts are offline only.']})
 write(D/'models-offline-only.json',models);finish('calibration',test_rows=len(test));print(json.dumps(audit))
if __name__=='__main__':main()
