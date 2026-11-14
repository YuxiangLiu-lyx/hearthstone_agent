"""Read-only audit of complete terminal labels and source coverage."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from development.secret_hunter_long.study import RUN
from development.secret_hunter_long.cfqueue import connect
from development.secret_hunter_mcgs import train

def main():
    db=connect();bykind=defaultdict(Counter);bad=[]
    for row in db.execute("select * from cf_jobs where status='done'"):
        r=json.loads(Path(row['result_path']).read_text());c=bykind[row['kind']]
        c['complete']+=1;c['terminal']+=bool(r.get('terminal'));c['win']+=r.get('win',0)
        c['winner1']+=r.get('winner')==1;c['winner2']+=r.get('winner')==2
        if not r.get('terminal') or r.get('winner') not in (1,2) or r.get('error'):bad.append(row['key'])
        if row['kind']=='tactical':
            c['with_actual_override']+=bool(r['actions_changed']);c['prefix_steps_verified']+=r['prefix_verified_steps']
    assert not bad,bad
    coverage={}
    for path in sorted((RUN/'tactical-sources').glob('manifest-*.json')):
        m=json.loads(path.read_text());ss=[json.loads((RUN/'tactical-sources'/(cid+'.json')).read_text()) for cid in m['cases']]
        counts=Counter()
        for s in ss:
            row=db.execute("select result from tasks where batch=? and candidate=? and seed=? and seat=? and json_extract(opponent,'$.name')=? and status='done'",(m['batch'],m['arm'],s['seed'],s['seat'],s['opponent_spec']['name'])).fetchone()
            assert row;full=json.loads(row[0]);first=full['first_player']==s['seat']
            counts['actual_first' if first else 'actual_second']+=1
        coverage[path.name]={'roots':len(ss),'groups':len({s['seed'] for s in ss}),
           'source_wins':sum(s['source_score'] for s in ss),'source_losses':sum(not s['source_score'] for s in ss),
           'by_actual_first':dict(counts),'by_opponent':dict(Counter(s['opponent_spec']['name'] for s in ss)),
           'by_route':dict(Counter(r for s in ss for r in s['routes'])),'split':m['by_split']}
    result={'label_counts':{k:dict(v) for k,v in bykind.items()},'no_unknown_winner_or_truncation':True,
       'coverage':coverage,'attempts':dict(db.execute('select status,count(*) from cf_attempts group by status').fetchall()),
       'scope':'Snapshot of completed labels; pending jobs omitted. Overrides are actual executed route differences from parent at current branch states.'}
    train.atomic(RUN/'analysis/label-integrity.json',result);print(json.dumps({k:v for k,v in result.items() if k!='coverage'}))

if __name__=='__main__':main()
