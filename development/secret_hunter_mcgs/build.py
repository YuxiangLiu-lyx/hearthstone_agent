"""Immutable candidate snapshots. Every build checks the ordered original deck."""
import json
from pathlib import Path
import shutil
from development.secret_hunter_dgm.deck_guard import check
from development.secret_hunter_program.common import ROOT, sha
from development.benchmarks.run import fingerprint

HERE=Path(__file__).resolve().parent
Y1=ROOT/'development/secret_hunter_response/candidates/Y1'


def build(name,settings,parent='Y1'):
    target=HERE/'candidates'/name
    if target.exists():
        raise FileExistsError('Candidate snapshots are immutable: '+str(target))
    staging=target.with_name(target.name+'.building')
    if staging.exists():shutil.rmtree(staging)
    shutil.copytree(Y1,staging,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    scripts=staging/'scripts'
    (scripts/'program_policy.py').rename(scripts/'y1_policy.py')
    shutil.copyfile(HERE/'adapter.py',scripts/'program_policy.py')
    for source in list(HERE.glob('mcgs_*.py'))+[HERE/'course_cards.json.gz']:
        shutil.copyfile(source,scripts/source.name)
    cfg=json.loads((staging/'config.json').read_text())
    cfg.update(version=name,parent=parent,mcgs=settings)
    (staging/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    check(staging)
    staging.rename(target)
    return {'name':name,'parent':parent,'path':str(target.relative_to(ROOT)),
            'sha256':fingerprint(target),'settings':settings,
            'deck_sha256':sha(target/'deck.json')}


if __name__=='__main__':
    base={'budget_s':1.3,'max_transitions':350,'horizon':3,'min_visits':2,'margin':.06,'iterations':100}
    variants=[('M0-uct',{'graph':'uct','chance':'fixed'}),
              ('M1-fixed',{'graph':'ucd','chance':'fixed'}),
              ('M2-dpw',{'graph':'ucd','chance':'dpw'})]
    rows=[build(n,{**base,**v}) for n,v in variants]
    (HERE/'lineage.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
