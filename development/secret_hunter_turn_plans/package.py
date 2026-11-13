"""Export byte-identical frozen skills, without environments or experiment data."""
import hashlib
import json
import subprocess
import sys
import tempfile
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

from development.benchmarks.run import fingerprint
from development.secret_hunter_turn_plans.build import HERE
from development.secret_hunter_turn_plans.study import ROOT,RUN


def main():
    freeze=json.loads((RUN/'final-freeze.json').read_text())
    dest=ROOT/'dist/secret-hunter-turn-plans';dest.mkdir(parents=True,exist_ok=True)
    records=[]
    for name in ('engine-trap-v2','E2-finish-minions'):
        source=HERE/'candidates'/name
        assert fingerprint(source)==freeze['fingerprints'][name]
        path=dest/(name+'.zip')
        with ZipFile(path,'w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
            for p in sorted(source.rglob('*')):
                if not p.is_file() or '__pycache__' in p.parts or p.suffix not in ('.py','.json','.md'):continue
                member=ZipInfo('secret-hunter/'+p.relative_to(source).as_posix(),(1980,1,1,0,0,0))
                member.compress_type=ZIP_DEFLATED;member.external_attr=0o644<<16
                archive.writestr(member,p.read_bytes())
        assert path.stat().st_size<=10_000_000
        with tempfile.TemporaryDirectory(prefix='krush-package-') as tmp:
            from pathlib import Path
            with ZipFile(path) as archive:archive.extractall(tmp)
            assert fingerprint(Path(tmp)/'secret-hunter')==freeze['fingerprints'][name]
            validation=subprocess.run([sys.executable,'-c','from hs_arena.cli import main; main()',
                'validate','--no-game',str(Path(tmp)/'secret-hunter')],text=True,capture_output=True,check=True)
        records.append({'candidate':name,'path':str(path.relative_to(ROOT)),
            'bytes':path.stat().st_size,'zip_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'candidate_fingerprint':freeze['fingerprints'][name],
            'single_skill_folder':True,'unpacked_fingerprint_matches':True,
            'course_static_validation':validation.stdout.strip(),
            'status':'Frozen comparison artifact. Recommendation is in REPORT.md; packaging is not promotion.'})
    (dest/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
