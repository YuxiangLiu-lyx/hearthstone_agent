"""Summarize paired turn labels, actual sequences, coverage and defense stress."""
from collections import Counter,defaultdict
import json
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train


def stats(pairs):
    return {'pairs':len(pairs),'source_groups':len({s['seed'] for s,b,r in pairs}),
            'source_cases':len({s['case'] for s,b,r in pairs}),
            'baseline_wins':sum(b['win'] for s,b,r in pairs),'route_wins':sum(r['win'] for s,b,r in pairs),
            'flips':sum(r['win']>b['win'] for s,b,r in pairs),
            'regressions':sum(r['win']<b['win'] for s,b,r in pairs),
            'changed_futures':sum(bool(r['actions_changed']) for s,b,r in pairs),
            'first_changed':sum(r['first_changed'] for s,b,r in pairs),
            'later_changed':sum(r['later_changed'] for s,b,r in pairs),
            'shared_first_but_later_changed':sum(not r['first_changed'] and r['later_changed'] for s,b,r in pairs),
            'forced_coil_used_baseline':sum(b.get('forced_coil_used',False) for s,b,r in pairs),
            'forced_coil_used_route':sum(r.get('forced_coil_used',False) for s,b,r in pairs)}


def resource(s):
    if s is None:return None
    y,o=s['you'],s['opponent']
    return {'health':y['hero']['health']+y['hero'].get('armor',0),
            'enemy_health':o['hero']['health']+o['hero'].get('armor',0),
            'enemy_attack':sum(m['attack'] for m in o['board']),
            'own_attack':sum(m['attack'] for m in y['board']),
            'hand':[c['card_id'] for c in y['hand']],
            'weapon':y.get('weapon'),'own_board':[m['card_id'] for m in y['board']],
            'enemy_board':[m['card_id'] for m in o['board']]}


def main():
    manifest=json.loads((RUN/'early-sources/manifest.json').read_text())
    groups=defaultdict(list);examples=[];source_counts=Counter()
    for cid in manifest['cases']:
        source=json.loads((RUN/'early-sources'/(cid+'.json')).read_text())
        kind=source.get('kind','early');source_counts[kind]+=1
        for scenario in ['natural']+(['forced_coil'] if kind=='late_cheap_defense' else []):
            suffix='-forced_coil' if scenario=='forced_coil' else ''
            for sample in range(3):
                files={route:RUN/'early-labels'/f'{cid}-{sample}-{route}{suffix}.json' for route in source['routes']}
                rows={route:json.loads(path.read_text()) for route,path in files.items()}
                assert all(r.get('terminal') and not r.get('error') for r in rows.values())
                base=rows['baseline']
                for route,row in rows.items():
                    if route=='baseline':continue
                    assert base['audit_hidden']==row['audit_hidden'] and base['root_digest']==row['root_digest']
                    groups[(kind,scenario,route)].append((source,base,row))
                    if row['win']!=base['win']:
                        examples.append({'case':cid,'seed':source['seed'],'source_score':source['source_score'],
                            'kind':kind,'split':source['split'],'scenario':scenario,'sample':sample,'route':route,
                            'baseline_win':base['win'],'route_win':row['win'],
                            'first_changed':row['first_changed'],'later_changed':row['later_changed'],
                            'baseline_file':str(files['baseline'].relative_to(ROOT)),
                            'route_file':str(files[route].relative_to(ROOT)),
                            'root':resource(source['state']),
                            'baseline_endpoint':resource(base['endpoint']),'route_endpoint':resource(row['endpoint']),
                            'baseline_after_response':resource(base['after_response']),
                            'route_after_response':resource(row['after_response'])})
    out={'source_counts':dict(source_counts),'rows':[{'kind':k[0],'scenario':k[1],'route':k[2],**stats(v)} for k,v in sorted(groups.items())],
         'change_metric':'At each actual observed state, compare route action with a fresh frozen-parent decision. Later changes are additional overrides after the root, not a line-by-line alignment of divergent trajectories.',
         'flips_and_regressions':examples,
         'limitations':'Only available routes compared; conditional source sampling is not a full-game population. Three futures per source are correlated. Natural late defense has two seed sources only. Forced Coil is mechanism stress, not natural improvement.'}
    train.atomic(ROOT/'docs/secret_hunter_final/label-audit.json',out)
    print(json.dumps({'sources':dict(source_counts),'route_summaries':len(out['rows']),'flips_and_regressions':len(examples)}))


if __name__=='__main__':main()
