"""First divergent executed action and search denominators for frozen arms."""
import argparse
from collections import Counter
import json
from development.secret_hunter_long.study import RUN
from development.secret_hunter_long.tactical import digest
from development.secret_hunter_mcgs import train
from development.teacher_eval.compare import index

def run(batch,left,right):
    db=train.connect(RUN);maps=[]
    for arm in (left,right):maps.append(index([json.loads(r[0]) for r in db.execute("select result from tasks where batch=? and candidate=? and status='done'",(batch,arm))]))
    aa,bb=maps;assert aa.keys()==bb.keys();counts={a:Counter() for a in (left,right)};examples=[];classes=Counter()
    for key in sorted(aa):
        logs=[]
        for arm,row in ((left,aa[key]),(right,bb[key])):
            folder=RUN/'batches'/batch/arm/'games'/row['game'];records=[json.loads(l) for l in (folder/f'p{row["seat"]}'/'observations.jsonl').read_text().splitlines()];logs.append(records)
            c=counts[arm];c['games']+=1;c['decisions']+=len(records)
            for r in records:
                info=r.get('info',{});search=info.get('turn_search',{});reply=search.get('reply',{})
                c['turn_search_calls']+=bool(search);c['supported_roots']+=bool(search.get('supported'))
                c['planned_action_available']+=bool(search.get('action'));c['plan_nodes']+=search.get('nodes',0)
                c['time_cutoffs']+=search.get('stop_reason')=='time';c['node_cutoffs']+=search.get('stop_reason')=='nodes'
                c['reply_calls']+=bool(reply);c['reply_comparable']+=bool(reply.get('comparable'));c['reply_endpoints']+=reply.get('candidates',0)
                c['recovery_calls']+=reply.get('recovery_calls',0);c['recovery_supported']+=reply.get('recovery_supported',0);c['recovery_nodes']+=reply.get('recovery_nodes',0)
                c['adaptive_depth_calls']+=bool(search.get('adaptive_depth'));c['lethal_proofs']+=bool(info.get('lethal',{}).get('guaranteed'))
                c['learned_rule_changes']+=bool(info.get('learned_rule_changed'))
        divergence=None
        for ix,(a,b) in enumerate(zip(*logs)):
            if digest(a['state'])!=digest(b['state']):
                divergence={'kind':'upstream_public_state_difference','index':ix};break
            if a['action']!=b['action']:
                kind='mulligan' if a['state']['phase']=='mulligan' else 'narrow_lethal' if b['info'].get('lethal',{}).get('proof') else 'same_state_tactical'
                divergence={'kind':kind,'index':ix,'seq':a['state']['seq'],'turn':a['state']['turn'],'a':a,'b':b,
                    'a_next_visible':logs[0][ix+1]['state'] if ix+1<len(logs[0]) else aa[key]['result'],
                    'b_next_visible':logs[1][ix+1]['state'] if ix+1<len(logs[1]) else bb[key]['result']};break
        if divergence:
            classes[divergence['kind']]+=1
            if divergence['kind']!='upstream_public_state_difference' or aa[key]['score']!=bb[key]['score']:
                examples.append({'key':list(key),'a_win':aa[key]['score'],'b_win':bb[key]['score'],**divergence})
    result={'batch':batch,'left':left,'right':right,'denominators':{a:dict(c) for a,c in counts.items()},'first_divergences':dict(classes),
       'examples':examples,'scope':'same-deck comparisons isolate first action divergence; deck substitutions change public remaining-card counts at the initial state'}
    train.atomic(RUN/'analysis'/f'{batch}-{left}-{right}-actions.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='examples'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('left');p.add_argument('right');a=p.parse_args();run(a.batch,a.left,a.right)
