"""Build deterministic ZIP, extract it, and validate the actual submission contents."""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-dir',default='development/secret_hunter_es/release')
    parser.add_argument('--source',default='development/secret_hunter_es/package/secret-hunter-program')
    parser.add_argument('--artifact',default='secret-hunter-es')
    args=parser.parse_args()
    src=ROOT/args.source;destination=ROOT/'dist'/f'{args.artifact}.zip'
    extracted=ROOT/args.freeze_dir
    assert not extracted.exists(),'Do not overwrite a frozen release'
    files=[p for p in sorted(src.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'scratch' not in p.parts and 'game' not in p.parts]
    assert all(p.suffix in ('.py','.md','.json') for p in files)
    imports=set()
    for p in files:
        if p.suffix=='.py':
            for n in ast.walk(ast.parse(p.read_text())):
                if isinstance(n,ast.Import):imports.update(a.name.split('.')[0] for a in n.names)
                if isinstance(n,ast.ImportFrom) and n.module:imports.add(n.module.split('.')[0])
    local={p.stem for p in files if p.suffix=='.py'}
    assert imports<=set(sys.stdlib_module_names)|local|{'hs_arena'},imports-(set(sys.stdlib_module_names)|local|{'hs_arena'})
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            info=zipfile.ZipInfo(str(Path(src.name)/p.relative_to(src)),date_time=(2026,11,11,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(destination) as z:
        assert {p.split('/')[0] for p in z.namelist()}=={'secret-hunter-program'}
        assert all('..' not in Path(p).parts for p in z.namelist())
        unpacked=sum(i.file_size for i in z.infolist());assert max(unpacked,destination.stat().st_size)<10_000_000
        z.extractall(extracted)
    tree=extracted/src.name
    assert fingerprint(tree)==fingerprint(src)
    output=subprocess.run([str(ROOT/'.venv/bin/hs-arena'),'validate',str(tree),'--no-game'],capture_output=True,text=True,check=True)
    (ROOT/'docs/secret_hunter_es'/f'{args.artifact}-extracted-validation.txt').write_text(output.stdout+output.stderr)
    from hs_arena.deck import validate_deck_data
    assert validate_deck_data(json.loads((tree/'deck.json').read_text()))==[]
    m={'status':'Frozen program strategy; champion status is governed separately by final paired and reliability evidence.',
       'zip':str(destination.relative_to(ROOT)),'zip_sha256':sha(destination),'zip_bytes':destination.stat().st_size,
       'unpacked_bytes':unpacked,'candidate_sha256':fingerprint(tree),'deck_sha256':sha(tree/'deck.json'),
       'config_sha256':sha(tree/'config.json'),'files':{str(p.relative_to(src)):sha(p) for p in files},
       'extracted':str(tree.relative_to(ROOT)),'imports':sorted(imports),'runtime_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/runtime.json'),
       'opponent_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json')}
    write(ROOT/'dist'/f'{args.artifact}.manifest.json',m);print(json.dumps({k:v for k,v in m.items() if k!='files'}))


if __name__=='__main__':main()
