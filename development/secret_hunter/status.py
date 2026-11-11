"""Read-only progress without inspecting held-out strategy outcomes."""
import json
from pathlib import Path
from development.secret_hunter.bootstrap import ROOT

ledger=json.loads((ROOT/'docs/secret_hunter/budget.json').read_text())
planned={Path(r['out']).name:r['reserved'] for r in ledger['runs']}
for name in ('secret-c4-model-confirmation','secret-c4-ablation-confirmation','secret-c5-model-confirmation','secret-c5-ablation-confirmation','secret-c4-zip-cli-smoke','secret-c5-zip-cli-smoke','secret-c4-skill-fault'):
    folder=ROOT/'experiments'/name
    paths=list(folder.glob('games/*/result.json'))+list(folder.glob('g_*/result.json'))
    complete=[json.loads(p.read_text()) for p in paths]
    active=[]
    for transcript in list(folder.glob('games/*/p*/seat/session_1.jsonl'))+list(folder.glob('g_*/p*/seat/session_1.jsonl')):
        game=transcript.parents[2]
        if (game/'result.json').exists():continue
        events=[json.loads(s) for s in transcript.read_text().splitlines() if s]
        seq=max((r['item']['arguments'].get('seq',0) for r in events if r.get('type')=='item.completed' and r.get('item',{}).get('tool')=='act'),default=0)
        active.append(seq)
    print(json.dumps({'run':name,'completed':len(complete),'active_last_seq':active,
                      'forfeits':sum(r['reason'].startswith('forfeit') for r in complete),
                      'planned':planned.get(name),'complete':len(complete)==planned.get(name)}))
