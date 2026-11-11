"""Audit actual ZIP reproduction and the no-model official client transport."""
import json

from development.secret_hunter_program.common import ROOT, write, readlines
from development.secret_hunter_program.relay_audit import audit
from development.teacher_eval.compare import index


def main():
    source=ROOT/'experiments/teacher-d1-confirmation'
    extracted=ROOT/'experiments/teacher-d1-zip-reproduction'
    a=index(readlines(source/'results.jsonl'));b=index(readlines(extracted/'results.jsonl'))
    assert len(b)==24 and b.keys()<=a.keys()
    same_outcomes=traces=0;details=[]
    for key,row in sorted(b.items()):
        original=a[key]
        same=all(original['result'][field]==row['result'][field] for field in ('winner','reason','turns','first_player'))
        same_outcomes+=same
        paths=[folder/'games'/r['game']/f'p{r["seat"]}'/'observations.jsonl' for folder,r in ((source,original),(extracted,row))]
        actions=[[record['action'] for record in readlines(path)] for path in paths]
        exact=actions[0]==actions[1];traces+=exact
        details.append({'pair':key,'same_outcome':same,'same_action_trace':exact,'decisions':[len(t) for t in actions]})
    report={'games':len(b),'same_outcomes':same_outcomes,'same_action_traces':traces,'details':details,
            'scope':'Previously used confirmation seeds; exact-ZIP reproducibility only, not additional independent evidence.'}
    write(ROOT/'docs/teacher_eval/zip-reproduction.json',report)
    clients=[audit(game,1) for game in sorted((ROOT/'experiments/teacher-d1-client').glob('g_*'))
             if (game/'result.json').exists()]
    assert len(clients)==2 and all(r['decisions'] and not r['relay_deviations'] and not r['worker_errors'] and not r['fallbacks'] for r in clients)
    assert all(not any(r['result']['illegal_counts'].values()) and not any(r['result']['timeouts'].values()) for r in clients)
    client={'games':len(clients),'decisions':sum(r['decisions'] for r in clients),
            'relay_deviations':sum(r['relay_deviations'] for r in clients),'reports':clients,
            'scope':'Official local no-model client, not Astra or a model-host test.'}
    write(ROOT/'docs/teacher_eval/client-audit.json',client)
    print(json.dumps({k:v for k,v in report.items() if k!='details'}))
    print(json.dumps({k:v for k,v in client.items() if k!='reports'}))


if __name__=='__main__':
    main()
