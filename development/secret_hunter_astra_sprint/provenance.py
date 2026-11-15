"""Content-addressed offline harness snapshots, separate from immutable skills."""
import hashlib
from pathlib import Path
from development.secret_hunter_program.common import ROOT
from development.secret_hunter_mcgs.train import atomic

def archive_code(run,paths):
    result={}
    for name in paths:
        raw=(ROOT/name).read_bytes();digest=hashlib.sha256(raw).hexdigest();path=run/'harness-by-sha'/(digest+'.json')
        if not path.exists():atomic(path,{'path':name,'sha256':digest,'utf8_source':raw.decode()})
        result[name]=digest
    return result
