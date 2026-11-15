"""Source-grouped paired residual ridge for the locked H2 ranking mechanism."""
import collections,hashlib,json,math,time
from pathlib import Path
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.study import RUN,HERE
from development.secret_hunter_astra_sprint.tactical import setup
from development.secret_hunter_program.common import sha

def solve(a,b):
    n=len(b);a=[list(row)+[b[i]] for i,row in enumerate(a)]
    for j in range(n):
        p=max(range(j,n),key=lambda i:abs(a[i][j]));a[j],a[p]=a[p],a[j]
        assert abs(a[j][j])>1e-12
        scale=a[j][j];a[j]=[v/scale for v in a[j]]
        for i in range(n):
            if i==j:continue
            scale=a[i][j]
            a[i]=[v-scale*w for v,w in zip(a[i],a[j])]
    return [row[-1] for row in a]

def fit(rows,alpha):
    n=len(rows[0]['x']);a=[[alpha*int(i==j) for j in range(n)] for i in range(n)];b=[0.]*n
    groups=collections.Counter(r['seed'] for r in rows)
    # Total weight one per source seed. Seats, opponents, roots and worlds remain clustered.
    for r in rows:
        w=1/groups[r['seed']];target=10*r['delta']-r['prior_delta'];x=r['x']
        for i in range(n):
            b[i]+=w*x[i]*target
            for j in range(n):a[i][j]+=w*x[i]*x[j]
    return solve(a,b)

def adjustment(x,coef):return max(-4,min(4,sum(a*b for a,b in zip(x,coef))))

def evaluate(rows,coef):
    groups=collections.defaultdict(list)
    for r in rows:groups[r['case'],r['world']].append(r)
    result={'roots_worlds':len(groups),'learned_net':0,'prior_net':0,'changed_routes':0,'mse':0.}
    for rs in groups.values():
        base=rs[0]['base']; options=[(0,0,'baseline')];old=[(0,0,'baseline')]
        for r in rs:
            gain=r['prior_delta']+adjustment(r['alternative'],coef)-adjustment(base,coef)
            options.append((gain,r['delta'],r['route']));old.append((r['prior_delta'],r['delta'],r['route']))
            result['mse']+=(gain-10*r['delta'])**2
        best=max(options,key=lambda z:z[0]);prior=max(old,key=lambda z:z[0])
        result['learned_net']+=best[1];result['prior_net']+=prior[1];result['changed_routes']+=best[2]!=prior[2]
    result['mse']/=max(1,len(rows));return result

def before_handoff(label):
    steps=label['sequence'];ends=[r for r in steps if r['action']['type']=='end_turn']
    if ends:return ends[-1]['state']
    return steps[-1]['next_visible'] if steps else None

def dataset():
    setup('DARCL2')
    from race_plan import value
    from public_response import worst_reply
    from tactical_model import prepare
    from development.secret_hunter_astra_sprint.rank_features import vector,eligible
    cfg=json.loads((HERE/'candidates/DARCL2/config.json').read_text());cache={};rows=[];skips=collections.Counter()
    for name in ('labels-train-worlds-01.json','labels-manifest-diagnostic-dev-late1-DARCL2-train-worlds-01.json'):
        evidence=json.loads((RUN/name).read_text());assert evidence['split']=='train' and evidence['worlds']==[0,1]
        for r in evidence['pairs']:
            def endpoint(route):
                key=(r['case'],r['world'],route)
                if key in cache:return cache[key]
                p=RUN/'tactical-labels'/f"{r['case']}-w{r['world']}-{route}.json";label=json.loads(p.read_text());s=before_handoff(label)
                if not s or not eligible(s) or min(s['you']['hero']['health'],s['opponent']['hero']['health'])<=0:
                    cache[key]=None;return None
                initial=prepare({**s,'planning_mode':'response'})
                reply=worst_reply(initial,cfg,time.monotonic()+2,cfg.get('reply_nodes',48))
                if not reply['supported'] or reply['visible_lethal_found']:
                    cache[key]=None;return None
                prior=.15*value(initial,cfg)+.85*reply['value']
                cache[key]=(vector(initial,reply['state']),prior);return cache[key]
            base=endpoint('baseline');alt=endpoint(r['route'])
            if not base or not alt:skips['unsupported_or_terminal']+=1;continue
            if abs(alt[1]-base[1])>50:skips['large_safety_score']+=1;continue
            x=[a-b for a,b in zip(alt[0],base[0])]
            rows.append({k:r[k] for k in ('case','seed','world','route','delta')}|{'x':x,'base':base[0],'alternative':alt[0],'prior_delta':alt[1]-base[1]})
    return rows,dict(skips)

