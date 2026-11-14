"""Run the two reported missed lethals from exact original seed/action prefixes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from development.secret_hunter_final.study import HERE,RUN,ROOT
from development.secret_hunter_final.counterfactual import setup,restore,digest,visible
from development.secret_hunter_mcgs import train

def main():
    setup();records=[]
    db=train.connect(RUN)
    pop={s['name']:s for s in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    for batch,seed,seat,seq in [('historical24',21110024,2,31),('historical37',21110037,1,34)]:
        rows=[json.loads(x) for x in (RUN/'batches'/batch/'B/results.jsonl').read_text().splitlines()]
        row=next(r for r in rows if r['seed']==seed and r['seat']==seat and r['opponent']=='bot2-face-proxy')
        folder=RUN/'batches'/batch/'B/games'/row['game']
        logs=[json.loads(x) for x in (folder/f'p{seat}/observations.jsonl').read_text().splitlines()]
        entry=next(r for r in logs if r['state']['seq']==seq)
        source={'case':f'historical-{seed}-{seat}-{seq}','seed':seed,'seat':seat,'seq':seq,
                'game_path':str(folder.relative_to(ROOT)),'state_digest':digest(entry['state']),
                'opponent_spec':pop[row['opponent']]}
        e,steps=restore(source);sequence=[]
        train.setmeta(db,'extra_continuations',train.meta(db,'extra_continuations',0)+1)
        with tempfile.TemporaryDirectory(prefix='lethal-cli-') as tmp:
            skill=Path(tmp)/'skill';shutil.copytree(HERE/'candidates/L2',skill,ignore=shutil.ignore_patterns('__pycache__'))
            (skill/'game').mkdir()
            for i in range(5):
                if e.over:break
                s=e.view(seat);s.update(player=seat,seq=seq+i,game_id=source['case'],events=[])
                history=[v for ev in e.events if (v:=ev.view(seat)) is not None]
                (skill/'game/state.json').write_text(json.dumps(s))
                (skill/'game/history.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in history))
                start=time.monotonic();proc=subprocess.run([sys.executable,'scripts/decide.py'],cwd=skill,capture_output=True,text=True,check=True,timeout=2)
                elapsed=time.monotonic()-start;out=json.loads(proc.stdout)
                info=json.loads((skill/'scratch/decisions.jsonl').read_text().splitlines()[-1])
                assert out['seq']==s['seq'] and not info.get('worker_error')
                assert e.step(seat,out['action']).accepted
                sequence.append({'state':s,'envelope':out,'elapsed_s':elapsed,'info':info['info']})
            assert e.over and e.winner==seat
        records.append({'source':source,'prefix_verified_steps':steps,'baseline_action':entry['action'],
                        'baseline_terminal_score':row['score'],'candidate':'L2','candidate_score':1,
                        'sequence':sequence,'terminal':True,'scope':'Known-seed diagnostic, excluded from independent gain'})
    train.atomic(ROOT/'docs/secret_hunter_final/historical-lethals.json',records)
    print(json.dumps({'exact_prefix_reproductions':len(records),'flips':len(records),
                      'cli_calls':sum(len(r['sequence']) for r in records)}))

if __name__=='__main__':main()
