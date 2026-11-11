"""Reproducible, separate policy/deck hypotheses over the preserved H7 champion."""
import argparse
import json
from pathlib import Path
import shutil

from hs_arena.deck import validate_deck_data
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import ROOT, write


def make(name):
    assert name in ('C1','D1','C2','D2','D3')
    source=ROOT/'secret-hunter-program'
    target=ROOT/'development/teacher_eval/candidates'/name
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    config=json.loads((target/'config.json').read_text())
    changes=[]
    if name in ('C1','C2'):
        evaluator=target/'scripts/evaluator.py'
        text=evaluator.read_text()
        old='THREATS = {"NEW1_019":3,'
        assert text.count(old)==1
        evaluator.write_text(text.replace(old,'THREATS = {"EX1_597":2.0,"NEW1_019":3,'))
        config.update(turn_board=1.30,protection_weight=.85,hidden_burst_buffer=5)
        changes.append('Value visible Imp Master recurring summons; favor protected board and larger hidden-burst reserve.')
    if name in ('D1','C2','D2','D3'):
        deck=json.loads((target/'deck.json').read_text())
        removed={'D1':('EX1_543','EX1_533'),'C2':('EX1_543','EX1_533'),
                 'D2':('EX1_533',),'D3':('EX1_543',)}[name]
        for cid in removed:
            deck['cards'].remove(cid)
        deck['cards']+=['DS1_185']*len(removed)
        assert not validate_deck_data(deck)
        write(target/'deck.json',deck)
        changes.append('Replace '+', '.join(removed)+' with '+str(len(removed))+' Arcane Shot(s); all other cards unchanged.')
    config.update(version='teacher-'+name,parent='H7')
    write(target/'config.json',config)
    write(ROOT/'docs/teacher_eval'/f'{name}.json',{'candidate':str(target.relative_to(ROOT)),
          'parent_sha256':fingerprint(source),'candidate_sha256':fingerprint(target),
          'hypotheses':changes,'status':'unselected research candidate'})
    print(target.relative_to(ROOT))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('name',choices=['C1','D1','C2','D2','D3'])
    make(parser.parse_args().name)
