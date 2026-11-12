"""Frozen local response models on formal C2 games; no online model loading."""
import json,sys
from development.secret_hunter_mcgs.build import ROOT,Y1
sys.path.insert(0,str(Y1/'scripts'))
from state_features import with_public_history
from development.secret_hunter_response.data import public_features,labels,LABELS
from development.secret_hunter_response.calibrate import predict,metrics

def main():
    rows=[json.loads(l) for l in (ROOT/'runs/krush-mcgs/submission2/responses.jsonl').read_text().splitlines()]
    data=[]
    for r in rows:
        s=with_public_history(r['state'],r['history']);seat=s['player']
        # Only the next opponent turn is labelled; own next-turn draws are ignored.
        if not any(e['event']=='turn_start' and e['player']!=seat for e in r['public_response']):continue
        data.append({'features':public_features(s),'labels':labels(r['public_response'],seat,s['you']['hero']['entity_id']),
                     'group':r['source_game'],'opponent':r['audit']['opponent']})
    base=ROOT/'docs/secret_hunter_response';models=json.loads((base/'models-offline-only.json').read_text())
    bigram=json.loads((base/'bigram-filtered-offline.json').read_text());result={}
    for mode,model in models.items():
        ps=[predict(model['weights'],r,mode,bigram,model['temperature']) for r in data]
        result[mode]={'all':metrics(data,ps),'by_opponent':{o:metrics([r for r in data if r['opponent']==o],[p for r,p in zip(data,ps) if r['opponent']==o]) for o in sorted({r['opponent'] for r in data})}}
    out={'response_windows':len(data),'game_groups':len({r['group'] for r in data}),'results':result,
         'scope':'Frozen models fitted on prior local Y1 seed groups; external formal C2 transfer audit. No refitting on these 14 games, no hand-possession labels. Not an original-deck win-rate experiment.'}
    (ROOT/'docs/secret_hunter_mcgs/response-transfer.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'n':len(data),'brier':{k:v['all']['macro_brier'] for k,v in result.items()}}))
if __name__=='__main__':main()
