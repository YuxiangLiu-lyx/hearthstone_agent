"""Freeze selected policy and baseline before opening final seeds."""
import json,shutil
from datetime import datetime,timezone
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint


def main():
    root=ROOT/'secret-hunter-program';base=ROOT/'development/secret_hunter_program/candidates'
    chosen=json.loads((base/'V3-trained/config.json').read_text());chosen.update(version='F1-program-final',parent='V3-trained',plan_cache=False)
    write(root/'config.json',chosen)
    for name,parent in [('F1','F1'),('B1','B0')]:
        dest=base/name;shutil.copytree(root,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
        if name=='B1':
            cfg=json.loads((base/'B0/config.json').read_text());cfg.update(version='B1-program-final-baseline',parent='B0',plan_cache=False);write(dest/'config.json',cfg)
    write(ROOT/'docs/secret_hunter_program/final-freeze.json',{
        'frozen_utc':datetime.now(timezone.utc).isoformat(),'selected':'F1','baseline':'B1','validation_parent':'V3-trained',
        'selection_reason':'Highest validation primary macro, Greedy no regression. T1 local training adds one validation win beyond untuned search. New scoring, secret rules and continuation reuse are disabled because they did not add stable benefit.',
        'engineering_changes_after_validation':'Identical action logic; cooperative deadline checks added to bounded ranking loops, optional disabled plan cache retained, public phase API and supervised runtime shared by both arms. Changes receive final confirmation.',
        'candidate_sha256':fingerprint(base/'F1'),'baseline_sha256':fingerprint(base/'B1'),
        'candidate_config_sha256':sha(base/'F1/config.json'),'baseline_config_sha256':sha(base/'B1/config.json'),
        'deck_sha256':sha(root/'deck.json'),'opponents_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),
        'seeds':json.loads((ROOT/'docs/secret_hunter_program/splits.json').read_text())['confirmation'],
        'promotion_gate':'Positive primary paired 95% seed-cluster interval, at least +2 percentage points, no own illegal/timeouts/forfeits/errors, measured supervised maximum <2s, exact final relay smoke if available. Otherwise preserve baseline.'})
    print('Frozen F1 and B1')
if __name__=='__main__':main()
