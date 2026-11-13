"""Audit archived pairs and explain the historical narrow continuation funnel."""
from collections import Counter,defaultdict
import hashlib
import json
import sys
import time
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import RUN,ROOT
sys.path.insert(0,str(HERE/'candidates/engine-trap-commit-v3/scripts'))
import tactical_model as model
from turn_commit import remember
from development.secret_hunter_turn_plans.routes import context,public_features


def main():
    archive=RUN/'imported/hearthstone_astra_0066a30/evidence';pools=json.loads((ROOT/'development/teacher_eval/core.json').read_text())
    if isinstance(pools,dict):pools=pools['opponents']
    specs={r['name']:r for r in pools};reports={};selected=[];buckets=Counter();seen=set()
    for arm in ('engine-trap-v2','Y1'):
        folder=archive/('dev-'+arm);counts=Counter();games=defaultdict(set);rejections=[]
        rows=[json.loads(l) for l in (folder/'results.jsonl').read_text().splitlines()]
        for r in rows:
            path=folder/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl'
            if not path.exists():continue
            counts['games_read']+=1;history=[]
            split='train' if int(hashlib.sha256(str(r['seed']).encode()).hexdigest()[:8],16)%5<3 else 'validation'
            for line in path.read_text().splitlines():
                d=json.loads(line);s=d['state'];history.extend(s.get('events',[]))
                if s['phase']!='main':continue
                seq=d['info'].get('turn_search',{}).get('sequence',[]);a=d['action'];counts['main_decisions']+=1
                flags={};flags['active_trap']=[c['card_id'] for c in s['you'].get('secrets',[])]==['EX1_610']
                flags['trap_and_deathrattle']=flags['active_trap'] and any(m.get('deathrattle') for m in s['opponent']['board'])
                target=next((m for m in s['opponent']['board'] if m['entity_id']==a.get('target')),None)
                flags['trap_target_deathrattle']=bool(flags['active_trap'] and target and target.get('deathrattle'))
                memory={};remember(s,a,seq,memory,time.monotonic()+1)
                flags['historical_remember_succeeded']=bool(memory.get('trap_steps'))
                if flags['trap_target_deathrattle'] and not flags['historical_remember_succeeded']:
                    rejections.append({'game':r['game'],'seed':r['seed'],'seat':r['seat'],'seq':s['seq'],
                                       'target':target['card_id'],'plan':seq,'supported':model.supported(s),
                                       'has_multiaction_plan':len(seq)>1,
                                       'supported_death_tokens':model.DEATH_TOKENS.get(target['card_id'],[]),
                                       'tail_has_rejected_action':any(x['type'] not in ('play_card','hero_power') or x.get('target') is not None for x in seq[1:])})
                flags['keeper_end_omission']=a['type']=='end_turn' and len(s['you']['board'])<7 and any(c['card_id']=='EX1_080' and c['cost']<=s['you']['mana'] for c in s['you']['hand'])
                for k,v in flags.items():
                    if v:counts[k]+=1;games[k].add(r['game'])
                for kind in context(s):
                    enemy={m['card_id'] for m in s['opponent']['board']}
                    if s['you']['mana']<2 or d['info'].get('reason')=='guaranteed_lethal':continue
                    if kind=='trap' and not flags['trap_and_deathrattle']:continue
                    if kind=='knife_wolf' and not {'NEW1_019','EX1_162'}<=enemy:continue
                    if kind=='amani' and s['opponent']['hero']['hero_class']!='WARLOCK':continue
                    key=(kind,r['seed']);bucket=(kind,split,r['score'])
                    if key in seen or buckets[bucket]>=4:continue
                    seen.add(key);buckets[bucket]+=1
                    selected.append({'case':f'{kind}-h{len(selected):03d}','kind':kind,'split':split,
                        'source_seed':r['seed'],'source_game':r['game'],'seat':r['seat'],'source_arm':arm,
                        'source_outcome':r['score'],'opponent_spec':specs[r['opponent']],'state':s,
                        'original_action':a,'original_plan':seq,'public_history':list(history),
                        'public_features':public_features(s),'source_path':str(path),'historical_gates':flags})
        reports[arm]={'decisions':dict(counts),'games':{k:len(v) for k,v in games.items()},'rejected_targeted_plans':rejections}
    out=RUN/'mined-historical';out.mkdir(exist_ok=True)
    for r in selected:(out/(r['case']+'.json')).write_text(json.dumps(r,indent=2)+'\n')
    result={'funnel':reports,'cases':len(selected),'buckets':{str(k):v for k,v in buckets.items()},
            'grouping':'SHA256(source seed) mod 5; all source arms, opponents and seats share a split. At most one case per kind/source seed.',
            'scope':'Archived real engine-trap-v2 and Y1 local proxy trajectories from the recovered commit.'}
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'docs/secret_hunter_turn_plans/historical-funnel.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
