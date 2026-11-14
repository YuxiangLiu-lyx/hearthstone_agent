"""Keep resource-distinct tails while retaining six total response evaluations."""
import json
import shutil
from development.secret_hunter_final.study import HERE
from development.benchmarks.run import fingerprint

HELPERS='''
def endpoint_resources(s):
    y,o=s['you'],s['opponent']
    return (tuple(sorted(c['card_id'] for c in y['hand'])),
            (y.get('weapon') or {}).get('durability',0),
            sum(m['health']==1 for m in y['board']),
            sum(m['attack'] for m in o['board']),y['hero']['health'])

def retain_endpoint(bucket,item):
    pool=sorted(bucket+[item],key=lambda x:x[0],reverse=True)
    first=pool[0];signature=endpoint_resources(first[1])
    second=next((x for x in pool[1:] if endpoint_resources(x[1])!=signature),None)
    return [first]+([second] if second else [])

def response_shortlist(buckets,limit):
    primary=sorted((b[0] for b in buckets),key=lambda x:x[0],reverse=True)
    # Four first actions and at most two alternative tails use the old six-leaf
    # response budget. If no distinct tail exists, restore the original breadth.
    leaders=primary[:max(1,limit-2)]
    alternate=[]
    for first in leaders:
        bucket=next(b for b in buckets if b[0] is first)
        if len(bucket)>1:alternate.append(bucket[1])
    alternate.sort(key=lambda x:x[0],reverse=True)
    selected=leaders+alternate[:2]
    for item in primary[len(leaders):]:
        if len(selected)>=limit:break
        selected.append(item)
    return selected[:limit]
'''

def main():
    dest=HERE/'candidates/T';assert not dest.exists()
    shutil.copytree(HERE/'candidates/ML2',dest,ignore=shutil.ignore_patterns('__pycache__'))
    p=dest/'scripts/turn_search.py';s=p.read_text()
    changes={"endpoints={'end_turn':(best,initial,[])}":"endpoints={'end_turn':[(best,initial,[])]}",
             "if root not in endpoints or v>endpoints[root][0]:endpoints[root]=(v,successor,path)":"endpoints[root]=retain_endpoint(endpoints.get(root,[]),(v,successor,path))",
             "candidates=sorted(endpoints.values(),key=lambda x:x[0],reverse=True)[:cfg.get('reply_candidates',6)]":"candidates=response_shortlist(list(endpoints.values()),cfg.get('reply_candidates',6))\n        report['endpoint_funnel']={'first_actions':len(endpoints),'retained':sum(map(len,endpoints.values())),'same_first_alternates':sum(len(b)>1 for b in endpoints.values()),'response_candidates':len(candidates),'max_total_response_candidates':cfg.get('reply_candidates',6)}"}
    for old,new in changes.items():assert s.count(old)==1;s=s.replace(old,new)
    p.write_text(s+HELPERS)
    path=HERE/'lineage.json';lineage=json.loads(path.read_text())
    lineage.append({'name':'T','parent':'ML2','sha256':fingerprint(dest),
                    'hypothesis':'Retain two resource-distinct endpoints per first action; same six-response total budget',
                    'status':'coverage gate pending; no commitment cache'})
    path.write_text(json.dumps(lineage,indent=2)+'\n')
    print(fingerprint(dest))

if __name__=='__main__':main()
