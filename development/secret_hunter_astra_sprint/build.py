"""Build immutable candidates from the exact requested submission ZIP."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile
from development.secret_hunter_astra_sprint.study import HERE,RUN,ROOT,BASE_SHA,DECK_SHA,ZIP_SHA,deck_check
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_mcgs.train import atomic

def audit(source):
    check=deck_check(source)
    proc=subprocess.run([sys.executable,'-c','from hs_arena.cli import main; main()',
                         'validate','--no-game',str(source)],capture_output=True,text=True,check=True)
    with tempfile.TemporaryDirectory(prefix='long-deck-') as tmp:
        root=Path(tmp)/'skill';shutil.copytree(source,root,ignore=shutil.ignore_patterns('__pycache__'))
        (root/'game').mkdir();(root/'game/state.json').write_text(json.dumps({'phase':'deck_submission','seq':701,'game_id':'deck-audit'}))
        start=time.monotonic();out=subprocess.run([sys.executable,'scripts/decide.py'],cwd=root,capture_output=True,text=True,check=True,timeout=2)
        elapsed=time.monotonic()-start;envelope=json.loads(out.stdout)
        assert envelope=={'seq':701,'action':{'type':'submit_deck','hero_class':'HUNTER','cards':check['ordered_cards']}}
    return {'candidate':source.name,'fingerprint':fingerprint(source),**check,
            'static_validation':proc.stdout,'actual_submit_deck':envelope,'elapsed_s':elapsed,'valid':True}

def clone(name,parent,changes=None,edit=None,hypothesis='',generation=0):
    dest=HERE/'candidates'/name
    lineage_path=HERE/'lineage.json';lineage=json.loads(lineage_path.read_text()) if lineage_path.exists() else []
    if not dest.exists():
        shutil.copytree(HERE/'candidates'/parent,dest,ignore=shutil.ignore_patterns('__pycache__'))
        if changes:
            p=dest/'deck.json';d=json.loads(p.read_text())
            for old,new in changes:
                i=d['cards'].index(old);d['cards'][i]=new
            p.write_text(json.dumps(d,indent=2)+'\n')
        if edit:edit(dest)
        parent_path=HERE/'candidates'/parent
        changed=[str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and '__pycache__' not in str(p) and (not (parent_path/p.relative_to(dest)).exists() or sha(p)!=sha(parent_path/p.relative_to(dest)))]
        lineage.append({'name':name,'parent':parent,'sha256':fingerprint(dest),'created':time.time(),
                        'generation':generation,'hypothesis':hypothesis,'changed_files':changed,
                        'deck':deck_check(dest),'status':'unvalidated'})
        atomic(lineage_path,lineage)
    else:assert any(r['name']==name and r['sha256']==fingerprint(dest) for r in lineage)
    return dest

