"""Audit locked-policy rollouts against exact paired baseline worlds."""
import argparse
from collections import Counter
import json
from pathlib import Path
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint.cfqueue import connect
from development.secret_hunter_astra_sprint.labels import summarize
from development.secret_hunter_astra_sprint import ledger

def analyze(arm):
    db=connect();rows=[];node_rows=[]
    for record in db.execute("select * from cf_jobs where kind='tactical' order by key"):
        job=json.loads(record['job'])
        if job.get('policy_arm')!=arm:continue
        assert record['status']=='done',('incomplete locked-policy labels',record['key'],record['status'])
        new=json.loads(Path(record['result_path']).read_text());case=job['case'];world=job['sample']
        old=json.loads((RUN/'tactical-labels'/f'{case}-w{world}-baseline.json').read_text())
        src=json.loads((RUN/'tactical-sources'/(case+'.json')).read_text())
        assert new['terminal'] and old['terminal'] and new['audit_hidden']==old['audit_hidden']
        assert new['root_digest']==old['root_digest']==src['state_digest']
        first=None
        for i,(a,b) in enumerate(zip(old['trace'],new['trace'])):
            assert (a['seat'],a['turn'],a['state_digest'])==(b['seat'],b['turn'],b['state_digest']),('Unexplained prefix divergence',case,world,i)
            if a['action']!=b['action']:
                assert a['seat']==src['seat'],('Opponent changed before candidate',case,world)
                first={'step':i,'turn':a['turn'],'state_digest':a['state_digest'],'baseline':a['action'],'candidate':b['action']};break
        if first is None:assert old['trace']==new['trace'] and old['winner']==new['winner']
        rows.append({'case':case,'seed':src['seed'],'opponent':src['opponent_spec']['name'],
            'split':src['split'],'world':world,'seat':src['seat'],'actual_first':src['actual_first'],
            'baseline':old['win'],'alternative':new['win'],'delta':new['win']-old['win'],
            'changed':bool(first),'first_changed':bool(first and first['step']==0),
            'later_changed':bool(first and first['step']>0),'first_difference':first})
        if world==0:
            info=new['sequence'][0]['info']
            node_rows.append({'case':case,'split':src['split'],'old_nodes':src['original_info']['nodes'],
                'new_nodes':info['nodes'],'old_turn':src['original_info'].get('turn_search',{}),
                'new_turn':info.get('turn_search',{}),'same_root_action':new['sequence'][0]['action']==old['sequence'][0]['action']})
    assert len(rows)==json.loads((RUN/(arm+'-continuation-plan.json')).read_text())['jobs']
    by_split={s:summarize([r for r in rows if r['split']==s]) for s in ('train','validation')}
    result={'candidate':arm,'total':summarize(rows),'by_split':by_split,
        'by_split_world':{s:{str(w):summarize([r for r in rows if r['split']==s and r['world']==w]) for w in (0,1,2)} for s in ('train','validation')},
        'by_proxy':{o:summarize([r for r in rows if r['opponent']==o]) for o in sorted({r['opponent'] for r in rows})},
        'rows':rows,'same_root_node_records':node_rows,
        'scope':'Outcome-stratified roots, paired remaining-deck worlds with original hidden hands fixed. Actual policy from root onward; these are not natural-frequency full-game gains.'}
    ledger.atomic(RUN/(arm+'-policy-continuations.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','same_root_node_records')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True);a=p.parse_args();analyze(a.arm)
