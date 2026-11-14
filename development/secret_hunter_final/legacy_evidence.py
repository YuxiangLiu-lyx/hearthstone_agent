"""Recover a small portable subset of old evidence; never call it new training."""
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from development.secret_hunter_final.study import RUN,ROOT
from development.secret_hunter_mcgs import train

OLD=Path('/Users/liuyuxiang/.codex/worktrees/hearthstone-turn-plans-20261112/runs/turn-plans-20261112')

def main():
    selected=[];aggregate={}
    folder=OLD/'amani-explicit-diagnostic';groups=defaultdict(dict)
    for p in folder.glob('*.json'):
        if '.request.' in p.name:continue
        r=json.loads(p.read_text())
        if isinstance(r,dict) and r.get('terminal'):groups[(r['case'],r['scenario'],r['sample'])][r['route']]=(p,r)
    for scenario in ['natural','forced_coil']:
        pairs=[(v['replan'],v['diagnostic_cheap_trade_highmane']) for (case,sc,sample),v in groups.items()
               if sc==scenario and 'replan' in v and 'diagnostic_cheap_trade_highmane' in v]
        aggregate[scenario]={'n':len(pairs),'baseline':sum(a[1]['win'] for a,b in pairs),
                             'cheap_trade':sum(b[1]['win'] for a,b in pairs),
                             'flips':sum(b[1]['win']>a[1]['win'] for a,b in pairs),
                             'regressions':sum(b[1]['win']<a[1]['win'] for a,b in pairs)}
        candidates=[(a,b) for a,b in pairs if b[1]['win']>a[1]['win'] and a[1].get('full_trace') and b[1].get('full_trace')]
        if candidates:selected.extend(x[0] for x in candidates[0])
    selected.extend(OLD/'recovered-golem-continuations'/f'trap-replay-0-natural-0-{r}.json' for r in ['replan','committed'])
    selected.extend(OLD/'continuations-v4'/f'amani-031-natural-0-{r}.json' for r in ['replan','bow_amani'])
    dest=RUN/'legacy';dest.mkdir(exist_ok=True);records=[]
    db=train.connect(RUN)
    for src in selected:
        request=json.loads(src.with_name(src.stem+'.request.json').read_text());source=Path(request['source'])
        if not source.exists():source=OLD/source.parent.name/source.name
        copied=dest/'sources'/source.name;copied.parent.mkdir(exist_ok=True);shutil.copy2(source,copied)
        target=dest/src.name;shutil.copy2(src,target);request['source']=str(copied)
        train.atomic(target.with_name(target.stem+'.request.json'),request)
        train.setmeta(db,'extra_continuations',train.meta(db,'extra_continuations',0)+1)
        result=subprocess.run([sys.executable,'-m','development.secret_hunter_turn_plans.replay',str(target)],
                              env={**os.environ,'KRUSH_TURN_RUN':str(dest)},capture_output=True,text=True,check=True)
        records.append({'result':str(target.relative_to(ROOT)),'replay':json.loads(result.stdout)})
    data={'historical_amani_raw_reaggregation':aggregate,'exact_replays':records,
          'provenance':'Known C2-translated public replay and old original-deck natural samples; reused diagnosis only. These are not new seed groups.'}
    train.atomic(ROOT/'docs/secret_hunter_final/legacy-evidence.json',data)
    print(json.dumps(data))

if __name__=='__main__':main()
