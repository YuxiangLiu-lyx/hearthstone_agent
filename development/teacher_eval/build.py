"""Package the frozen teacher candidate separately from the canonical H7 artifact."""
import json
from pathlib import Path
import subprocess
import zipfile

from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import ROOT, sha, write


def main():
    plan=json.loads((ROOT/'docs/teacher_eval/validation-plan.json').read_text())
    source=ROOT/plan['candidate']
    assert fingerprint(source)==plan['candidate_sha256']
    dest=ROOT/'dist/secret-hunter-teacher-d1.zip'
    extracted=ROOT/'development/teacher_eval/release'
    assert not dest.exists() and not extracted.exists(), 'Frozen artifacts must not be overwritten'
    files=[p for p in sorted(source.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
           and 'scratch' not in p.parts and 'game' not in p.parts]
    assert all(p.suffix in ('.py','.json','.md') for p in files)
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:
            name=(Path('secret-hunter-program')/p.relative_to(source)).as_posix()
            info=zipfile.ZipInfo(name,date_time=(2026,11,11,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,p.read_bytes())
    with zipfile.ZipFile(dest) as archive:
        assert all('..' not in Path(p).parts for p in archive.namelist())
        assert sum(i.file_size for i in archive.infolist())<10_000_000
        archive.extractall(extracted)
    tree=extracted/'secret-hunter-program'
    assert fingerprint(tree)==plan['candidate_sha256']
    result=subprocess.run([str(ROOT/'.venv/bin/hs-arena'),'validate',str(tree),'--no-game'],
                          capture_output=True,text=True,check=True)
    (ROOT/'docs/teacher_eval/zip-validation.txt').write_text(result.stdout+result.stderr)
    manifest={'zip':str(dest.relative_to(ROOT)),'zip_sha256':sha(dest),'source':plan['candidate'],
              'source_sha256':fingerprint(source),'extracted':str(tree.relative_to(ROOT)),
              'files':{p.relative_to(source).as_posix():sha(p) for p in files},
              'scope':'Teacher-informed local candidate, not an official submission; selection is in docs/teacher_eval/decision.json.'}
    write(ROOT/'dist/secret-hunter-teacher-d1.manifest.json',manifest)
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))


if __name__=='__main__':
    main()
