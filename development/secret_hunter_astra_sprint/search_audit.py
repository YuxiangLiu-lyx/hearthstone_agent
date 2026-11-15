"""Offline instrumentation of an unchanged candidate's bounded turn search."""
import argparse
import copy
import json
import time
import types
from pathlib import Path
from development.secret_hunter_astra_sprint.study import HERE,RUN
from development.secret_hunter_astra_sprint.tactical import setup
from development.secret_hunter_astra_sprint.mine import action_key
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import sha

def instrument(arm):
    path=HERE/'candidates'/arm/'scripts/turn_search.py';source=path.read_text()
    replacements=[
        ("report={'nodes':0", "report={'audit':{'generated':[],'frontiers':[],'endpoints':[],'reply_candidates':[],'reply_scores':[]},'nodes':0"),
        ("successor=model.transition(current,action);report['nodes']+=1", "successor=model.transition(current,action);report['nodes']+=1\n                report['audit']['generated'].append({'line':line+[action],'supported':successor is not None})"),
        ("frontier=[(s,line) for _,s,line in following[:width]]", "frontier=[(s,line) for _,s,line in following[:width]]\n        report['audit']['frontiers'].append([line for _,line in frontier])"),
        ("if cfg.get('public_response') and time.monotonic()<outer_deadline:", "report['audit']['endpoints']=[{'before':v,'line':line} for v,_,line in endpoints.values()]\n    if cfg.get('public_response') and time.monotonic()<outer_deadline:"),
        ("reply_deadline=min(outer_deadline", "report['audit']['reply_candidates']=[line for _,_,line in candidates]\n        reply_deadline=min(outer_deadline"),
        ("evaluated.append((v,path,response))", "evaluated.append((v,path,response))\n            report['audit']['reply_scores'].append({'value':v,'line':path,'response':response})"),
    ]
    for old,new in replacements:
        assert source.count(old)==1,(path,old,source.count(old))
        source=source.replace(old,new)
    module=types.ModuleType('offline_instrumented_turn');module.__file__=str(path)
    exec(compile(source,str(path), 'exec'),module.__dict__)
    return module,sha(path)

def audit(case,arm='DARCL2'):
    setup(arm)
    from secret_policy import rank
    from action_validator import legal
    src=json.loads((RUN/'tactical-sources'/(case+'.json')).read_text())
    assert src['split']=='train','Held-out search inspection requires a separate, locked validation workflow'
    state=src['state'];cfg=json.loads((HERE/'candidates'/arm/'config.json').read_text())
    ranked=rank(state,cfg,time.monotonic()+1.5)
    module,digest=instrument(arm)
    result=module.plan(state,ranked,cfg,time.monotonic()+1.5)
    original=src['original_info'].get('turn_search',{})
    comparable=all(result.get(k)==original.get(k) for k in ('nodes','action','sequence','bounded_out','stop_reason','excluded','beam_pruned','depth'))
    trace=result.get('audit',{});by_route={}
    for route in src['routes']:
        p=RUN/'tactical-labels'/f'{case}-w0-{route}.json'
        if not p.exists():continue
        label=json.loads(p.read_text())
        if not label.get('terminal'):continue
        sequence=[r['action'] for r in label['sequence'] if r['action']['type']!='end_turn']
        canonical=[action_key(a) for a in sequence]
        generated=[g for g in trace.get('generated',[]) if g['supported']]
        paths=[[action_key(a) for a in g['line']] for g in generated]
        prefix=max((len(p) for p in paths if p==canonical[:len(p)]),default=0)
        root=action_key(label['sequence'][0]['action']) if label['sequence'] else None
        def starts(lines):return any(line and action_key(line[0])==root for line in lines)
        by_route[route]={'original_world_win':label['win'],'first_action':label['sequence'][0]['action'] if label['sequence'] else None,
            'route_action_count':len(sequence),'generated_prefix_length':prefix,
            'root_in_ranked':any(action_key(a)==root for _,a in ranked),
            'root_generated_supported':starts([g['line'] for g in generated]),
            'root_survived_beam':any(starts(lines) for lines in trace.get('frontiers',[])),
            'root_retained_endpoint':starts([x['line'] for x in trace.get('endpoints',[])]),
            'root_received_response_ranking':starts(trace.get('reply_candidates',[])),
            'root_in_chance_comparison':any(action_key(v['action'])==root for v in src['original_info'].get('chance',{}).get('comparisons',[])),
            'changed_actions':label['actions_changed'],'first_changed':label['first_changed']}
    return {'case':case,'arm':arm,'source_seed':src['seed'],'proxy':src['opponent_spec']['name'],
        'split':src['split'],'source_code_sha256':digest,'original_info':src['original_info'],
        'instrumented_matches_original_search':comparable,'instrumented_report':result,'route_coverage':by_route,
        'scope':'Public-state offline search instrumentation. Timed traces are evidence only when original search action/count/stop/prune metadata match.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--arm',default='DARCL2');a=p.parse_args()
    result=audit(a.case,a.arm)
    assert result['split']=='train','Do not inspect held-out roots during hypothesis generation'
    ledger.atomic(RUN/'search-audits'/(a.case+'.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('original_info','instrumented_report')},indent=2))
