"""Validate actual CLI deck envelopes with the course deck validator."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from hs_arena.deck import deck_from_ids
from development.benchmarks.run import fingerprint
from development.secret_hunter_turn_plans.build import HERE,Y1
from development.secret_hunter_turn_plans.study import ROOT


def main():
    expected=json.loads((Y1/'deck.json').read_text());rows=[]
    for name in ('Y1','engine-trap-v2','engine-trap-commit-v3','E2-finish-minions','E3-verified-plans','E4-trap-continuation'):
        source=Y1 if name=='Y1' else HERE/'candidates'/name
        with tempfile.TemporaryDirectory(prefix='krush-deck-') as tmp:
            skill=Path(tmp)/'skill'
            shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
            (skill/'game').mkdir()
            state={'phase':'deck_submission','seq':901,'game_id':'deck-audit'}
            (skill/'game/state.json').write_text(json.dumps(state))
            start=time.monotonic()
            run=subprocess.run([sys.executable,'scripts/decide.py'],cwd=skill,text=True,capture_output=True,check=True,timeout=2)
            elapsed=time.monotonic()-start;answer=json.loads(run.stdout);action=answer['action']
            assert answer['seq']==state['seq'] and action=={'type':'submit_deck','hero_class':expected['hero_class'],'cards':expected['cards']}
            deck_from_ids(action['hero_class'],action['cards'])
            log=json.loads((skill/'scratch/decisions.jsonl').read_text().splitlines()[-1])
            assert not log.get('worker_error') and elapsed<2
            rows.append({'candidate':name,'code_fingerprint':fingerprint(source),'envelope':answer,
                'valid':True,'validator':'hs_arena.deck.deck_from_ids','ordered_deck_exact':True,
                'elapsed_s':elapsed,'worker_error':log.get('worker_error'),
                'startup_fallback_flag':log['info'].get('fallback'),
                'note':'Deck submission intentionally uses the prepared fixed-deck path without a search worker. The in-game action validator excludes submit_deck and is not a deck validator.'})
    (ROOT/'docs/secret_hunter_turn_plans/actual-deck-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'n':len(rows),'course_valid':sum(r['valid'] for r in rows),
                      'max_cli_s':max(r['elapsed_s'] for r in rows)}))


if __name__=='__main__':main()
