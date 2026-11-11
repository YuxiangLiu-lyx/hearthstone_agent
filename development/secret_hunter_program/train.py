"""Two generations of seeded local mutations and measured parent retention."""
import json,random,shutil,subprocess,sys,time
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.benchmarks.run import fingerprint


def main():
    rng=random.Random(4611);base=json.loads((ROOT/'development/secret_hunter_program/candidates/P2/config.json').read_text())
    defaults={'turn_face':1.1,'turn_board':1.0,'turn_hand':1.4,'turn_risk':4.0,'turn_width':10,'turn_depth':7,'turn_nodes':300,'turn_budget_s':.045}
    parent=base|defaults;retained='P2';records=[]
    p2=json.loads((ROOT/'experiments/program-p2-development/summary.json').read_text())
    best=(p2['primary']['win_rate'],p2['base']['win_rate'])
    for generation in range(2):
        offspring=[]
        for child in range(3):
            name='T'+str(generation*3+child+1);cfg=dict(parent)
            for key,sd,lo,hi in [('turn_face',.25,.6,1.8),('turn_board',.2,.6,1.4),('turn_hand',.35,.5,2.3),('turn_risk',1.0,1.,7.)]:
                cfg[key]=round(max(lo,min(hi,cfg[key]+rng.gauss(0,sd))),3)
            cfg['turn_width']=rng.choice([6,10,14]);cfg['turn_depth']=rng.choice([5,7,9]);cfg['turn_nodes']=rng.choice([200,350,500]);cfg['turn_budget_s']=.08
            cfg.update(version=name,parent=retained)
            dest=ROOT/'development/secret_hunter_program/candidates'/name
            shutil.copytree(ROOT/'secret-hunter-program',dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
            write(dest/'config.json',cfg)
            out='experiments/program-'+name.lower()+'-development'
            hypothesis=f'{name}: local mutation of {retained}; optimize board/face/hand/risk weights and beam/node/depth controls on frozen development seeds.'
            command=[sys.executable,'-m','development.secret_hunter_program.run','--candidate',str(dest.relative_to(ROOT)),'--out',out,'--start','73000','--seeds','6','--workers','4','--hypothesis',hypothesis]
            record={'candidate':name,'generation':generation,'parent':retained,'hypothesis':hypothesis,'config':cfg,'candidate_sha256':fingerprint(dest),'command':command,'status':'running'};records.append(record)
            write(ROOT/'docs/secret_hunter_program/training.json',{'random_seed':4611,'method':'Two generations, three Gaussian/local categorical mutations per generation, elitist retention on matched development outcomes. No coevolving opponents.','records':records})
            with (ROOT/'docs/secret_hunter_program'/f'{name}-run.log').open('w') as log:subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            result=json.loads((ROOT/out/'summary.json').read_text());fitness=(result['primary']['win_rate'],result['base']['win_rate']);record.update(status='completed',result=result,fitness=fitness)
            offspring.append((fitness,name,cfg))
            print(name,'primary',result['primary']['wins'],'/',result['primary']['n'],'base',result['base']['wins'],flush=True)
        top=max(offspring,key=lambda x:x[0])
        if top[0]>best:best,retained,parent=top
        for record in records:
            if record['generation']==generation:record['retained_after_generation']=retained
        write(ROOT/'docs/secret_hunter_program/training.json',{'random_seed':4611,'method':'Two generations, three Gaussian/local categorical mutations per generation; retained best paired development fitness (primary macro, then Greedy). Selection-biased until validation.','retained':retained,'fitness':best,'records':records})
        print('Retained',retained,best,flush=True)
if __name__=='__main__':main()
