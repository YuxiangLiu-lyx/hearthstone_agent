"""Supplement Python-code pins with course data and dependency provenance."""
import importlib.metadata
import json
from pathlib import Path
import time
import hs_arena
from development.secret_hunter_final.study import ROOT,RUN
from development.secret_hunter_program.common import sha
from development.secret_hunter_mcgs import train


def check():
    path=RUN/'engine-data-freeze.json'
    if path.exists():
        data=json.loads(path.read_text())
        assert all(sha(Path(p))==h for p,h in data['files'].items())
        assert all(importlib.metadata.version(name)==version for name,version in data['versions'].items())
        return data
    installed=Path(hs_arena.__file__).parent;distribution=ROOT/'hs-arena-0.2.2/src/hs_arena'
    files={};matched=[]
    for p in sorted(installed.rglob('*')):
        if not p.is_file() or p.suffix not in ('.json','.xml','.txt'):continue
        files[str(p)]=sha(p);original=distribution/p.relative_to(installed)
        if original.exists():
            assert sha(original)==files[str(p)],p
            matched.append(str(p.relative_to(installed)))
    data={'created':time.time(),'files':files,'distribution_byte_matches':matched,
          'versions':{name:importlib.metadata.version(name) for name in ['hs-arena','hearthstone','hearthstone-data']},
          'scope':'Supplemental resource audit before final opening; Python code and opponents were pinned before the first new game. Installed resource bytes match the retained course distribution wherever present.'}
    train.atomic(path,data);return data


if __name__=='__main__':
    d=check();print(json.dumps({'resource_files':len(d['files']),'distribution_matches':len(d['distribution_byte_matches']),'versions':d['versions']}))
