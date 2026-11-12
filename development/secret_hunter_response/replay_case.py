"""Replay a recorded conditional future using only archived engine action prefixes."""
import argparse,copy,json
from pathlib import Path
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.counterfactual import worker
from development.secret_hunter_response.accounting import reserve,finish

def main():
 p=argparse.ArgumentParser();p.add_argument('--file',default='counterfactual-extended.jsonl');p.add_argument('--case',type=int,required=True);p.add_argument('--plan',required=True);p.add_argument('--sample',type=int,default=0);p.add_argument('--out',required=True);a=p.parse_args()
 D=ROOT/'docs/secret_hunter_response';r=next(x for x in readlines(D/a.file) if x['case_id']==a.case);plan=next(p for p in r['plans'] if p['id']==a.plan);expected=next(o for o in plan['outcomes'] if o['split']=='validation' and o['sample']==a.sample)
 c=copy.deepcopy(r['case']);c['_frozen_plans']=[{k:v for k,v in plan.items() if k!='outcomes'}];c['_validation_offset']=expected['future_rng_seed']-964000-a.case*100
 name='replay-'+Path(a.out).stem;reserve(name,full=1,short=300,final=True,seconds=120);actual=worker((c,a.case,0,1))['plans'][0]['outcomes'][0]
 report={'source':a.file,'case':a.case,'plan':a.plan,'sample':a.sample,'expected':expected,'actual':actual,'same_win':expected['win']==actual['win'],'same_first_turn_trace':expected['own_first_turn_plan']==actual['own_first_turn_plan'],'same_next_turn':expected['start_of_next_own_turn']==actual['start_of_next_own_turn']};write(ROOT/a.out,report);finish(name,actual_full=1);assert report['same_win'] and report['same_first_turn_trace'] and report['same_next_turn'];print(json.dumps({k:v for k,v in report.items() if k not in ('expected','actual')}))
if __name__=='__main__':main()
