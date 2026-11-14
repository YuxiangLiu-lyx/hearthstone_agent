"""Fresh early roots, verified original prefixes and paired terminal rollouts."""
import argparse
from collections import defaultdict,Counter
import hashlib
import json
import random
import sys
from development.secret_hunter_long.study import HERE,RUN,ROOT
from development.secret_hunter_long.cfqueue import reserve
from development.secret_hunter_mcgs import train

def setup(arm='B'):
    sys.path.insert(0,str(HERE/'candidates'/arm/'scripts'))
    from development.secret_hunter_mcgs.mcgs_init import initialize
    initialize()

def visible(s):return {k:s.get(k) for k in ('phase','turn','you','opponent','legal_actions')}
def digest(s):return hashlib.sha256(json.dumps(visible(s),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def propose(s,route,memory,baseline):
    from development.secret_hunter_final.early_routes import propose as old
    from action_validator import expand
    if route not in ('bow_clear','develop_then_trap'):return old(s,route,memory,baseline)
    if s.get('phase')!='main':return None
    y,o=s['you'],s['opponent'];hand={c['entity_id']:c for c in y['hand']};actions=expand(s,positions=True)
    if route=='develop_then_trap':
        plays=[a for a in actions if a['type']=='play_card' and hand[a['card']]['type']=='MINION' and 'target' not in a]
        if plays and not memory.get('developed'):
            a=max(plays,key=lambda a:(hand[a['card']].get('attack',0)+hand[a['card']].get('health',0),-hand[a['card']]['cost']))
            memory['developed']=True;return a
        return old(s,'trap',memory,baseline)
    victims={m['entity_id']:m for m in o['board']}
    attacks=[a for a in actions if a['type']=='attack' and a['attacker']==y['hero']['entity_id'] and a['target'] in victims
             and victims[a['target']]['attack']<y['hero']['health']+y['hero'].get('armor',0)]
    if attacks:
        return max(attacks,key=lambda a:(int(victims[a['target']]['health']<=y['hero']['attack'] and not victims[a['target']].get('divine_shield')),
             victims[a['target']]['card_id'] in ('NEW1_019','EX1_162','EX1_597'),victims[a['target']]['attack']))
    if not y.get('weapon'):
        return next((a for a in actions if a['type']=='play_card' and hand[a['card']]['card_id']=='EX1_536'),None)
    return None

def mine(batch,arm,cap,samples,balance_families=False):
    setup(arm)
    from development.secret_hunter_final.early_routes import features
    from action_validator import legal
    db=train.connect(RUN);rows=[json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done' order by seed,opponent,seat",(batch,arm))]
    pop={o['name']:o for o in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    routes=('coin_bow','coin_minion','bow_clear','kill_juggler','kill_wolf','hounds_trade','develop_then_trap','develop','hold_coin','trap','preserve_burn','face','power')
    candidates=[];coverage=Counter()
    for r in rows:
        if r.get('harness_error'):continue
        coverage['wins' if r['score'] else 'losses']+=1
        folder=RUN/'batches'/batch/arm/'games'/r['game'];logs=[json.loads(l) for l in (folder/f"p{r['seat']}"/'observations.jsonl').read_text().splitlines()]
        eligible=[]
        for z in logs:
            s=z['state']
            if s['phase']!='main':continue
            f=features(s)
            if not 1<=f['mana']<=5:continue
            if not ((f['coin'] and f['mana']<=3) or (f['incoming']>=3 and f['mana']>=2)):continue
            if z['info'].get('reason')=='guaranteed_lethal':continue
            available=[]
            for route in routes:
                a=propose(s,route,{},z['action'])
                if a is not None and a!=z['action'] and legal(s,a):available.append(route)
            if len(available)>=2:eligible.append((z,available))
        if not eligible:continue
        coverage['eligible_games']+=1
        # Earliest legitimate fork, not the visually worst late state.
        z,available=eligible[0];s=z['state'];cid=f't-{arm}-{r["seed"]}-{r["opponent"]}-s{r["seat"]}-q{s["seq"]}'
        candidates.append({'case':cid,'arm':arm,'seed':r['seed'],'seat':r['seat'],'seq':s['seq'],
            'actual_first':r['first_player']==r['seat'],
            'source_score':r['score'],'state':s,'state_digest':digest(s),'opponent_spec':pop[r['opponent']],
            'game_path':str(folder.relative_to(ROOT)),'features':features(s),
            'split':'validation' if r['seed']%5 in (0,1) else 'train','routes':['baseline']+available[:5],
            'original_action':z['action']})
    grouped=defaultdict(list)
    for c in candidates:grouped[c['seed']].append(c)
    # Each seed contributes roots before any seed contributes its next root.
    # Rotate opponent order, and interleave known wins and losses within seed.
    for seed,cs in grouped.items():
        mixed=[]
        if balance_families:
            # At six roots per seed this yields 3 Astra, 2 Bot2, 1 Bot1.
            # Within each family alternate wins/losses and rotate opponents and
            # seats. Source outcomes affect offline sampling only, never policy.
            queues={}
            for family in ('astra','bot2','bot1'):
                items=[c for c in cs if c['opponent_spec']['group']==family]
                groups=[]
                for score in (0,1):
                    xs=[c for c in items if c['source_score']==score]
                    offset=seed%len(xs) if xs else 0;groups.append(xs[offset:]+xs[:offset])
                queue=[]
                for j in range(max(map(len,groups),default=0)):
                    for xs in groups:
                        if j<len(xs):queue.append(xs[j])
                queues[family]=queue
            schedule=('astra','bot2','bot1','astra','bot2','astra')
            while any(queues.values()):
                for family in schedule:
                    if queues[family]:mixed.append(queues[family].pop(0))
        else:
            lost=[c for c in cs if not c['source_score']];won=[c for c in cs if c['source_score']]
            for i in range(max(len(lost),len(won))):
                if i<len(lost):mixed.append(lost[i])
                if i<len(won):mixed.append(won[i])
        grouped[seed]=mixed
    chosen=[]
    for i in range(max((len(cs) for cs in grouped.values()),default=0)):
        for cs in grouped.values():
            if i<len(cs) and len(chosen)<cap:chosen.append(cs[i])
    jobs=[]
    for c in chosen:
        train.atomic(RUN/'tactical-sources'/(c['case']+'.json'),c)
        for sample in range(samples):
            for route in c['routes']:
                jobs.append((f'{c["case"]}-w{sample}-{route}',{'case':c['case'],'sample':sample,'route':route,'arm':arm}))
    manifest={'batch':batch,'arm':arm,'cases':[c['case'] for c in chosen],'coverage':dict(coverage),'roots':len(chosen),
        'seed_groups':len({c['seed'] for c in chosen}),'by_split':{s:{'roots':sum(c['split']==s for c in chosen),'groups':len({c['seed'] for c in chosen if c['split']==s})} for s in ('train','validation')},
        'samples':samples,'jobs':len(jobs),'family_balanced':balance_families,'selection':'earliest eligible T1-5 branch, per-source-seed round-robin, wins and losses included',
        'worlds':'sample0 exact original; alternate samples shuffle remaining deck orders and future RNG only, original hidden hands fixed'}
    train.atomic(RUN/'tactical-sources'/f'manifest-{batch}-{arm}.json',manifest);reserve('tactical',jobs);print(json.dumps(manifest))

def restore(src):
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    seat=src['seat'];spec=src['opponent_spec'];arm=src['arm']
    decks={seat:load_deck(HERE/'candidates'/arm/'deck.json'),3-seat:load_deck(ROOT/spec['deck'])}
    e=Engine(decks[1],decks[2],src['seed'],max_turns=180);folder=ROOT/src['game_path']
    logs={i:[json.loads(l) for l in (folder/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
    ix={1:0,2:0};steps=0
    while not e.over:
        active,_=e.pending();row=logs[active][ix[active]];s=e.view(active)
        assert visible(s)==visible(row['state']),('prefix public mismatch',src['case'],active,ix[active])
        if active==seat and row['state']['seq']==src['seq']:
            assert digest(s)==src['state_digest'];return e,steps
        assert e.step(active,row['action']).accepted;ix[active]+=1;steps+=1
    raise ValueError('root not reached')

def execute(job):
    setup(job.get('policy_arm',job['arm']))
    from program_policy import decide
    from state_features import with_public_history
    from action_validator import legal
    from development.secret_hunter_tactics.run import opponent
    src=json.loads((RUN/'tactical-sources'/(job['case']+'.json')).read_text())
    e,prefix=restore(src);seat=src['seat'];root_turn=e.turn;before=digest(e.view(seat))
    if job['sample']:
        rng=random.Random(81600000+src['seed']*17+job['sample'])
        for i in (1,2):rng.shuffle(e.player(i).deck)
        e.game.random.seed(91700000+src['seed']*31+job['sample'])
    assert before==digest(e.view(seat))
    hidden={'deck1':[c.id for c in e.player(1).deck],'deck2':[c.id for c in e.player(2).deck],
        'hand1':[c.id for c in e.player(1).hand],'hand2':[c.id for c in e.player(2).hand],
        'rng_hash':hashlib.sha256(repr(e.game.random.getstate()).encode()).hexdigest()}
    cfg=json.loads((HERE/'candidates'/job.get('policy_arm',job['arm'])/'config.json').read_text());foe=opponent(src['opponent_spec'])
    memory={};sequence=[];trace=[];endpoint=None;after_response=None;changes=0
    own_decisions=0;policy_changes=0;fallbacks=0
    for step in range(700):
        if e.over:break
        active,_=e.pending();s=e.view(active);history=[v for ev in e.events if (v:=ev.view(active)) is not None]
        s.update(player=active,seq=step+1,game_id='offline-public-turn',timeout_s=2,events=[]);s=with_public_history(s,history)
        intervention=active==seat and e.turn==root_turn
        if active==seat:
            a,info=decide(s,cfg);assert not info.get('error'),info.get('error');base=dict(info.get('learned_parent_action',a))
            own_decisions+=1;policy_changes+=int(a!=base);fallbacks+=bool(info.get('fallback'))
            if job.get('policy_arm'):assert not info.get('fallback'),('actual learned policy fallback',job,info)
            if intervention and job['route']!='baseline' and info.get('reason')!='guaranteed_lethal':
                alternative=propose(s,job['route'],memory,base)
                if alternative is not None:a=alternative
            changes+=int(intervention and a!=base)
        else:a=foe.fn(s);base=None
        assert legal(s,a),('route illegal',job,a)
        if intervention:sequence.append({'action':a,'baseline_action':base,'state':visible(s),'state_digest':digest(s)})
        trace.append({'seat':active,'turn':s['turn'],'action':a,'state_digest':digest(s)})
        assert e.step(active,a).accepted
        if intervention:
            endpoint=visible(e.view(seat));sequence[-1]['next_visible']=endpoint
        if after_response is None and (e.over or e.turn>=root_turn+2):after_response=visible(e.view(seat))
    assert e.over,('nonterminal',job)
    if job['sample']==0 and job['route']=='baseline' and not job.get('policy_arm'):assert int(e.winner==seat)==src['source_score'],('baseline result mismatch',job)
    return {**job,'source_seed':src['seed'],'split':src['split'],'features':src['features'],
        'source_score':src['source_score'],'prefix_verified_steps':prefix,'root_digest':before,'audit_hidden':hidden,
        'win':int(e.winner==seat),'winner':e.winner,'terminal':True,'actions_changed':changes,
        'own_decisions':own_decisions,'policy_changed_actions':policy_changes,'fallbacks':fallbacks,
        'first_changed':bool(sequence and sequence[0]['action']!=sequence[0]['baseline_action']),
        'later_changed':any(x['action']!=x['baseline_action'] for x in sequence[1:]),
        'sequence':sequence,'endpoint':endpoint,'after_response':after_response,'trace':trace}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--arm',default='B')
    p.add_argument('--cap',type=int,default=360);p.add_argument('--samples',type=int,default=3)
    p.add_argument('--balance-families',action='store_true')
    a=p.parse_args();mine(a.batch,a.arm,a.cap,a.samples,a.balance_families)
