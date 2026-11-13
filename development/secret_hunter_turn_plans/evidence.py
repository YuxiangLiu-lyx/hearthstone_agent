"""Describe executed routes, grouped interventions, and exact replay evidence."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys

from development.secret_hunter_turn_plans.analyze_offline import effect
from development.secret_hunter_turn_plans.study import ROOT, RUN


def read_rows(folder):
    rows=[]
    for path in sorted(folder.glob('*.json')):
        if '.request.' in path.name:continue
        row=json.loads(path.read_text())
        if isinstance(row,dict) and row.get('terminal'):rows.append(row)
    return rows


def route_summary(rows):
    routes=defaultdict(dict)
    for row in rows:routes[row['route']][(row['case'],row['sample'])]=row
    if 'replan' not in routes:return {}
    result={}
    for name,route in sorted(routes.items()):
        result[name]=effect(routes['replan'],route)
        coverage=Counter()
        for row in route.values():
            seq=row['sequence']
            flags={
                'targeted_juggler':any(s['target']=='NEW1_019' for s in seq),
                'targeted_wolf':any(s['target']=='EX1_162' for s in seq),
                'targeted_amani':any(s['target']=='EX1_393' for s in seq),
                'hero_attacked_amani':any(s['action']['type']=='attack' and
                    (s['attacker'] or '').startswith('HERO_') and s['target']=='EX1_393' for s in seq),
                'played_highmane':any(s['card']=='EX1_534' for s in seq),
                'played_secretkeeper':any(s['card']=='EX1_080' for s in seq),
                'forced_coil_played':row['forced_coil_played'],
            }
            coverage.update({k:1 for k,v in flags.items() if v})
        result[name]['executed_coverage']=dict(coverage)
    return result


def main():
    rows=read_rows(RUN/'continuations-v4')
    stress=read_rows(RUN/'strict-coil-v2')
    sources={r['case']:r for p in (RUN/'mined-v4').glob('*.json')
             if p.name!='manifest.json' for r in [json.loads(p.read_text())]}
    strict_cases={r['case'] for r in stress}
    result={'scope':'Selected conditional course-engine continuations; not population win rates.',
            'route_label_warning':'Route names are search objectives. Coverage counts describe actual executed actions.',
            'amani':{},'knife_wolf':{},'unrescued':[], 'exact_replays':[]}
    for split in ('train','validation'):
        result['amani'][split]={}
        for scenario in ('no_coil','natural','forced_coil'):
            population=stress if scenario=='forced_coil' else rows
            subset=[r for r in population if r['kind']=='amani' and r['split']==split
                    and r['scenario']==scenario and r['case'] in strict_cases]
            result['amani'][split][scenario]=route_summary(subset)
        for label,condition in (
            ('all',lambda s:True),
            ('both_targets',lambda s:{'NEW1_019','EX1_162'}<={m['card_id'] for m in s['opponent']['board']}),
            ('no_current_hand_or_board_slot',lambda s:s['opponent'].get('hand_size',0)==0 or len(s['opponent']['board'])==7),
            ('has_current_hand_and_slot',lambda s:s['opponent'].get('hand_size',0)>0 and len(s['opponent']['board'])<7),
        ):
            subset=[r for r in rows if r['kind']=='knife_wolf' and r['split']==split
                    and r['scenario']=='natural' and condition(sources[r['case']]['state'])]
            result['knife_wolf'][split+'/'+label]=route_summary(subset)
    natural=[r for r in rows if r['scenario']=='natural']
    grouped=defaultdict(list)
    for row in natural:grouped[row['case']].append(row)
    for case,group in sorted(grouped.items()):
        if not any(r['win'] for r in group):
            result['unrescued'].append({'case':case,'source_seed':sources[case]['source_seed'],
                'routes':sorted({r['route'] for r in group}),
                'samples_per_route':len({r['sample'] for r in group})})
    # These examples were picked from development data before final evaluation.
    # Reproduce every public state and legal action, through the terminal winner.
    selected=[('recovered-golem-continuations','trap-replay-0-natural-0-replan'),
              ('recovered-golem-continuations','trap-replay-0-natural-0-committed'),
              ('continuations-v4','amani-h007-natural-0-replan'),
              ('continuations-v4','amani-h007-natural-0-bow_amani'),
              ('continuations-v4','amani-031-natural-0-replan'),
              ('continuations-v4','amani-031-natural-0-bow_amani')]
    for folder,name in selected:
        path=RUN/folder/(name+'.json')
        row=json.loads(path.read_text())
        completed=subprocess.run([sys.executable,'-m','development.secret_hunter_turn_plans.replay',str(path)],
                                 cwd=ROOT,text=True,capture_output=True,check=True,timeout=30)
        result['exact_replays'].append({'result':str(path.relative_to(RUN)),
            'verification':json.loads(completed.stdout),'executed_tested_turn':row['sequence'],
            'response':row['after_response']})
    out=ROOT/'docs/secret_hunter_turn_plans/continuation-evidence.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(out),'replays':len(result['exact_replays']),
                      'unrescued_cases':len(result['unrescued']),'strict_cases':len(strict_cases)}))


if __name__=='__main__':main()
