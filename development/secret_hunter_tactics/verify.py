"""Verify preserved champion, runtime/opponents, release bytes and public inputs."""
import json,zipfile
from pathlib import Path
import hs_arena
from development.secret_hunter_program.common import ROOT,sha,write,readlines
from development.benchmarks.run import fingerprint
O=ROOT/'docs/secret_hunter_tactics'
freeze=json.loads((O/'freeze.json').read_text());manifest=json.loads((ROOT/'dist/secret-hunter-tactics.manifest.json').read_text())
assert sha(ROOT/manifest['zip'])==manifest['zip_sha256']
assert fingerprint(ROOT/manifest['extracted'])==fingerprint(ROOT/'development/secret_hunter_tactics/package/secret-hunter-program')==manifest['candidate_sha256']
protected=dict(freeze['protected'])
for path in ['docs/secret_hunter_program/protected-before.json','docs/secret_hunter/protected-before.json']:
 protected.update(json.loads((ROOT/path).read_text()))
archive=json.loads((O/'archive.json').read_text()) if (O/'archive.json').exists() else None
for name,digest in protected.items():
 target=name
 if archive:
  for old,new in archive['protected_path_mapping'].items():
   if name==old or (old.endswith('/') and name.startswith(old)):target=new+name[len(old):];break
 assert sha(ROOT/target)==digest,(name,target)
baseline_path=ROOT/'development/secret_hunter_tactics/previous-champion/secret-hunter-program' if archive else ROOT/'secret-hunter-program'
if archive:
 marker=json.loads((ROOT/'SECRET_HUNTER_CHAMPION.json').read_text())
 assert fingerprint(ROOT/'secret-hunter-program')==manifest['candidate_sha256']==marker['source_sha256']
 assert sha(ROOT/'dist/secret-hunter-program.zip')==manifest['zip_sha256']==marker['zip_sha256']
runtime=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text());base=Path(hs_arena.__file__).parent
for name,digest in runtime['installed_files'].items():assert sha(base/name)==digest,name
opponents=json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())
assert sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json')==freeze['opponent_manifest_sha256']
assert sha(ROOT/opponents['population'])==opponents['population_sha256']
for o in opponents['opponents']:
 assert sha(ROOT/o['deck'])==o['deck_sha256']
 for name,digest in o['dependencies'].items():
  if not name.startswith('installed:'):assert sha(ROOT/name)==digest,name
with zipfile.ZipFile(ROOT/manifest['zip']) as z:
 assert sum(p.file_size for p in z.infolist())<10_000_000
 assert {p.split('/')[0] for p in z.namelist()}=={'secret-hunter-program'}
 for name,digest in manifest['files'].items():assert sha(ROOT/manifest['extracted']/name)==digest
observations=0
for entry in json.loads((O/'budget.json').read_text())['runs']:
 if entry['mode']!='python':continue
 folder=ROOT/entry['out'];cfg=json.loads((folder/'config.json').read_text())
 assert fingerprint(ROOT/cfg['candidate'])==cfg['candidate_sha256']
 for r in readlines(folder/'results.jsonl'):
  for z in readlines(folder/'games'/r['game']/f'p{r["seat"]}/observations.jsonl'):
   s=z['state'];assert not any(k in s for k in ('seed','rng','opponent_id','opponent_name','opponent_policy','engine'))
   assert 'hand' not in s['opponent'] and 'deck' not in s['opponent'];assert s.get('game_id')==r['game']
   observations+=1
report={'status':'H7 promoted; F2 preserved byte-for-byte in explicit archives' if archive else 'F2 champion and ZIP preserved; research ZIP frozen separately',
 'protected_files_unchanged':len(protected),'runtime_files_unchanged':len(runtime['installed_files']),
 'opponents_unchanged':len(opponents['opponents']),'public_observations_checked':observations,
 'research_zip_sha256':manifest['zip_sha256'],'baseline_tree_unchanged':fingerprint(baseline_path)==freeze['baseline_sha256']}
write(O/'verification.json',report);print(json.dumps(report))
