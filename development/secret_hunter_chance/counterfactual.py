"""Early public decision disagreements with conditional terminal continuations."""
import copy,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_chance.accounting import reserve,finish
SRC=ROOT/'experiments/secret-hunter-chance-m1-screen'
C=ROOT/'development/secret_hunter_chance/candidates/C1'
D=ROOT/'docs/secret_hunter_chance'


def find(row):
    sys.path.insert(0,str(C/'scripts'))
    from program_policy import decide
    cfg=json.loads((C/'config.json').read_text());count=0
    for z in readlines(SRC/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl'):
        s=z['state']
        if s['phase']!='main' or not 4<=s['turn']<=14:continue
        # Existing public telemetry identifies plausible combo states cheaply.
        y=s['you']
        if not any(m['card_id']=='NEW1_019' for m in y['board']+y['hand']):continue
        a,info=decide(s,cfg);count+=1
        q=info.get('chance',{})
        if q.get('action') and a!=z['action']:
            return {'row':row,'observation':s,'original_action':z['action'],'alternative':a,
                    'chance':q,'source_info':z['info'],'evaluated':count}
    return {'row':row,'skipped':True,'evaluated':count}


def rollout(task):
    case,spec,index=task;row=case['row'];seat=row['seat']
    sys.path.insert(0,str(C/'scripts'))
    from hs_arena.engine import Engine
    from hs_arena.deck import load_deck
    from hs_arena.runner import build_state
    from hs_arena.protocol import Config
    from development.secret_hunter_tactics.run import opponent
    from program_policy import decide
    from state_features import with_public_history
    from action_validator import legal
    own=load_deck(C/'deck.json');other=load_deck(ROOT/spec['deck']);cfg=json.loads((C/'config.json').read_text())
    e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed'],max_turns=180)
    obs={i:readlines(SRC/'games'/row['game']/f'p{i}/observations.jsonl') for i in (1,2)};idx={1:0,2:0};prefix=0
    while True:
        who,_=e.pending();z=obs[who][idx[who]]
        if who==seat and z['state']['seq']==case['observation']['seq']:break
        assert e.step(who,z['action']).accepted and not e.over;idx[who]+=1;prefix+=1
    policy=opponent(spec);alternatives=[]
    for action in (case['original_action'],case['alternative']):
        outcomes=[]
        for sample in range(8):
            b=copy.deepcopy(e);b.game.random.seed(744000+index*100+sample)
            for player in b.game.players:b.game.random.shuffle(player.deck)
            steps=0;error=None;policy_errors=0
            try:
                assert b.step(seat,action).accepted
                while not b.over and steps<600:
                    p,_=b.pending();s=build_state(b,'conditional-chance',p,steps+1,None,Config(max_turns=180))
                    if p==seat:
                        history=[ev.view(seat) for ev in b.events if ev.view(seat) is not None]
                        a,inf=decide(with_public_history(s,history),cfg)
                        policy_errors+=bool(inf.get('error'))
                        assert legal(s,a) and not inf.get('error')
                    else:a=policy.fn(s)
                    assert b.step(p,a).accepted;steps+=1
                if not b.over:error='continuation_limit'
            except Exception:error=traceback.format_exc()
            outcomes.append({'sample':sample,'win':int(b.over and b.winner==seat),'terminal':b.over,'steps':steps,'error':error,'policy_errors':policy_errors})
        alternatives.append({'action':action,'outcomes':outcomes,'win_rate':sum(o['win'] for o in outcomes)/8})
    return {**case,'alternatives':alternatives,'prefix_actions':prefix,'split':'validation' if index%4==3 else 'train','continuation':'C1 own / original frozen opponent; both actions share eight resampled future RNG/deck orders, conditioned on existing hidden hands. Policies receive only public build_state/history. Divergent actions do not guarantee identical subsequent draws.','budget':{'full_games':16,'samples_per_action':8}}


def main():
    rows=sorted(readlines(SRC/'results.jsonl'),key=lambda r:(r['score'],r['opponent'],r['seed'],r['seat']))
    reserve('counterfactual-selection',short=3000)
    with ProcessPoolExecutor(max_workers=6) as pool:cases=list(pool.map(find,rows))
    write(D/'counterfactual-selection.json',cases);finish('counterfactual-selection',actual_short=sum(c['evaluated'] for c in cases))
    found=[c for c in cases if not c.get('skipped')]
    losses=[c for c in found if not c['row']['score']];wins=[c for c in found if c['row']['score']]
    selected=losses[:12]+wins[:12]
    specs={s['name']:s for s in json.loads((SRC/'config.json').read_text())['population']}
    reserve('counterfactual-terminal',full=len(selected)*16,short=2000)
    out=[]
    with ProcessPoolExecutor(max_workers=6) as pool,(D/'counterfactual.jsonl').open('w') as f:
        futures=[pool.submit(rollout,(c,specs[c['row']['opponent']],i)) for i,c in enumerate(selected)]
        for future in as_completed(futures):
            c=future.result();out.append(c);f.write(json.dumps(c)+'\n');f.flush();print('cases',len(out),len(selected),flush=True)
    finish('counterfactual-terminal',completed=len(out)*16,actual_short=sum(c['prefix_actions'] for c in out),errors=sum(bool(o['error']) for c in out for a in c['alternatives'] for o in a['outcomes']))
    print(json.dumps({'cases':len(out),'found_disagreement_games':len(found),'full_games':len(out)*16,'loss_cases':min(12,len(losses))}))
if __name__=='__main__':main()
