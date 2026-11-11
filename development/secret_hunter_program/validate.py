"""Matched validation and real module ablations after development training."""
import json,shutil,subprocess,sys
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.compare import compare


def main():
    base=ROOT/'development/secret_hunter_program/candidates';dst=base/'V6-cache'
    shutil.copytree(ROOT/'secret-hunter-program',dst,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
    cfg=json.loads((base/'T1/config.json').read_text());cfg.update(version='V6-cache',parent='T1',plan_cache=True);write(dst/'config.json',cfg)
    names=['B0','V1-score','V2-search','V3-trained','V4-no-search','V5-combined','V6-cache']
    results={}
    for name in names:
        folder='experiments/program-'+name.lower()+'-validation'
        command=[sys.executable,'-m','development.secret_hunter_program.run','--candidate',str((base/name).relative_to(ROOT)),'--out',folder,'--start','73500','--seeds','10','--workers','4','--split','validation','--hypothesis',f'Frozen validation of {name}; matched module ablation against B0. No final seeds inspected.']
        with (ROOT/'docs/secret_hunter_program'/f'{name}-validation.log').open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        summary=json.loads((ROOT/folder/'summary.json').read_text());results[name]={'summary':summary,'command':command}
        if name!='B0':results[name]['paired']=compare('experiments/program-b0-validation',folder)
        write(ROOT/'docs/secret_hunter_program/validation.json',results)
        print(name,summary['primary']['wins'],'/',summary['primary']['n'],'base',summary['base']['wins'],'/',summary['base']['n'],flush=True)
if __name__=='__main__':main()
