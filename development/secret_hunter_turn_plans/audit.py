"""Game-level trigger funnels, full-CLI reliability, and strict pairing audits."""
from collections import Counter,defaultdict
import argparse
import json
from pathlib import Path
import sqlite3
from development.secret_hunter_turn_plans.study import RUN
from development.secret_hunter_program.common import quantiles
from development.teacher_eval.compare import paired,index


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--baseline',default='Y1');args=p.parse_args()
    db=sqlite3.connect(f'file:{RUN}/ledger.sqlite?mode=ro',uri=True)
    tasks=defaultdict(list)
    for arm,raw in db.execute("select candidate,result from tasks where batch=? and status='done'",(args.batch,)):
        tasks[arm].append(json.loads(raw))
    report={'batch':args.batch,'arms':{},'pair_audit':[],'comparisons':{}}
    for arm,rows in tasks.items():
        decisions=Counter();games=defaultdict(set);reasons=Counter();times=[];invalid=0;first_errors=[]
        for row in rows:
            game=row.get('game')
            if not game:continue
            path=RUN/'batches'/args.batch/arm/'games'/game/f"p{row['seat']}"/'observations.jsonl'
            for line in path.read_text().splitlines():
                event=json.loads(line);info=event['info'];r=info.get('turn_routes',{});s=event['state']
                times.append(event['elapsed_s']);decisions['calls']+=1
                for key in ('hit','legal_alternative','changed','cache_hit'):
                    if r.get(key):decisions[key]+=1;games[key].add(game)
                for ctx in r.get('context',[]):games['context_'+ctx].add(game)
                if r.get('cached_steps'):decisions['plans_saved']+=1;games['plans_saved'].add(game)
                if r.get('cache_hit') or r.get('cache')=='fresh_plan_preferred':
                    games['valid_continuation'].add(game)
                if r.get('changed') or r.get('cache')=='fresh_plan_preferred':
                    games['different_legal_continuation'].add(game)
                if r.get('cache'):reasons[r['cache']]+=1
                for key in ('fallback','error'):
                    if info.get(key):decisions[key]+=1;games[key].add(game)
                if event['elapsed_s']>2:decisions['over_2s']+=1
                if info.get('error') and len(first_errors)<3:first_errors.append({'game':game,'seq':s['seq'],'error':info['error']})
        report['arms'][arm]={'games':len(rows),'decisions':dict(decisions),
                            'game_funnel':{k:len(v) for k,v in games.items()},'cache_reasons':dict(reasons),
                            'latency_s':quantiles(times),'first_errors':first_errors}
    names=list(tasks)
    if args.baseline in names:names.remove(args.baseline);names.insert(0,args.baseline)
    base=names[0]
    for arm in names[1:]:
        aa,bb=index(tasks[base]),index(tasks[arm])
        if aa.keys()!=bb.keys():continue
        report['comparisons'][arm]={'all':paired(tasks[base],tasks[arm])}
        if {r['group'] for r in tasks[base]}>={'astra','bot2'}:
            report['comparisons'][arm]['primary']=paired(tasks[base],tasks[arm],groups=['astra','bot2'],equal_groups=True)
            report['comparisons'][arm]['astra']=paired(tasks[base],tasks[arm],groups=['astra'])
        for key in sorted(aa):
            a,b=aa[key],bb[key]
            if a['score']==b['score']:continue
            event_rows=[]
            for who,r in ((base,a),(arm,b)):
                path=RUN/'batches'/args.batch/who/'games'/r['game']/f"p{r['seat']}"/'observations.jsonl'
                event_rows.append([json.loads(line) for line in path.read_text().splitlines()])
            first=None
            for x,y in zip(*event_rows):
                if x['action']!=y['action']:
                    # The source pair must have identical public boards/hands up
                    # to its first changed atomic action. Presentation IDs may vary.
                    matched=all(x['state'].get(k)==y['state'].get(k) for k in ('you','opponent','phase','turn'))
                    first={'seq':[x['state']['seq'],y['state']['seq']], 'same_public_state':matched,
                           'state':x['state'],'baseline_action':x['action'],'candidate_action':y['action'],
                           'baseline_info':x['info'],'candidate_info':y['info']}
                    break
            report['pair_audit'].append({'key':key,'baseline':base,'candidate':arm,'baseline_score':a['score'],
                                        'candidate_score':b['score'],'first_difference':first})
    suffix='' if args.baseline=='Y1' else '-'+args.baseline
    out=RUN/'batches'/args.batch/('audit'+suffix+'.json');out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'arms':report['arms'],'audited_discordant_pairs':len(report['pair_audit']),
                     'first_public_state_mismatches':sum(not r['first_difference']['same_public_state'] for r in report['pair_audit'] if r['first_difference'])},indent=2))


if __name__=='__main__':main()