def main():
    plan={'created':time.time(),'hypothesis':'H2: Existing T2-T5 public-response candidates miss longer-term hand/board tradeoffs. A small source-grouped paired residual ranker applied only after the unchanged six bounded visible replies can rank rescued routes higher without increasing search nodes. Parent DARCL2, deck/mulligan fixed; Warlock public class only, T2-T5 only. Refute by nonpositive independent source continuation or fresh full-game net gain.',
      'features_sha256':sha(HERE/'rank_features.py'),'trainer_sha256':sha(Path(__file__)),
      'data':['labels-train-worlds-01.json','labels-manifest-diagnostic-dev-late1-DARCL2-train-worlds-01.json'],
      'worlds':[0,1],'holdout':'late1 world2 and independent diagnostic-holdout2 source labels unopened',
      'model':'24 fixed public features; ridge residual target 10*(paired terminal win delta) - old visible-reply value delta; per-source weight one; correction clipped +/-4 per endpoint',
      'cv':'Five folds by (source_seed-62150000)%5, all roots/seats/opponents/worlds grouped; alpha chosen by out-of-fold rescued-minus-regressed roots/worlds, then MSE, then stronger regularization',
      'alphas':[.1,.3,1,3,10,30],
      'deployment':'Only add correction to final complete visible-reply endpoint score; generation/beam/reply search/chance search unchanged. Exact lethal penalty preserved. No opponent IDs or hidden values.',
      'fresh_full_test':{'batch':'round2-ranker','start':62150200,'seeds':40,'arms':['DARCL2','PRR'],'workers':6}}
    destination=RUN/'hypotheses/H2-plan.json'
    if destination.exists():
        old=json.loads(destination.read_text());assert old['hypothesis']==plan['hypothesis'] and old['alphas']==plan['alphas']
        ledger.atomic(RUN/'hypotheses/H2-implementation-fix.json',{'created':time.time(),'old_trainer_sha256':old['trainer_sha256'],'new_trainer_sha256':plan['trainer_sha256'],'reason':'Initial fit aborted before producing labels: baseline config omits reply_nodes and uses code default 48; match that default. No feature, objective, split or hyperparameter change.'})
    else:ledger.atomic(destination,plan)
    rows,skips=dataset();ledger.atomic(RUN/'H2-training-pairs.json',{'rows':rows,'skips':skips})
    scores=[]
    for alpha in plan['alphas']:
        folds=[]
        for fold in range(5):
            train=[r for r in rows if (r['seed']-62150000)%5!=fold];test=[r for r in rows if (r['seed']-62150000)%5==fold]
            folds.append(evaluate(test,fit(train,alpha)))
        scores.append({'alpha':alpha,'folds':folds,'net':sum(f['learned_net'] for f in folds),'prior_net':sum(f['prior_net'] for f in folds),'mse':sum(f['mse'] for f in folds)/5})
    chosen=max(scores,key=lambda x:(x['net'],-x['mse'],x['alpha']));coef=fit(rows,chosen['alpha'])
    from development.secret_hunter_astra_sprint.rank_features import NAMES
    result={'created':time.time(),'plan_sha256':sha(destination),'training_pairs':len(rows),'source_seeds':len({r['seed'] for r in rows}),'skips':skips,'cv':scores,'chosen_alpha':chosen['alpha'],'names':NAMES,'coef':coef,'clip':4,'in_sample':evaluate(rows,coef)}
    ledger.atomic(RUN/'H2-fitted-ranker.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
