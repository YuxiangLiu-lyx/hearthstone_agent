"""Preregistered Astra sampling; source blocks replace old modulo splits."""
import argparse
from collections import Counter, defaultdict
import json
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.study import ROOT, RUN, HERE
from development.secret_hunter_astra_sprint.tactical import setup, propose, digest
from development.secret_hunter_astra_sprint.cfqueue import reserve

ROUTES = {
    'coin': ('coin_bow', 'coin_minion', 'hold_coin'),
    'clear': ('clear_key', 'bow_clear', 'kill_juggler', 'kill_wolf', 'kill_amani', 'hounds_trade'),
    'develop': ('develop', 'preserve_burn'),
    'secret': ('develop_then_trap', 'trap'),
    'face': ('burn_face', 'face'),
    'power': ('power',),
}

def action_key(action):
    # A placement-only change is not a new tactical category in this deck.
    # Keep the original position in the actual engine action and replay.
    return json.dumps({k:v for k,v in action.items() if k!='position'},sort_keys=True)

def mine(batch, split, stage='initial'):
    setup('DARCL2')
    from development.secret_hunter_final.early_routes import features
    from action_validator import legal
    db = ledger.connect(RUN)
    m = ledger.meta(db, 'manifest')
    assert not ledger.meta(db, 'selection_opened', False)
    bounds = m['seed_blocks']['development' if split == 'train' else 'label_holdout']
    batchrow = db.execute('select * from batches where id=?', (batch,)).fetchone()
    assert batchrow['status'] == 'done'
    assert json.loads(batchrow['arms']) == ['DARCL2']
    rows = [json.loads(r[0]) for r in db.execute(
        "select result from tasks where batch=? and candidate='DARCL2' order by seed,opponent,seat", (batch,))]
    assert all(bounds[0] <= r['seed'] <= bounds[1] for r in rows)
    specs = {o['name']:o for o in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    quota = {'astra-board-proxy':60, 'astra-sticky-proxy':60, 'astra-tempo-proxy':24}
    if split == 'validation': quota = {k:int(v*2/3) for k,v in quota.items()}
    minimum_mana=2;route_groups=ROUTES;old_roots={};rescued=set()
    if stage=='late1':
        minimum_mana=3;route_groups=dict(ROUTES)
        route_groups['clear']=('clear_key','bow_amani',*ROUTES['clear'][1:])
        if split=='train':
            quota={'astra-board-proxy':50,'astra-sticky-proxy':50,'astra-tempo-proxy':20}
            labels=json.loads((RUN/'labels-train-worlds-01.json').read_text())
            rescued={r['case'] for r in labels['pairs'] if r['world']==0 and r['delta']>0}
            for p in (RUN/'tactical-sources').glob('sprint-*.json'):
                old=json.loads(p.read_text())
                if old['split']=='train':old_roots[old['opponent_spec']['name'],old['seed'],old['seat']]=old
    candidates=[]; coverage=defaultdict(Counter); catalogue=[]
    for r in rows:
        name=r['opponent']; count=coverage[name]
        count['all_games']+=1; count['wins' if r['score'] else 'losses']+=1
        assert not r.get('harness_error') and not r.get('course_failure')
        previous=old_roots.get((name,r['seed'],r['seat']))
        if previous and not r['score'] and previous['case'] in rescued:
            count['excluded_already_rescued_original_loss']+=1;continue
        earliest_mana=max(minimum_mana,previous['features']['mana']+1 if previous else minimum_mana)
        folder=RUN/'batches'/batch/'DARCL2'/'games'/r['game']
        logs=[json.loads(line) for line in (folder/f"p{r['seat']}/observations.jsonl").read_text().splitlines()]
        earliest=None; ever=set()
        for z in logs:
            s=z['state']
            if s['phase']!='main' or not earliest_mana<=s['you']['max_mana']<=5:continue
            if z['info'].get('reason')=='guaranteed_lethal':continue
            choices=[]; actions=set()
            for category,routes in route_groups.items():
                for route in routes:
                    action=propose(s,route,{},z['action'])
                    if action is None or action_key(action)==action_key(z['action']) or not legal(s,action):continue
                    ever.add(route)
                    key=action_key(action)
                    if key not in actions:
                        choices.append((category,route,action));actions.add(key)
                        break
            if choices and earliest is None:
                # Keep at most five categories. Rotate the excluded category
                # using source seed, without consulting any continuation label.
                if len(choices)>5:
                    drop=r['seed']%len(choices);choices=choices[:drop]+choices[drop+1:]
                earliest=(z,choices)
        for route in ever:count['ever_eligible_'+route]+=1
        catalogue.append({'seed':r['seed'],'opponent':name,'seat':r['seat'],
                          'actual_first':r['first_player']==r['seat'],'score':r['score'],
                          'eligible_routes':sorted(ever),'root_seq':earliest[0]['state']['seq'] if earliest else None})
        if earliest is None:continue
        count['eligible_games']+=1
        if name not in quota:continue
        z,choices=earliest;s=z['state']
        prefix='sprint' if stage=='initial' else stage
        case=f"{prefix}-DARCL2-{r['seed']}-{name}-s{r['seat']}-q{s['seq']}"
        opening=[{'seq':v['state']['seq'],'phase':v['state']['phase'],
                  'action':v['action'],'hand':[c['card_id'] for c in v['state'].get('you',{}).get('hand',[])]}
                 for v in logs if v['state']['seq']<s['seq'] and v['state']['phase'] in ('mulligan','main')]
        candidates.append({'case':case,'arm':'DARCL2','seed':r['seed'],'seat':r['seat'],'seq':s['seq'],
            'actual_first':r['first_player']==r['seat'],'source_score':r['score'],
            'state':s,'state_digest':digest(s),'opponent_spec':specs[name],
            'game_path':str(folder.relative_to(ROOT)),'features':features(s),'split':split,
            'routes':['baseline']+[v[1] for v in choices],
            'route_categories':{v[1]:v[0] for v in choices},'original_action':z['action'],
            'original_info':z['info'],'opening_actions':opening})
    chosen=[];used_seeds=Counter()
    for name,n in quota.items():
        remaining=[c for c in candidates if c['opponent_spec']['name']==name]
        targets={(score,first):n//3 if score==0 else n//6 for score in (0,1) for first in (False,True)}
        # Fill underrepresented outcome/order cells first; repeat the source
        # seed with the fewest already selected roots. Rare cells may be empty.
        taken=Counter()
        while remaining and sum(taken.values())<n:
            def priority(c):
                cell=(c['source_score'],c['actual_first'])
                return (taken[cell]>=targets[cell],taken[cell]/max(1,targets[cell]),
                        used_seeds[c['seed']],c['seed'],c['seat'])
            c=min(remaining,key=priority);remaining.remove(c);chosen.append(c)
            taken[c['source_score'],c['actual_first']]+=1;used_seeds[c['seed']]+=1
    jobs=[]
    for c in chosen:
        path=RUN/'tactical-sources'/(c['case']+'.json')
        if path.exists():assert json.loads(path.read_text())==c
        else:ledger.atomic(path,c)
        for world in range(3):
            for route in c['routes']:
                jobs.append((f"{c['case']}-w{world}-{route}",
                    {'case':c['case'],'sample':world,'route':route,'arm':'DARCL2'}))
    manifest={'batch':batch,'split':split,'roots':len(chosen),'jobs':len(jobs),
        'source_groups':len(used_seeds),'cases':[c['case'] for c in chosen],
        'coverage':dict(coverage),'catalogue':catalogue,
        'strata':dict(Counter(f"{c['opponent_spec']['name']}:{c['source_score']}:{c['actual_first']}" for c in chosen)),
        'label_access':'train worlds 0/1 only before hypothesis lock; world 2 and validation source labels held out',
        'worlds':'0 original; 1/2 shuffle both remaining decks and future RNG, hidden hands fixed'}
    if stage!='initial':manifest.update(stage=stage,minimum_mana=minimum_mana,source_batch=batch,
        earlier_rescued_losses_excluded=split=='train',
        source_status='Seen development seeds; do not claim a new source holdout' if split=='train' else 'Independent registered label-holdout source block')
    suffix='' if stage=='initial' else '-'+stage
    target=RUN/'tactical-sources'/f'manifest-{batch}{suffix}-DARCL2.json'
    if target.exists():assert json.loads(target.read_text())==manifest
    else:ledger.atomic(target,manifest)
    reserve('tactical',jobs)
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('cases','catalogue')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True)
    p.add_argument('--split',choices=['train','validation'],required=True)
    p.add_argument('--stage',choices=['initial','late1'],default='initial')
    a=p.parse_args();mine(a.batch,a.split,a.stage)
