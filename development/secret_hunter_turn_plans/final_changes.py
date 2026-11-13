"""Read-only diagnosis of frozen final actions; never changes the challenger."""
import argparse
import json
import sys
import time

from development.secret_hunter_turn_plans.study import ROOT,RUN
from development.secret_hunter_turn_plans.build import HERE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True);args=parser.parse_args()
    folder=RUN/'batches'/args.batch;arms=['engine-trap-v2','E2-finish-minions']
    rows={a:[json.loads(line) for line in (folder/a/'results.jsonl').read_text().splitlines()] for a in arms}
    base={(r['opponent'],r['seed'],r['seat']):r for r in rows[arms[0]]};changes=[]
    def observations(arm,row):
        path=folder/arm/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl'
        return path,[json.loads(line) for line in path.read_text().splitlines()]
    for row in rows[arms[1]]:
        path,events=observations(arms[1],row)
        for event in events:
            if not event['info'].get('turn_routes',{}).get('changed'):continue
            key=(row['opponent'],row['seed'],row['seat']);old=base[key];old_path,old_events=observations(arms[0],old)
            after={}
            for name,items in [(arms[0],old_events),(arms[1],events)]:
                after[name]=next((e for e in items if e['state']['turn']>event['state']['turn']),None)
            changes.append({'key':key,'baseline_win':old['score'],'candidate_win':row['score'],
                'candidate_event':event,'next_own_turn':after,
                'baseline_trace':str(old_path.relative_to(ROOT)),'candidate_trace':str(path.relative_to(ROOT))})
    result={'batch':args.batch,'scope':'Post-freeze read-only diagnosis; final seeds become development if used to tune a later policy.',
            'actual_changed_decisions':len(changes),'changes':changes}
    if args.batch=='final-core':
        loss=next(r for r in changes if r['baseline_win']>r['candidate_win'])
        state=loss['candidate_event']['state'];action=loss['candidate_event']['action']
        card=next(c for c in state['you']['hand'] if c['entity_id']==action['card'])
        assert card['card_id']=='EX1_029'
        sys.path[:0]=[str(HERE/'candidates/E2-finish-minions/scripts'),str(ROOT/'development/secret_hunter_mcgs')]
        from mcgs_init import initialize
        initialize()
        from mcgs_world import build
        import tactical_model as model
        import public_response as response
        amani=next(m for m in state['opponent']['board'] if m['card_id']=='EX1_393')
        reply={'type':'attack','attacker':amani['entity_id'],'target':card['entity_id']}
        projected=model.transition(model.prepare({**state,'planning_mode':'response'}),action)
        predicted=response.attack(response.prepare_reply(projected),reply)
        world=build(state,9001)
        assert world.step(1,action).accepted
        assert world.step(1,{'type':'end_turn'}).accepted
        assert world.step(2,reply).accepted
        actual=world.view(1)
        def public_summary(s):return {'own_hp':s['you']['hero']['health'],'enemy_hp':s['opponent']['hero']['health'],
            'own_board':[(m['card_id'],m['attack'],m['health']) for m in s['you']['board']],
            'enemy_board':[(m['card_id'],m['attack'],m['health']) for m in s['opponent']['board']]}
        assert public_summary(predicted)==public_summary(actual)
        result['gnome_enrage_differential']={'prediction':public_summary(predicted),'engine':public_summary(actual),
            'interpretation':'The existing public model correctly predicts the visible trade enabling Enrage. The final regression is a harmful commitment overriding fresh end-turn selection, not a missing Amani damage rule.'}
        # Show the earlier search bottleneck without changing the frozen policy:
        # two complete endpoints have the same first action, so the old map
        # discards one before evaluating an opponent response.
        previous_path=ROOT/loss['candidate_trace']
        previous=next(e for line in previous_path.read_text().splitlines()
                      if (e:=json.loads(line))['state']['seq']==state['seq']-1)
        from turn_search import value
        cfg=json.loads((HERE/'candidates/engine-trap-v2/config.json').read_text())
        first=previous['action']
        hold=model.transition(model.prepare({**previous['state'],'planning_mode':'response'}),first)
        develop=model.transition(hold,action)
        endpoints=[]
        for label,endpoint,path in [('trade_then_stop',hold,[first,{'type':'end_turn'}]),
                                    ('trade_then_gnome',develop,[first,action,{'type':'end_turn'}])]:
            before=value(endpoint,cfg)
            reply_result=response.worst_reply(endpoint,cfg,time.monotonic()+2,512)
            assert reply_result['supported']
            weight=cfg.get('reply_weight',.85)
            endpoints.append({'route':label,'actions':path,'before_reply':before,
                'after_reply':reply_result['value'],'combined':(1-weight)*before+weight*reply_result['value'],
                'reply_nodes':reply_result['nodes']})
        result['same_first_action_endpoint_loss']={'source_seq':previous['state']['seq'],
            'original_plan':previous['info']['turn_search']['sequence'],'endpoints':endpoints,
            'source_function':'turn_search.plan: endpoints[root] retains only the highest pre-response value per first action.',
            'interpretation':'Retaining multiple resource-distinct endpoints per first action is a next-round hypothesis. This diagnostic does not tune or modify final code.'}
    out=ROOT/'docs/secret_hunter_turn_plans'/(args.batch+'-action-changes.json')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'batch':args.batch,'changed_decisions':len(changes),
        'changed_keys':[r['key'] for r in changes],'gnome_differential_passed':'gnome_enrage_differential' in result}))


if __name__=='__main__':main()
