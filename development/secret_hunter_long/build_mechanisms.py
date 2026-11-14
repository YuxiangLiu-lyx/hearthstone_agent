"""Two champion-mechanism ablations share the parent's exact time/node caps."""
import json
import shutil
from development.secret_hunter_long.build import clone,audit
from development.secret_hunter_long.study import HERE,RUN,ROOT
from development.secret_hunter_mcgs.train import atomic

def miller(dest):
    p=dest/'scripts/turn_search.py';s=p.read_text()
    old="    for d in range(depth):"
    new="""    # Miller 2020: spend depth on small branching factors, bounded by the
    # inherited maximum depth, nodes and wall clock. No extra search budget.
    branches=sum(a['type']!='end_turn' for _,a in ranked)
    depth=min(depth,9 if branches<5 else 6 if branches<25 else 3)
    report['adaptive_depth']={'branches':branches,'limit':depth,'source':'Miller2020'}
    for d in range(depth):"""
    assert s.count(old)==1;p.write_text(s.replace(old,new))

def predator(dest):
    shutil.copy2(HERE/'champion_recovery.py',dest/'scripts/champion_recovery.py')
    p=dest/'scripts/turn_search.py';s=p.read_text()
    old="response=worst_reply(endpoint,cfg,reply_deadline,cfg.get('reply_nodes',48))"
    new="response=worst_reply(endpoint,cfg,reply_deadline,max(1,cfg.get('reply_nodes',48)*2//3))"
    assert s.count(old)==1;s=s.replace(old,new)
    old="            if response['visible_lethal_found']:v-=100000"
    new="""            if response['visible_lethal_found']:v-=100000
            else:
                from champion_recovery import recovery
                rec=recovery(response['state'],cfg,reply_deadline,cfg.get('reply_nodes',48)//3)
                reply_nodes+=rec['nodes']
                response['known_hand_recovery']=rec
                if rec.get('supported'):v+=0.35*min(30,rec.get('gain',0))"""
    assert s.count(old)==1;p.write_text(s.replace(old,new))

def lethal(dest):
    shutil.copy2(ROOT/'development/secret_hunter_final/candidates/L2/scripts/face_lethal.py',dest/'scripts/face_lethal.py')
    p=dest/'scripts/program_policy.py';s=p.read_text();old="            info.update(lethal=lethal,nodes=lethal['nodes'])"
    new="""            if not lethal['guaranteed']:
                from face_lethal import prove
                face=prove(state)
                if face:
                    face['inherited_nodes']=lethal['nodes'];lethal=face
            info.update(lethal=lethal,nodes=lethal['nodes'])"""
    assert s.count(old)==1;p.write_text(s.replace(old,new))

def main():
    rows=[]
    for name,edit,description in [
      ('TMILL',miller,'2020 premade champion Miller GetMove branching depth allocation; same parent caps'),
      ('TRPLY',predator,'2018 premade champion PredatorMCTS response then known-hand recovery; same 48 nodes split 32/16 per endpoint'),
      ('BL2',lethal,'Standalone inherited narrow burn/power lethal coverage repair; original deck and mulligan')]:
        p=clone(name,'B',edit=edit,hypothesis=description,generation=1);rows.append(audit(p))
    atomic(RUN/'mechanism-candidate-audit.json',rows)
    print(json.dumps({r['candidate']:r['fingerprint'] for r in rows}))

if __name__=='__main__':main()
