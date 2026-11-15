"""Freeze challenging public states from completed, seen development games."""
import json,time
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.tactical import digest
from development.secret_hunter_program.common import sha

def main():
 path=RUN/'runtime-stress-cases.json';assert not path.exists();assert not (RUN/'final-freeze.json').exists()
 db=ledger.connect(RUN);assert db.execute("select status from batches where id='diagnostic-dev'").fetchone()[0]=='done'
 rows=[]
 for q in db.execute("select result from tasks where batch='diagnostic-dev' and candidate='DARCL2'"):
  game=json.loads(q[0]);folder=RUN/'batches/diagnostic-dev/DARCL2/games'/game['game'];log=folder/f"p{game['seat']}/observations.jsonl"
  for line in log.read_text().splitlines():
   z=json.loads(line);s=z['state']
   if s['phase']!='main':continue
   rows.append({'seed':game['seed'],'opponent':game['opponent'],'seat':game['seat'],'log_path':str(log),'state':s,'digest':digest(s),'observed_cli_s':z['elapsed_s'],'nodes':z['info'].get('nodes',0)})
 rows.sort(key=lambda r:(-r['observed_cli_s'],r['seed'],r['opponent'],r['seat'],r['state']['seq']))
 early=[r for r in rows if r['state']['opponent']['hero']['hero_class']=='WARLOCK' and 2<=r['state']['you']['max_mana']<=5]
 chosen=early[:4];keys={r['digest'] for r in chosen}
 for r in rows:
  if r['digest'] not in keys:chosen.append(r);keys.add(r['digest'])
  if len(chosen)==8:break
 ledger.atomic(path,{'created':time.time(),'source_batch':'diagnostic-dev','source_partition':'development','selection':'Four slowest T2-T5 Warlock public observations plus four other slowest distinct main observations, ranked by complete CLI latency, never by winner. Fixed before final opening.','cases':chosen})
 print(json.dumps({'cases':len(chosen),'sha256':sha(path),'observed_cli_s':[r['observed_cli_s'] for r in chosen]}))
if __name__=='__main__':main()
