"""Package the validated Zoo branch; never replace the Paladin release or v6 ZIP."""
import hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from hs_arena.deck import validate_deck_data
from development.benchmarks.run import fingerprint
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'development/candidates/v7-zoo-strength'
FILES=['SKILL.md','config.json','deck.json','scripts/actions.py','scripts/decide.py',
       'scripts/evaluator.py','scripts/base_policy.py','scripts/policy.py','scripts/zoo_combat.py']

def main():
    protected=json.loads((ROOT/'development/reports/zoo-v7-protected-before.json').read_text())
    for name,digest in protected.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    selection=json.loads((ROOT/'development/reports/zoo-v7-selection.json').read_text())
    holdout=json.loads((ROOT/'development/experiments/zoo-v7-holdout-strength/manifest.json').read_text())
    assert selection['sha256']==fingerprint(SOURCE)==holdout['candidate_sha256']
    assert fingerprint(SOURCE)==fingerprint(ROOT/'development/checkpoints/v7-zoo-strength')
    assert json.loads((ROOT/'development/reports/zoo-v7-holdout-comparison.json').read_text())['gate_pass']
    assert not validate_deck_data(json.loads((SOURCE/'deck.json').read_text()))
    for original,candidate in [('policy.py','base_policy.py'),('actions.py','actions.py'),('decide.py','decide.py'),('evaluator.py','evaluator.py')]:
        assert (ROOT/'submission/hearthstone-agent/scripts'/original).read_bytes()==(SOURCE/'scripts'/candidate).read_bytes()
    out=ROOT/'dist/hearthstone-zoo-strength.zip';hashes={}
    with ZipFile(out,'w',compression=ZIP_DEFLATED) as z:
        for name in FILES:
            data=(SOURCE/name).read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
            info=ZipInfo('hearthstone-agent/'+name,date_time=(2026,11,10,0,0,0))
            info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
    with ZipFile(out) as z:
        assert z.testzip() is None
        size=sum(i.file_size for i in z.infolist());assert len(z.infolist())==len(FILES)
    report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':fingerprint(SOURCE),
            'artifact':str(out.relative_to(ROOT)),'status':'validated_zoo_branch_main_champion_unchanged',
            'files':hashes,'zip_bytes':out.stat().st_size,'uncompressed_bytes':size,
            'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
            'protected_files_unchanged':len(protected),'fresh_llm_validation':False}
    (ROOT/'development/reports/zoo-v7-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
if __name__=='__main__':main()
