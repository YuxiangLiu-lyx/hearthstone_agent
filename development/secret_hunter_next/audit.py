"""Separate state support, explored search limits, and excluded legal root actions."""
import argparse,json,sys,collections
from development.secret_hunter_program.common import ROOT,readlines,write,quantiles
from development.secret_hunter_next.accounting import reserve,finish

def reasons(s,m):
    r=[]
    if s['opponent'].get('secrets_count'):r.append('hidden_enemy_secret')
    for key in ('you','opponent'):
        side=s[key]
        r.extend('history:'+c['card_id'] for c in side.get('graveyard',[]) if c['card_id'] in m.UNSUPPORTED_HISTORY)
        r.extend('minion:'+c['card_id'] for c in side['board'] if not c.get('silenced') and c['card_id'] not in m.SAFE)
        r.extend('deathrattle:'+c['card_id'] for c in side['board'] if c.get('deathrattle') and c['card_id'] not in set(m.DEATH_TOKENS)|{'EX1_029','EX1_096','EX1_012'})
    return sorted(set(r))
def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--candidate',required=True);a=p.parse_args()
    sys.path.insert(0,str(ROOT/a.candidate/'scripts'))
    import tactical_model as m
    from actions import expand
    from action_validator import legal
    src=ROOT/'experiments'/('secret-hunter-next-'+a.run);rows=readlines(src/'results.jsonl');groups=collections.defaultdict(list);details=[];short=0
    name='audit-'+a.run;reserve(name,short=5000)
    for row in rows:
        obs=readlines(src/'games'/row['game']/f"p{row['seat']}"/'observations.jsonl')
        key=f"{row['opponent']}|{'win' if row['score'] else 'loss'}|{'first' if row['seat']==row['first_player'] else 'second'}"
        for z in obs:
            s=z['state'];info=z['info']
            if s['phase']!='main':continue
            ts=info.get('turn_search',{});lethal=info.get('lethal',{})
            record={'game':row['game'],'seq':s['seq'],'turn':s['turn'],'supported':m.supported(s),'unsupported_reasons':reasons(s,m),'turn_searched':bool(ts.get('nodes')),'normal_bounded':bool(ts.get('bounded_out')),'normal_exit':ts.get('reason'),'lethal_bounded':bool(lethal.get('bounded_out')),'lethal_upper_pruned':bool(lethal.get('pruned_by_upper_bound')),'reply_comparable':ts.get('reply',{}).get('comparable'),'nodes':info.get('nodes',0),'elapsed_s':z['elapsed_s'],'error':info.get('error'),'fallback':info.get('fallback',False),'excluded_roots':[]}
            if m.supported(s) and short<4800:
                initial=m.prepare({**s,'planning_mode':'response'})
                for action in list(expand(s))[:12]:
                    if action['type']=='end_turn' or not legal(s,action):continue
                    short+=1
                    if m.transition(initial,action) is None:
                        cid=next((c['card_id'] for c in s['you']['hand'] if c['entity_id']==action.get('card')),action['type'])
                        record['excluded_roots'].append(cid)
            groups[key].append(record);details.append(record)
    def group(rs):
        return {'states':len(rs),'supported':sum(r['supported'] for r in rs),'searched':sum(r['turn_searched'] for r in rs),'normal_bounded':sum(r['normal_bounded'] for r in rs),'lethal_bounded':sum(r['lethal_bounded'] for r in rs),'lethal_upper_pruned':sum(r['lethal_upper_pruned'] for r in rs),'unsupported_reasons':dict(collections.Counter(x for r in rs for x in r['unsupported_reasons'])),'normal_exit':dict(collections.Counter(r['normal_exit'] for r in rs if r['normal_exit'])),'excluded_roots':dict(collections.Counter(x for r in rs for x in r['excluded_roots'])),'latency_s':quantiles([r['elapsed_s'] for r in rs]),'nodes':quantiles([r['nodes'] for r in rs]),'errors':sum(bool(r['error']) for r in rs),'fallbacks':sum(r['fallback'] for r in rs)}
    report={'run':a.run,'all':group(details),'groups':{k:group(v) for k,v in groups.items()},'details':details,'short_transitions':short,'limits':'Old telemetry combines node/time exhaustion; beam-pruned counts were not logged. Unsupported states and losses are associations, not causes. Ordinary search is distinct from the independent base lethal entrypoint.'}
    write(ROOT/'docs/secret_hunter_next'/f'{name}.json',report);finish(name,actual_short=short);print(json.dumps({k:v for k,v in report.items() if k not in ('details','groups')}))
if __name__=='__main__':main()
