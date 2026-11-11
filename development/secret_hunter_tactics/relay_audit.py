"""Audit completed host games and explicitly separate an externally interrupted attempt."""
import json
from development.secret_hunter_program.common import ROOT,write,readlines
from development.secret_hunter_program.relay_audit import audit
folder=ROOT/'experiments/tactics-relay-smoke-confirmation';rows=readlines(folder/'results.jsonl')
reports=[audit(folder/'games'/r['game'],r['seat']) for r in rows]
partial=[]
for p in (folder/'games').glob('*/interruption.json'):
    event=json.loads(p.read_text());g=p.parent;seat=event['seat'];logs=readlines(g/f'p{seat}/seat/scratch/decisions.jsonl');byseq={r['seq']:r for r in logs}
    actual=[]
    for f in sorted((g/f'p{seat}/decisions').glob('*.action.json')):
        envelope=json.loads(f.read_text());record=byseq.get(envelope['seq'])
        actual.append({**envelope,'exact':bool(record and record['action']==envelope['action'])})
    calls=[c for c in readlines(g/f'p{seat}/seat/mcp_calls.jsonl') if c.get('tool')=='act']
    requests=[{'seq':c['arguments']['seq'],'exact':c['arguments']['seq'] in byseq and byseq[c['arguments']['seq']]['action']==c['arguments']['action']} for c in calls]
    partial.append({'interruption':event,'accepted_actions':len(actual),'accepted_deviations':sum(not x['exact'] for x in actual),
      'requested_actions':len(requests),'request_deviations':sum(not x['exact'] for x in requests),
      'worker_errors':[r['worker_error'] for r in logs if r.get('worker_error')],
      'fallbacks':sum(r['info'].get('fallback',False) for r in logs if r['phase']!='deck_submission'),
      'accepted_details':actual,'request_details':requests})
result={'games':len(reports),'attempts':len(reports)+len(partial),'decisions':sum(r['decisions'] for r in reports),
 'relay_deviations':sum(r['relay_deviations'] for r in reports),'reports':reports,'interrupted_attempts':partial,
 'scope':'One completed official host game and one externally interrupted attempt. Partial actions are audited but do not constitute a completed second host game or match outcome.'}
write(ROOT/'docs/secret_hunter_tactics/relay-audit.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('reports','interrupted_attempts')}))
for p in partial:print({k:v for k,v in p.items() if k not in ('accepted_details','request_details','interruption')})
