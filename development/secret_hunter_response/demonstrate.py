"""Replay the borrowed endpoint/response/recovery mechanism on public course states."""
import json,subprocess,sys
from development.secret_hunter_program.common import ROOT,readlines,write
from development.secret_hunter_response.accounting import reserve,finish
D=ROOT/'docs/secret_hunter_response';reserve('mechanism-demonstration',short=500,seconds=300)
rows=readlines(D/'counterfactual-balanced.jsonl')+readlines(D/'counterfactual-pilot.jsonl');results=[]
code='import json,sys;from pathlib import Path;p=Path(sys.argv[1]);sys.path.insert(0,str(p/"scripts"));from program_policy import decide;print(json.dumps(decide(json.load(sys.stdin),json.loads((p/"config.json").read_text()))))'
for r in rows[:30]:
 s=r['case']['observation'];outputs={}
 for arm in ('Y1','B3','C3'):
  path=ROOT/'development/secret_hunter_response/candidates'/arm
  action,info=json.loads(subprocess.check_output([sys.executable,'-c',code,str(path)],input=json.dumps(s),text=True));outputs[arm]={'action':action,'response':info.get('response'),'guaranteed_lethal':info.get('lethal',{}).get('guaranteed',False)}
 if outputs['C3'].get('response',{}).get('candidates'):
  results.append({'source_case_id':r['case_id'],'source':r['case']['source'],'row':r['case']['row'],'observation':s,'outputs':outputs,'root_changed':outputs['Y1']['action']!=outputs['C3']['action'],'hypotheses_changed_choice':outputs['B3']['action']!=outputs['C3']['action']})
  if len(results)>=4 and any(x['root_changed'] for x in results):break
write(D/'mechanism-demonstration.json',results);finish('mechanism-demonstration',actual_short=(rows.index(r)+1)*3);print(json.dumps([{'seq':x['observation']['seq'],'seed':x['row']['seed'],'opponent':x['row']['opponent'],'changed':x['root_changed'],'hypotheses_changed_choice':x['hypotheses_changed_choice']} for x in results]))
