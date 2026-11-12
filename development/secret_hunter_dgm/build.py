"""Build a deterministic, competition-only ZIP from the already frozen candidate."""
import json,zipfile,subprocess
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write,sha
from development.benchmarks.run import fingerprint
D=ROOT/'docs/secret_hunter_dgm';freeze=json.loads((D/'final-freeze.json').read_text());src=ROOT/freeze['source']
from development.secret_hunter_dgm.deck_guard import check
check(src)
assert fingerprint(src)==freeze['source_sha256']
files=[src/n for n in ('SKILL.md','deck.json','config.json','client.py')]+sorted((src/'scripts').glob('*.py'))
assert not any('learned' in p.name for p in files)
dest=ROOT/freeze['zip'];extract=ROOT/'development/secret_hunter_dgm/release';assert not dest.exists() and not extract.exists()
with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:
  info=zipfile.ZipInfo((Path('secret-hunter-program')/p.relative_to(src)).as_posix(),date_time=(2026,11,11,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
with zipfile.ZipFile(dest) as z:
 unpacked=sum(i.file_size for i in z.infolist());assert unpacked<=10_000_000 and dest.stat().st_size<=10_000_000;z.extractall(extract)
tree=extract/'secret-hunter-program';check(tree);assert fingerprint(tree)==freeze['source_sha256']
r=subprocess.run([str(ROOT/'.venv/bin/hs-arena'),'validate',str(tree),'--no-game'],capture_output=True,text=True,check=True);(D/'zip-validation.txt').write_text(r.stdout+r.stderr)
manifest={'zip':str(dest.relative_to(ROOT)),'zip_sha256':sha(dest),'source':freeze['source'],'source_sha256':fingerprint(src),'extracted':str(tree.relative_to(ROOT)),'bytes':dest.stat().st_size,'unpacked_bytes':unpacked,'files':{p.relative_to(src).as_posix():sha(p) for p in files},'course_assignment_sha256':sha(D/'current-assignment.md'),'scope':'Frozen research candidate; promotion depends on decision.json. No official upload. H7/D1 old artifacts preserved.'}
write(dest.with_suffix('.manifest.json'),manifest);print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))
