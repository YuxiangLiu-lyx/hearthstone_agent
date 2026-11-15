"""Real-engine boundary checks, conservatively charged as CF attempts."""
import json
import time
from pathlib import Path
from development.secret_hunter_astra_sprint.study import RUN,HERE
from development.secret_hunter_astra_sprint.tactical import setup,restore
from development.secret_hunter_astra_sprint.cfqueue import connect,reserve
from development.secret_hunter_astra_sprint import ledger
from development.benchmarks.run import fingerprint

def projection(s):
    fields=('card_id','entity_id','attack','health','max_health','taunt','divine_shield','silenced','stealth','frozen')
    return {side:{'hero':{k:s[side]['hero'].get(k,False) for k in ('health','armor','attack')},
        'board':[{k:m.get(k,False) for k in fields} for m in s[side]['board']],
        **({'mana':s[side]['mana'],'hand':[c['entity_id'] for c in s[side]['hand']]} if side=='you' else {})}
        for side in ('you','opponent')}

def main():
    setup('RJC');import tactical_model as model
    db=connect();sources=[]
    for p in sorted((RUN/'tactical-sources').glob('sprint-*.json')):
        src=json.loads(p.read_text())
        if src['split']!='train':continue
        s=src['state'];a=src['original_action'];hand={c['entity_id']:c for c in s['you']['hand']}
        if src['original_info'].get('turn_search',{}).get('reason')!='top_action_outside_effect_coverage':continue
        if a['type']=='play_card' and hand[a['card']]['card_id']=='NEW1_019' and not any(m['card_id']=='NEW1_019' and not m.get('silenced') for m in s['you']['board']):sources.append(src)
    jobs=[('projection-RJC-'+src['case'],{'case':src['case'],'arm':'RJC','kind':'one-action projection audit'}) for src in sources]
    reserve('projection',jobs);results=[]
    for src,(key,job) in zip(sources,jobs):
        row=db.execute('select * from cf_jobs where key=?',(key,)).fetchone();path=Path(row['result_path'])
        if row['status']=='done':results.append(json.loads(path.read_text()));continue
        assert db.execute('select count(*) from cf_attempts').fetchone()[0]<16000
        aid=db.execute("insert into cf_attempts(key,status,started) values (?,'running',?)",(key,time.time())).lastrowid
        db.execute("update cf_jobs set status='running' where key=?",(key,));db.commit()
        try:
            e,steps=restore(src);s=e.view(src['seat']);a=src['original_action']
            projected=model.transition(model.prepare({**src['state'],'planning_mode':'response'}),a)
            assert projected is not None
            assert e.step(src['seat'],a).accepted
            assert projection(projected)==projection(e.view(src['seat'])),(src['case'],projection(projected),projection(e.view(src['seat'])))
            # The newly admitted card must remain available for comparison.
            initial=model.prepare({**src['state'],'planning_mode':'response'})
            assert any(x.get('card')==a['card'] for x in model.options(initial))
            result={'case':src['case'],'job':job,'prefix_steps':steps,'passed':True,
                    'candidate_sha256':fingerprint(HERE/'candidates/RJC'),
                    'terminal':False,'scope':'One-action model fidelity check, not a win/loss continuation; conservatively consumes CF budget'}
            ledger.atomic(path,result)
            db.execute("update cf_attempts set status='done',finished=? where id=?",(time.time(),aid))
            db.execute("update cf_jobs set status='done' where key=?",(key,));db.commit();results.append(result)
        except Exception:
            db.execute("update cf_attempts set status='error',finished=? where id=?",(time.time(),aid))
            db.execute("update cf_jobs set status='error' where key=?",(key,));db.commit();raise
    ledger.setmeta(db,'continuations',db.execute('select count(*) from cf_attempts').fetchone()[0])
    ledger.atomic(RUN/'RJC-engine-projection-checks.json',{'checks':len(results),'all_passed':all(r['passed'] for r in results),'records':results})
    print(json.dumps({'checks':len(results),'all_passed':all(r['passed'] for r in results)}))

if __name__=='__main__':main()
