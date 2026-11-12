"""Recorded structural revision after the pilot weapon reconstruction failure."""
import json
from development.secret_hunter_mcgs.build import build,HERE
from development.secret_hunter_mcgs.train import connect,meta,setmeta,reserve,atomic,ROOT

def main():
    run=ROOT/'runs/krush-mcgs';db=connect(run)
    assert meta(db,'pid') is None
    before=json.loads((ROOT/'docs/secret_hunter_mcgs/recovery-before.json').read_text())
    done={r[0] for r in db.execute("SELECT key FROM tasks WHERE status='done'")}
    assert set(before['done_keys'])<=done
    attempts=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    assert attempts==len(done)==48
    atomic(ROOT/'docs/secret_hunter_mcgs/recovery-after-stop.json',{'attempts':attempts,'completed':len(done),'prior_completed_retained':True,'duplicate_charges':0,'signal':'SIGTERM','inflight_drained':True})
    old=meta(db,'candidates');base=dict(old['M2-dpw']['settings'])
    rows=[]
    for name,graph,chance,parent in [('M3-uct','uct','fixed','M0-uct'),('M3-fixed','ucd','fixed','M1-fixed'),('M3-dpw','ucd','dpw','M2-dpw')]:
        item=build(name,{**base,'graph':graph,'chance':chance},parent)
        item.update(origin='Codex structural revision',failure='Weapon.max_health is not durability; public-world bow gained two phantom charges.',
                    change='Reconstruct damage from observed durability; reject root weapon mismatch.',
                    evidence='checks.test_secret_order_bow_and_misdirection, original 48-game diagnostic')
        old[name]=item;rows.append(item)
    setmeta(db,'candidates',old);setmeta(db,'archive',['Y1','M3-uct','M3-fixed','M3-dpw'])
    with db:
        db.execute("UPDATE tasks SET status='cancelled_before_launch' WHERE status='pending'")
        db.execute("UPDATE batches SET status='aborted_semantic_failure' WHERE status!='done'")
    # The original seed block remains development. New paired blocks are separate.
    reserve(db,'pilot-100','development',['Y1','M3-uct','M3-fixed','M3-dpw'],10000200,2)
    reserve(db,'pilot-101','development',['Y1','M3-dpw'],10000300,2)
    atomic(HERE/'structural-lineage.json',rows)
    atomic(run/'amendment-001.json',{'reason':rows[0]['failure'],'charged_attempts_retained':48,'cancelled_unlaunched':96,
                                  'new_batches':['pilot-100','pilot-101'],'final_seeds_untouched':True})
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
