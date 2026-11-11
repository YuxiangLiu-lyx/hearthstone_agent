"""Compact interpretable mutations with fresh-block parent re-evaluation and retention."""
import subprocess,sys,json
from development.secret_hunter_tactics.freeze_candidate import freeze,D,DOC
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.compare import compare

def run(name,start,seeds,label,hypothesis):
    out=f'experiments/tactics-{name.lower()}-{label}'
    cmd=[sys.executable,'-m','development.secret_hunter_tactics.run','--candidate',str((D/'candidates'/name).relative_to(ROOT)),
         '--out',out,'--start',str(start),'--seeds',str(seeds),'--hypothesis',hypothesis]
    with open(f'/tmp/tactics-{name.lower()}-{label}.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
    s=json.loads((ROOT/out/'summary.json').read_text());print(name,label,s['primary']['wins'],s['primary']['n'],flush=True)
    return {'name':name,'out':out,'primary_wins':s['primary']['wins'],'base_wins':s['base']['wins'],'summary':s}

def main():
    base=json.loads((D/'candidates/H3/config.json').read_text())
    base.update(extended_turn=True)
    freeze('H4',base,'H3 with conservative rejection of unobserved freeze expiry and fair response deadline fallback.','H3')
    freeze('H5',{**base,'public_response':False},'Attack-response ablation with identical effect coverage, hand clock and opening policy.','H4')
    for n in ('H4','H5'):run(n,82100,6,'development',json.loads((DOC/f'{n}.json').read_text())['hypothesis'])
    mutations=[('T1',{'reply_weight':.55,'reply_nodes':72,'reply_width':5,'turn_nodes':450,'turn_width':12,'turn_budget_s':.10},'Broader response search, less pessimistic post-response weight.'),
      ('T2',{'race_face_bonus':.9,'hand_clock_bonus':22,'board_clock_bonus':7,'turn_face':1.28,'reply_weight':.7},'Stronger two-turn closure when visible health reserve is safe.'),
      ('T3',{'hidden_burst_buffer':5,'turn_risk':4.2,'protection_weight':.9,'reply_weight':1.0,'reply_nodes':72},'Higher hidden-burst reserve and protection of key minions.'),
      ('T4',{'trap_resource':2.1,'explosive_priority':3.5,'combo_weight':1.3,'turn_width':12,'turn_nodes':450,'turn_budget_s':.10},'More contingent trap value and combo ordering with wider own-turn search.'),
      ('T5',{'opening_plan':False,'race_face_bonus':.35,'hand_clock_bonus':10,'board_clock_bonus':3,'turn_board':1.2,'reply_weight':.7},'Conservative closure and stronger material with the old opening policy.')]
    for n,changes,h in mutations:freeze(n,{**base,**changes},h,'H4')
    plan={'method':'One (1+5) interpretable mutation/retention generation; parent re-evaluated on the same fresh block. No coevolution or rarity features.',
      'parent':'H4','seeds':list(range(82200,82206)),'mutations':[{'name':n,'changes':v,'hypothesis':h} for n,v,h in mutations]}
    write(DOC/'tuning-plan.json',plan)
    results=[]
    for n in ['H4']+[x[0] for x in mutations]:results.append(run(n,82200,6,'tuning',json.loads((DOC/f'{n}.json').read_text())['hypothesis']))
    winner=max(results,key=lambda x:(x['primary_wins'],x['base_wins']))['name']
    trained=max(results[1:],key=lambda x:(x['primary_wins'],x['base_wins']))['name']
    write(DOC/'tuning.json',{'plan':plan,'fitness':results,'retained':winner,'best_mutation':trained,
       'paired_vs_parent':{r['name']:compare(ROOT/results[0]['out'],ROOT/r['out']) for r in results[1:]}})
    print('RETAIN',winner,'BEST MUTATION',trained,flush=True)
if __name__=='__main__':main()
