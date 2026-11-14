"""Validate frozen cards and exercise the actual deployment entrypoint."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from development.secret_hunter_final.study import HERE,RUN,ROOT,DECK_SHA
from development.benchmarks.run import fingerprint
from hs_arena.deck import deck_from_ids

def deck_audit(source):
    assert hashlib.sha256((source/'deck.json').read_bytes()).hexdigest()==DECK_SHA
    deck=json.loads((source/'deck.json').read_text());assert len(deck['cards'])==30
    deck_from_ids(deck['hero_class'],deck['cards'])
    proc=subprocess.run([sys.executable,'-c','from hs_arena.cli import main; main()',
                         'validate','--no-game',str(source)],capture_output=True,text=True,check=True)
    with tempfile.TemporaryDirectory(prefix='final-deck-') as tmp:
        root=Path(tmp)/'skill';shutil.copytree(source,root,ignore=shutil.ignore_patterns('__pycache__'))
        (root/'game').mkdir();(root/'game/state.json').write_text(json.dumps({'phase':'deck_submission','seq':701,'game_id':'deck-audit'}))
        start=time.monotonic();out=subprocess.run([sys.executable,'scripts/decide.py'],cwd=root,capture_output=True,text=True,check=True,timeout=2)
        dt=time.monotonic()-start;envelope=json.loads(out.stdout)
        assert envelope=={'seq':701,'action':{'type':'submit_deck','hero_class':deck['hero_class'],'cards':deck['cards']}}
        deck_from_ids(envelope['action']['hero_class'],envelope['action']['cards'])
    return {'candidate':source.name,'fingerprint':fingerprint(source),'deck_sha256':DECK_SHA,
            'static_validation':proc.stdout,'actual_submit_deck':envelope,'elapsed_s':dt,'valid':True}

def main():
    rows=[deck_audit(p) for p in sorted((HERE/'candidates').iterdir()) if p.is_dir()]
    (ROOT/'docs/secret_hunter_final/deck-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'validated_candidates':len(rows),'max_s':max(x['elapsed_s'] for x in rows)}))

if __name__=='__main__':main()
