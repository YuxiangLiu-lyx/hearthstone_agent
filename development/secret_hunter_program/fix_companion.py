"""Correct an unused chance helper and freeze a new untouched confirmation block."""
import json,shutil
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint


def main():
    root=ROOT/'secret-hunter-program';p=root/'scripts/tactical_model.py';s=p.read_text()
    assert '"NEW1_032": (4, 2, True, False)' in s and '"NEW1_034": (4, 4, False, True)' in s
    s=s.replace('"NEW1_032": (4, 2, True, False)','"NEW1_032": (4, 4, False, True)').replace('"NEW1_034": (4, 4, False, True)','"NEW1_034": (4, 2, True, False)');p.write_text(s)
    cfg=json.loads((root/'config.json').read_text());cfg.update(version='F2-companion-id-audit',parent='F1-program-final');write(root/'config.json',cfg)
    base=ROOT/'development/secret_hunter_program/candidates'
    shutil.copytree(root,base/'F2',ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    shutil.copy2(ROOT/'dist/secret-hunter-program.zip',ROOT/'dist/secret-hunter-program-f1.zip')
    shutil.copy2(ROOT/'dist/secret-hunter-program.manifest.json',ROOT/'dist/secret-hunter-program-f1.manifest.json')
    record={'frozen_utc':datetime.now(timezone.utc).isoformat(),'candidate':'F2','baseline':'B1','start':174000,'seeds':10,'seats':[1,2],
        'reason':'Engine inspection found swapped Misha/Huffer token identities in inherited optional chance enumeration. Active policy invokes only deterministic search and never options(random=True) or transition(companion=...). F2 corrects these token constants; weights and active choices are unchanged. Reconfirm on a new seed block, with no extra official model games.',
        'old_final_seeds_status':'F1 evidence preserved; now development for any changed strategy. F2 confirmation is reported separately.',
        'candidate_sha256':fingerprint(base/'F2'),'baseline_sha256':fingerprint(base/'B1'),'deck_sha256':sha(root/'deck.json'),'opponents_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),
        'promotion_gate':'Same predeclared gate: primary paired 95% interval strictly positive, gain at least 2 points, no own reliability defects and supervised target satisfied. Ten seed clusters give unstable intervals; disclose this.'}
    write(ROOT/'docs/secret_hunter_program/f2-freeze.json',record)
    print(json.dumps(record))
if __name__=='__main__':main()
