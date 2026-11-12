"""Audit both players' action traces and preserve the first public divergence."""
import json
from development.secret_hunter_program.common import ROOT,readlines,write
from development.teacher_eval.compare import index
D=ROOT/'docs/secret_hunter_response';A=ROOT/'experiments/secret-hunter-response-e1-retain';B=ROOT/'experiments/secret-hunter-response-zip-reproduction'
a,b=index(readlines(A/'results.jsonl')),index(readlines(B/'results.jsonl'));details=[];differences=[]
for key,r in sorted(b.items()):
 old=a[key];both=True
 for seat in (1,2):
  xs=[readlines(folder/'games'/row['game']/f'p{seat}/observations.jsonl') for folder,row in ((A,old),(B,r))];equal=[z['action'] for z in xs[0]]==[z['action'] for z in xs[1]];both&=equal
  if not equal:
   for i,(x,y) in enumerate(zip(*xs)):
    if x['action']!=y['action']:
     ignore={'game_id','deadline_epoch_s'};same={k:v for k,v in x['state'].items() if k not in ignore}=={k:v for k,v in y['state'].items() if k not in ignore}
     differences.append({'pair':key,'seat':seat,'index':i,'same_public_observation_except_protocol_metadata':same,'old_action':x['action'],'new_action':y['action'],'old_info':x.get('info'),'new_info':y.get('info'),'old_elapsed':x.get('elapsed_s'),'new_elapsed':y.get('elapsed_s')});break
 details.append({'pair':key,'both_players_trace_equal':both})
write(D/'reproduction-differences.json',{'games':len(details),'both_players_exact':sum(x['both_players_trace_equal'] for x in details),'details':details,'first_differences':differences});print(json.dumps(differences)[:5000])
