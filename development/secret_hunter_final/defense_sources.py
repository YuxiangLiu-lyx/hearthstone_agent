"""Add independent late Amani opportunities, one root per original game."""
import json
import sqlite3
import sys
from development.secret_hunter_final.study import RUN,ROOT,HERE
from development.secret_hunter_final.counterfactual import digest
from development.secret_hunter_mcgs import train

def main():
    sys.path.insert(0,str(HERE/'candidates/B/scripts'))
    from development.secret_hunter_final.early_routes import propose,features
    coverage=json.loads((RUN/'natural-amani-coverage.json').read_text())
    db=train.connect(RUN);selected={};pop={o['name']:o for o in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    for c in coverage['cases']:
        key=(c['opponent'],c['seed'],c['seat'])
        if key in selected or c['action'].get('target')==c['baseline'].get('target'):continue
        selected[key]=c
    manifest_path=RUN/'early-sources/manifest.json';manifest=json.loads(manifest_path.read_text())
    extra=[]
    for (name,seed,seat),c in selected.items():
        r=json.loads(db.execute('select result from tasks where batch="dev-core" and candidate="B" and seed=? and seat=? and json_extract(result,"$.opponent")=?',(seed,seat,name)).fetchone()[0])
        folder=RUN/'batches/dev-core/B/games'/r['game'];logs=[json.loads(x) for x in (folder/f'p{seat}/observations.jsonl').read_text().splitlines()]
        z=next(z for z in logs if z['state']['seq']==c['seq']);s=z['state']
        cid=f'{seed}-{name}-s{seat}-q{c["seq"]}-defense'
        routes=['baseline','cheap_defense']+[route for route in ('kill_amani','bow_amani','develop','preserve_burn','bank_tail') if propose(s,route,{},z['action']) is not None]
        source={'case':cid,'seed':seed,'seat':seat,'seq':s['seq'],'source_score':r['score'],
                'state':s,'state_digest':digest(s),'opponent_spec':pop[name],'game_path':str(folder.relative_to(ROOT)),
                'features':features(s),'split':'validation' if seed%5 in (0,1) else 'train',
                'routes':routes,'original_action':z['action'],'kind':'late_cheap_defense'}
        train.atomic(RUN/'early-sources'/(cid+'.json'),source);extra.append(cid)
    manifest['cases']=list(dict.fromkeys(manifest['cases']+extra));manifest['late_defense_cases']=extra
    manifest['late_defense_coverage']=coverage['counts'];train.atomic(manifest_path,manifest)
    print(json.dumps({'added':extra,'coverage':coverage['counts']}))

if __name__=='__main__':main()
