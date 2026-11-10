"""Replay public action prefixes, then compare old/new observation-only suffixes.

Engine cloning is confined to this offline diagnostic harness, never the Skill.
These selected failures are not independent win-rate evidence.
"""
import copy,json
from pathlib import Path
from hs_arena.engine import Engine
from hs_arena._fp import init_engine
from development.benchmarks.run import load_policy
from development.opponents.population import decide as population_decide
from development.opponents.search import decide as search_decide


def main():
    old,actions=load_policy('development/candidates/v6-zoo-guide')
    new,_=load_policy('development/candidates/v7-zoo-combat')
    db=init_engine();memo={id(c):c for c in db.db.values()}
    cases=json.loads(Path('development/reports/zoo-v6-loss-audit.json').read_text())['loss_cases']
    results=[]
    for case in cases:
        if not case['taunt_stall_seqs']:continue
        directory=Path(case['replay']).parent;experiment=directory.parent
        manifest=json.loads((experiment/'manifest.json').read_text())
        opponent=next(o for o in manifest['population'] if o['name']==case['opponent'])
        from hs_arena.deck import load_deck
        decks={case['seat']:load_deck('development/candidates/v6-zoo-guide/deck.json'),3-case['seat']:load_deck(opponent['deck'])}
        e=Engine(decks[1],decks[2],case['seed'],max_turns=180)
        records={i:[json.loads(l) for l in (directory/f'p{i}/observations.jsonl').read_text().splitlines()] for i in (1,2)}
        positions={1:0,2:0};seq=case['taunt_stall_seqs'][0]
        while not e.over:
            i,_=e.pending();row=records[i][positions[i]];positions[i]+=1
            view=e.view(i)
            for field in ('phase','turn','you','opponent','legal_actions'):
                assert view[field]==row['state'][field],(case,field)
            if i==case['seat'] and row['state']['seq']==seq:break
            assert e.step(i,row['action']).accepted
        assert not e.over
        if opponent.get('policy'):
            p,_=load_policy(opponent['policy'])
            cfg=json.loads((Path(opponent['policy'])/'config.json').read_text())
            opponent_fn=lambda s:p.decide(s,cfg)
        elif opponent['mode']=='search':opponent_fn=lambda s:search_decide(s,actions.expand)
        else:opponent_fn=lambda s:population_decide(s,opponent['mode'],actions.expand)
        branches={};first={}
        for name,policy in (('old',old),('new',new)):
            branch=copy.deepcopy(e,dict(memo));first[name]=policy.decide(branch.view(case['seat']))
            count=0
            while not branch.over:
                seat,_=branch.pending();s=branch.view(seat)
                action=policy.decide(s) if seat==case['seat'] else opponent_fn(s)
                assert branch.step(seat,action).accepted
                count+=1;assert count<2500
            branches[name]={'winner':branch.winner,'candidate_won':branch.winner==case['seat'],'suffix_actions':count}
        assert not branches['old']['candidate_won'],'Old branch must reproduce loss'
        results.append({'seed':case['seed'],'seat':case['seat'],'opponent':case['opponent'],'seq':seq,
                        'first_actions':first,'branches':branches,'observations':case['observations']})
    out={'cases':results,'cases_count':len(results),'changed_first_action':sum(c['first_actions']['old']!=c['first_actions']['new'] for c in results),
         'new_wins':sum(c['branches']['new']['candidate_won'] for c in results),'old_wins':0,
         'note':'Selected historical failures, switched policy only after first flagged stall. Diagnostic, not a fresh benchmark.'}
    Path('development/reports/zoo-v7-counterfactuals.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
