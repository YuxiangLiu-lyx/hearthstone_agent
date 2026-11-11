"""Freeze and evaluate three independent loss-driven hypotheses."""
import json,shutil,subprocess,sys
from development.secret_hunter_program.common import ROOT,write
DEV=ROOT/'development/secret_hunter_es';DOC=ROOT/'docs/secret_hunter_es'
sys.path.insert(0,str(DEV/'working/scripts'))
from evolved_value import DEFAULT
for name,changes,hypothesis in [
 ('C1',{'evolved_features':False,'response_exposure':False},'Exact Secret, Houndmaster, Ooze, single-target Deadly Shot, and snake coverage with conditional Secret potential'),
 ('C2',{'evolved_features':True,'response_exposure':False},'21 interpretable end-turn feature weights including beast, mana, and Secret resources'),
 ('C3',{'evolved_features':True,'response_exposure':True},'Soft visible enemy attack exposure after taunt and shield capacity')]:
 dest=DEV/'candidates'/name
 assert not dest.exists();shutil.copytree(DEV/'working',dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
 cfg=json.loads((dest/'config.json').read_text());cfg.update(version=name,parent='F2',weights=DEFAULT,**changes)
 write(dest/'config.json',cfg)
 cmd=[sys.executable,'-m','development.secret_hunter_es.run','--candidate',str(dest.relative_to(ROOT)),
 '--out',f'experiments/es-{name.lower()}-screen','--start','78100','--seeds','4','--hypothesis',hypothesis]
 with open(f'/tmp/es-{name.lower()}-screen.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 summary=json.loads((ROOT/f'experiments/es-{name.lower()}-screen/summary.json').read_text())
 print(name,summary['primary']['wins'],summary['primary']['n'],summary['base']['wins'],flush=True)
