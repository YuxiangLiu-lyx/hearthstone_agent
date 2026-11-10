"""Package the validated champion; fail closed on provenance, layout and runtime files."""
import ast
import hashlib
import json
import zipfile
from pathlib import Path
from hs_arena.skill.loader import load_skill
from hs_arena.deck import load_deck

ROOT=Path(__file__).resolve().parents[1]

def files(path):
    return {p.relative_to(path):p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}

def main():
    record=json.loads((ROOT/'development/checkpoints/CHAMPION.json').read_text())
    champion=ROOT/record['path'];submission=ROOT/'submission/hearthstone-agent'
    load_skill(submission);load_deck(submission/'deck.json')
    a,b=files(champion),files(submission)
    assert a.keys()==b.keys(),'Submission file set differs from champion'
    for name in a:assert a[name].read_bytes()==b[name].read_bytes(),f'Changed after validation: {name}'
    allowed={'json','argparse','sys','pathlib','subprocess','itertools','hs_arena','actions','evaluator','policy','planner','copy','time'}
    imports=set()
    for name,p in b.items():
        assert p.suffix in ('.py','.md','.json'),f'Unexpected file: {name}'
        assert not p.is_symlink(),'Symlinks are not shipped'
        if p.suffix=='.py':
            for node in ast.walk(ast.parse(p.read_text())):
                if isinstance(node,ast.Import):imports.update(x.name.split('.')[0] for x in node.names)
                if isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module.split('.')[0])
    assert imports<=allowed,imports-allowed
    size=sum(p.stat().st_size for p in b.values());assert size<10_000_000
    out=ROOT/'dist';out.mkdir(exist_ok=True);zip_path=out/'hearthstone-agent.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,p in sorted(b.items()):
            info=zipfile.ZipInfo('hearthstone-agent/'+name.as_posix(),date_time=(2026,11,10,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert {x.split('/')[0] for x in z.namelist()}=={'hearthstone-agent'}
        assert 'hearthstone-agent/SKILL.md' in z.namelist()
    report={'zip':str(zip_path),'zip_bytes':zip_path.stat().st_size,'uncompressed_bytes':size,
            'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'champion':record['champion'],
            'files':[str(x) for x in sorted(b)],'imports':sorted(imports)}
    (out/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
