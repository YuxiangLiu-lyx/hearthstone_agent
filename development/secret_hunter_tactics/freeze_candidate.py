"""Immutable policy snapshots with explicit hypotheses and hashes."""
import json,shutil
from pathlib import Path
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
D=ROOT/'development/secret_hunter_tactics';DOC=ROOT/'docs/secret_hunter_tactics'

def freeze(name,overrides,hypothesis,parent='F2',source=None):
    dst=D/'candidates'/name
    assert not dst.exists(),dst
    shutil.copytree(source or D/'working',dst,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    cfg=json.loads((dst/'config.json').read_text());cfg.update(overrides,version=name,parent=parent)
    write(dst/'config.json',cfg)
    shutil.copy2(ROOT/'development/secret_hunter_es/relay-fix/secret-hunter-program/SKILL.md',dst/'SKILL.md')
    meta={'candidate':name,'hypothesis':hypothesis,'parent':parent,'source':str(source or D/'working'),
          'tree_sha256':fingerprint(dst),'config_sha256':sha(dst/'config.json'),'deck_sha256':sha(dst/'deck.json'),
          'opponent_manifest_sha256':sha(ROOT/'docs/secret_hunter_program/opponent_manifest.json'),'config':cfg}
    write(DOC/f'{name}.json',meta);return dst

if __name__=='__main__':
    h1={'combat_guides':True,'opening_plan':False,'race_plan':False,'public_response':False}
    freeze('H1',h1,'Exact lethal coverage and explicit combo/protection priorities, with guarded random follow-ups.')
    h2={**h1,'race_plan':True,'public_response':True}
    freeze('H2',h2,'Continuous face value, mana-constrained next-turn hand clock and visible attack/Secret response search.')
    freeze('H3',{**h2,'opening_plan':True},'Class-conditioned curve, supported Secret and Hounds mulligan on top of H2.',parent='H2')
