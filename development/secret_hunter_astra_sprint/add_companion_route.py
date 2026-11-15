"""Diagnostic-only correction: Animal Companion is a spell, not a minion."""
import json
import time
from collections import Counter
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint.tactical import setup,propose
from development.secret_hunter_astra_sprint.cfqueue import reserve
from development.secret_hunter_astra_sprint import ledger

def main():
    setup('DARCL2')
    from action_validator import legal
    jobs=[];extra={};counts=Counter()
    for path in sorted((RUN/'tactical-sources').glob('sprint-*.json')):
        src=json.loads(path.read_text());action=propose(src['state'],'coin_companion',{},src['original_action'])
        if action is None or not legal(src['state'],action):continue
        counts[src['split']+'_eligible']+=1
        if len(src['routes'])>=6:
            counts[src['split']+'_skip_prespecified_five_alternative_cap']+=1;continue
        extra[src['case']]=['coin_companion'];counts[src['split']+'_added']+=1
        for world in range(3):
            jobs.append((f"{src['case']}-w{world}-coin_companion",{'case':src['case'],'sample':world,'route':'coin_companion','arm':'DARCL2'}))
    record={'created':time.time(),'routes_by_case':extra,'counts':dict(counts),'jobs':len(jobs),
        'reason':'The inherited coin_minion route excludes Animal Companion because it is a spell. Add this single diagnostic route with unchanged source roots and baseline worlds. No policy candidate changed and no held-out outcomes inspected.',
        'source_files_unchanged':True,'baseline_jobs_reused':True,'source_group_partitions_unchanged':True}
    path=RUN/'tactical-extra-routes.json';assert not path.exists()
    ledger.atomic(path,record);reserve('tactical',jobs)
    print(json.dumps({k:v for k,v in record.items() if k!='routes_by_case'},indent=2))

if __name__=='__main__':main()
