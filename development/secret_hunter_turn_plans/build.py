"""Immutable candidate snapshots; missing historical code is never impersonated."""
import json
from pathlib import Path
import shutil
from development.secret_hunter_program.common import ROOT,sha
from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check

HERE=Path(__file__).resolve().parent
Y1=ROOT/'development/secret_hunter_dgm/candidates/Y1'


def build(name,settings,parent='Y1',source=None):
    target=HERE/'candidates'/name
    if target.exists():raise FileExistsError(target)
    shutil.copytree(source or Y1,target,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    scripts=target/'scripts';(scripts/'program_policy.py').rename(scripts/'parent_policy.py')
    for src,dest in [('policy.py','program_policy.py'),('routes.py','turn_routes.py'),('cache.py','continuation_cache.py')]:
        shutil.copyfile(HERE/src,scripts/dest)
    cfg=json.loads((target/'config.json').read_text());cfg.update(version=name,parent=parent,**settings)
    # The frozen warm-policy harness forwards memory only with this flag. The
    # wrapper disables the legacy cache internally, then uses the corrected one.
    cfg['plan_cache']=bool(cfg.get('continuation_memory'))
    (target/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    audit=check(target)
    return {'name':name,'parent':parent,'path':str(target.relative_to(ROOT)),
            'settings':settings,'sha256':fingerprint(target),'deck_audit':audit}


if __name__=='__main__':
    specs=[('R0-trap-reference',{'route_contexts':['trap']},'Y1'),
           ('R1-memory',{'route_contexts':['trap'],'continuation_memory':True},'R0-trap-reference'),
           ('R2-context',{'route_contexts':['trap','knife_wolf','amani'],'continuation_memory':True,
                          'route_weights':{'knife':1.5,'amani':8,'reserve':0}},'R1-memory'),
           ('R3-reserve',{'route_contexts':['trap','knife_wolf','amani'],'continuation_memory':True,
                          'route_weights':{'knife':.7,'amani':5,'reserve':2}},'R1-memory')]
    rows=[build(*spec) for spec in specs]
    (HERE/'lineage.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
