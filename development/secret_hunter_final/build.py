"""Unpack the authentic parent and build immutable, minimal descendants."""
import json
from pathlib import Path
import shutil
from zipfile import ZipFile
from development.secret_hunter_final.study import HERE,RUN,ROOT,BASE_SHA,DECK_SHA
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint

def main():
    dest=HERE/'candidates';dest.mkdir(parents=True,exist_ok=True)
    if not (dest/'B').exists():
        with ZipFile(ROOT/'dist/secret-hunter-turn-plans/engine-trap-v2.zip') as z:
            z.extractall(RUN/'baseline-unpacked')
        src=RUN/'baseline-unpacked/secret-hunter'
        assert fingerprint(src)==BASE_SHA and sha(src/'deck.json')==DECK_SHA
        shutil.copytree(src,dest/'B')
    assert fingerprint(dest/'B')==BASE_SHA
    if not (dest/'M').exists():
        shutil.copytree(dest/'B',dest/'M',ignore=shutil.ignore_patterns('__pycache__'))
        p=dest/'M/scripts/tactics_rank.py';s=p.read_text()
        old="if secrets and (keeper or (pressure and low and secrets[0]['card_id']=='EX1_610')):"
        new="if secrets and (keeper or (pressure and low and secrets[0]['card_id']=='EX1_610') or (hc=='WARLOCK' and not ones and not two and secrets[0]['card_id']=='EX1_610')):"
        assert s.count(old)==1;p.write_text(s.replace(old,new))
    lineage=[{'name':'B','parent':None,'sha256':fingerprint(dest/'B'),'origin':'Exact specified ZIP'},
             {'name':'M','parent':'B','sha256':fingerprint(dest/'M'),'hypothesis':'Keep one Explosive Trap vs Warlock with no 1/2-cost minion; retain every prior branch','status':'unvalidated'}]
    p=HERE/'lineage.json'
    if not p.exists():p.write_text(json.dumps(lineage,indent=2)+'\n')
    lineage=json.loads(p.read_text())
    for name,parent in [('L','B'),('ML','M'),('L2','B'),('ML2','M')]:
        if (dest/name).exists():continue
        shutil.copytree(dest/parent,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(HERE/'face_lethal.py',dest/name/'scripts/face_lethal.py')
        policy=dest/name/'scripts/program_policy.py';s=policy.read_text()
        old="            info.update(lethal=lethal,nodes=lethal['nodes'])"
        new="""            # Preserve the inherited proof's priority; only fill its coverage gap.
            if not lethal['guaranteed']:
                from face_lethal import prove
                face=prove(state)
                if face:
                    face['inherited_nodes']=lethal['nodes']
                    lethal=face
            info.update(lethal=lethal,nodes=lethal['nodes'])"""
        assert s.count(old)==1;policy.write_text(s.replace(old,new))
        lineage.append({'name':name,'parent':parent,'sha256':fingerprint(dest/name),
                        'hypothesis':'Narrow burn/Steady Shot proof after existing lethal proof; v2 covers Houndmaster spell-safe board',
                        'status':'unvalidated'})
    p.write_text(json.dumps(lineage,indent=2)+'\n')
    print(json.dumps(lineage))

if __name__=='__main__':main()
