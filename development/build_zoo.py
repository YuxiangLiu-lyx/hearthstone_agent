"""Build the optional Zoo artifact without changing the champion or release ZIP."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from hs_arena.deck import validate_deck_data

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'development/candidates/v6-zoo-guide'
FILES = ['SKILL.md', 'config.json', 'deck.json', 'scripts/actions.py',
         'scripts/decide.py', 'scripts/evaluator.py', 'scripts/base_policy.py', 'scripts/policy.py']


def main():
    protected = json.loads((ROOT/'development/reports/zoo-protected-before.json').read_text())
    for name, digest in protected.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    assert not validate_deck_data(json.loads((SOURCE/'deck.json').read_text()))
    for original, candidate in [('policy.py','base_policy.py'), ('actions.py','actions.py'),
                                ('decide.py','decide.py'), ('evaluator.py','evaluator.py')]:
        assert (ROOT/'submission/hearthstone-agent/scripts'/original).read_bytes() == (SOURCE/'scripts'/candidate).read_bytes()
    out = ROOT/'dist/hearthstone-zoo-candidate.zip'
    hashes = {}
    with ZipFile(out, 'w', compression=ZIP_DEFLATED) as z:
        for name in FILES:
            data = (SOURCE/name).read_bytes()
            hashes[name] = hashlib.sha256(data).hexdigest()
            info = ZipInfo('hearthstone-agent/'+name, date_time=(2026,11,10,0,0,0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info,data)
    with ZipFile(out) as z:
        assert z.testzip() is None
        size = sum(x.file_size for x in z.infolist())
        assert len(z.infolist()) == len(FILES)
    manifest = {'source':str(SOURCE.relative_to(ROOT)), 'artifact':str(out.relative_to(ROOT)),
                'status':'optional_candidate_not_promoted', 'files':hashes,
                'zip_bytes':out.stat().st_size, 'uncompressed_bytes':size,
                'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
                'protected_files_unchanged':len(protected),
                'fresh_llm_validation':False}
    (ROOT/'development/reports/zoo-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))


if __name__ == '__main__':
    main()
