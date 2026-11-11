"""Read-only release, protected-file, runtime and public-input audit."""
import json,zipfile
from pathlib import Path
import hs_arena
from development.secret_hunter_program.common import ROOT,sha,write,readlines
from development.benchmarks.run import fingerprint


def main():
    doc=ROOT/'docs/secret_hunter_program';manifest=json.loads((ROOT/'dist/secret-hunter-program.manifest.json').read_text());src=ROOT/'secret-hunter-program';frozen=ROOT/manifest['extracted']
    assert sha(ROOT/manifest['zip'])==manifest['zip_sha256'];assert fingerprint(src)==fingerprint(frozen)==manifest['candidate_sha256']
    for name,digest in manifest['files'].items():assert sha(src/name)==sha(frozen/name)==digest,name
    with zipfile.ZipFile(ROOT/manifest['zip']) as z:
        assert len(z.namelist())==len(manifest['files'])
        assert sum(i.file_size for i in z.infolist())<10_000_000
    protected={}
    for p in [doc/'protected-before.json',ROOT/'docs/secret_hunter/protected-before.json']:
        protected.update(json.loads(p.read_text()))
    for name,digest in protected.items():assert sha(ROOT/name)==digest,name
    runtime=json.loads((doc/'runtime.json').read_text());base=Path(hs_arena.__file__).parent
    for name,digest in runtime['installed_files'].items():assert sha(base/name)==digest,name
    opponent=json.loads((doc/'opponent_manifest.json').read_text());assert sha(ROOT/opponent['population'])==opponent['population_sha256']
    for o in opponent['opponents']:
        assert sha(ROOT/o['deck'])==o['deck_sha256']
        for name,digest in o['dependencies'].items():
            if not name.startswith('installed:'):assert sha(ROOT/name)==digest
    f1=json.loads((ROOT/'dist/secret-hunter-program-f1.manifest.json').read_text());assert sha(ROOT/'dist/secret-hunter-program-f1.zip')==f1['zip_sha256']
    inputs=0
    for r in readlines(ROOT/'experiments/program-f2-confirmation/results.jsonl'):
        for z in readlines(ROOT/'experiments/program-f2-confirmation/games'/r['game']/f'p{r["seat"]}/observations.jsonl'):
            s=z['state'];assert not any(k in s for k in ('seed','rng','opponent_id','opponent_name','opponent_policy','engine'))
            assert 'hand' not in s['opponent'] and 'deck' not in s['opponent'];assert s.get('game_id')==r['game']
            inputs+=1
    result={'zip_sha256':manifest['zip_sha256'],'source_matches_zip':True,'frozen_source_matches':True,'protected_files_unchanged':len(protected),'runtime_files_unchanged':len(runtime['installed_files']),'opponents_unchanged':len(opponent['opponents']),'public_observations_checked':inputs,'archived_f1_zip_unchanged':True,'imports':manifest['imports']}
    write(doc/'verification.json',result);print(json.dumps(result))
if __name__=='__main__':main()
