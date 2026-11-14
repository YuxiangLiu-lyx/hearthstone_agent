"""Add independent late Amani opportunities, one root per original game."""
import json
import sqlite3
import sys
from development.secret_hunter_final.study import RUN,ROOT,HERE
from development.secret_hunter_final.counterfactual import digest
from development.secret_hunter_mcgs import train

def mine_coverage(db):
    from development.secret_hunter_final.early_routes import propose,features
    counts={'amani_states':0,'amani_risk':0,'cheap_defense_available':0};cases=[]
    for row in db.execute('select result from tasks where batch="dev-core" and candidate="B" and status="done" order by seed,opponent,seat'):
        r=json.loads(row[0]);folder=RUN/'batches/dev-core/B/games'/r['game']
        for z in map(json.loads,(folder/f'p{r["seat"]}/observations.jsonl').read_text().splitlines()):
            s=z['state']
            if s['phase']!='main':continue
            f=features(s)
            if not f['amani']:continue
            counts['amani_states']+=1
            if f['incoming']+3<f['health']:continue
            counts['amani_risk']+=1;a=propose(s,'cheap_defense',{},z['action'])
            if a is None:continue
            counts['cheap_defense_available']+=1
            cases.append({'seed':r['seed'],'seat':r['seat'],'opponent':r['opponent'],'seq':s['seq'],
                          'mana':f['mana'],'action':a,'baseline':z['action'],'score':r['score']})
    return {'counts':counts,'cases':cases}

def main():
    sys.path.insert(0,str(HERE/'candidates/B/scripts'))
    from development.secret_hunter_final.early_routes import propose,features
    db=train.connect(RUN);coverage=mine_coverage(db)
    path=RUN/'natural-amani-coverage.json'
    if path.exists():assert coverage==json.loads(path.read_text()),'source coverage changed'
    else:train.atomic(path,coverage)
    selected={};pop={o['name']:o for o in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
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
