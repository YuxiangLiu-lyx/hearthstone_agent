"""Read-only verification of the exact ZIP, extracted candidate and protected inputs."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import hs_arena
from hs_arena.deck import validate_deck_data
from development.benchmarks.run import fingerprint
from development.secret_hunter.bootstrap import ROOT, sha, write


def main():
    m=json.loads((ROOT/'dist/secret-hunter-agent.manifest.json').read_text())
    tree=ROOT/m['extracted'];archive=ROOT/m['zip']
    assert sha(archive)==m['zip_sha256']
    assert fingerprint(tree)==fingerprint(ROOT/'secret-hunter-agent')==m['candidate_sha256']
    with zipfile.ZipFile(archive) as z:
        assert {p.split('/')[0] for p in z.namelist()}=={'secret-hunter-agent'}
        assert len(z.namelist())==len(m['files'])
        assert sum(i.file_size for i in z.infolist())==m['unpacked_bytes']<10_000_000
        for name,digest in m['files'].items():
            assert sha(tree/name)==digest
            assert hashlib.sha256(z.read('secret-hunter-agent/'+name)).hexdigest()==digest
    assert archive.stat().st_size==m['zip_bytes']<10_000_000
    deck=json.loads((tree/'deck.json').read_text())
    expected='EX1_029 EX1_029 EX1_080 EX1_080 DS1_184 EX1_162 EX1_531 EX1_531 EX1_533 EX1_554 EX1_066 EX1_610 EX1_610 EX1_611 EX1_611 NEW1_019 NEW1_019 EX1_536 EX1_536 EX1_538 EX1_538 EX1_539 EX1_539 EX1_617 NEW1_031 NEW1_031 DS1_070 EX1_534 EX1_534 EX1_543'.split()
    assert Counter(deck['cards'])==Counter(expected) and deck['hero_class']=='HUNTER'
    assert not validate_deck_data(deck)
    imports=set();local={p.stem for p in tree.rglob('*.py')}
    for path in tree.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):imports.update(a.name.split('.')[0] for a in node.names)
            if isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module.split('.')[0])
    assert imports<=set(sys.stdlib_module_names)|local|{'hs_arena'}
    off=ROOT/'development/secret_hunter/ablation-C5/secret-hunter-agent'
    cfg=json.loads((tree/'config.json').read_text());off_cfg=json.loads((off/'config.json').read_text())
    assert {**cfg,'model_authority':False}==off_cfg
    for name,digest in m['files'].items():
        if name!='config.json':assert sha(off/name)==digest,name
    old=json.loads((ROOT/'dist/secret-hunter-c4-research.manifest.json').read_text())
    assert sha(ROOT/old['zip'])==old['zip_sha256']
    assert fingerprint(ROOT/old['extracted'])==old['candidate_sha256']
    protected=json.loads((ROOT/'docs/secret_hunter/protected-before.json').read_text())
    changed=[name for name,digest in protected.items() if sha(ROOT/name)!=digest]
    assert not changed,changed
    runtime=json.loads((ROOT/'docs/secret_hunter/runtime.json').read_text())
    installed=Path(hs_arena.__file__).parent
    assert all(sha(installed/name)==digest for name,digest in runtime['installed_files'].items())
    assert sha(ROOT/'docs/secret_hunter/runtime.json')==m['runtime_manifest_sha256']
    manifest=json.loads((ROOT/'docs/secret_hunter/opponent_manifest.json').read_text())
    assert sha(ROOT/'docs/secret_hunter/opponent_manifest.json')==m['opponent_manifest_sha256']
    for opponent in manifest['opponents']:
        assert sha(ROOT/opponent['deck'])==opponent['deck_sha256']
        for name,digest in opponent['dependencies'].items():
            path=installed/name.removeprefix('installed:hs_arena/') if name.startswith('installed:') else ROOT/name
            assert sha(path)==digest,name
    checked=subprocess.run([str(ROOT/'.venv/bin/hs-arena'),'validate',str(tree),'--no-game'],capture_output=True,text=True,check=True)
    (ROOT/'docs/secret_hunter/extracted-validation.txt').write_text(checked.stdout+checked.stderr)
    report={'protected_files':len(protected),'changed':changed,'root_equals_extracted':True,
            'candidate_sha256':m['candidate_sha256'],'zip_sha256':m['zip_sha256'],
            'installed_files_verified':len(runtime['installed_files']),'opponents_verified':len(manifest['opponents']),
            'deck_cards':len(expected),'single_root':True,'dependencies_allowed':True,
            'ablation_only_changes_authority':True,'C4_archive_preserved':True,
            'course_static_validator':'passed','scope':'Static integrity only; actual skill results are separate.'}
    write(ROOT/'docs/secret_hunter/protected-verification.json',report)
    print(json.dumps(report))


if __name__=='__main__':main()
