"""Pooled exact-package statistics and protocol timing after both pools close."""
import json
from pathlib import Path
from development.secret_hunter_astra_sprint.study import ROOT,RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import quantiles,sha

def read(p):return json.loads(p.read_text())

def main():
 db=ledger.connect(RUN);recommendation=read(ROOT/'docs/secret_hunter_astra_sprint/recommendation.json');acceptance=read(RUN/'final-acceptance.json');freeze=read(RUN/'final-freeze.json');pools={}
 for batch in ('final-core','final-guard'):
  assert db.execute('select status from batches where id=?',(batch,)).fetchone()[0]=='done'
  p=RUN/'batches'/batch/'report.json';pools[batch]={'report_sha256':sha(p),'report':read(p)}
  for suffix in ('actions','action-paths'):
   path=RUN/'analysis'/f'{batch}-DARCL2-{recommendation["challenger"]}-{suffix}.json'
   if path.exists():pools[batch][suffix]={k:v for k,v in read(path).items() if k!='examples'}
 cli={}
 for arm in freeze['arms']:
  rows=[json.loads(r[0]) for r in db.execute("select result from tasks where phase in ('final_core','final_guard') and candidate=? and status='done'",(arm,))];runtime=read(ROOT/f'docs/secret_hunter_astra_sprint/runtime-{arm}.json')
  cli[arm]={'merged_final_pools':ledger.summarize(rows),'cold_start':quantiles([r['elapsed_s'] for r in runtime['records'] if r['tag'].startswith('cold-')]),'runtime_ordinary':runtime['ordinary_latency_s'],'runtime_including_injected_faults':runtime['all_including_fault_latency_s'],'concurrency_action_stability':runtime['concurrency_action_stability']}
 relay={}
 for mode in ('luna','client'):
  records=[r for r in acceptance.get('records',[]) if r['mode']==mode];internal=[];publication=[];outside=[]
  for record in records:
   player=Path(record['game_path'])/f'p{record["seat"]}';decisions=[json.loads(l) for l in (player/'seat/scratch/decisions.jsonl').read_text().splitlines()];normal={d['seq']:d for d in decisions if d['phase']!='deck_submission'};internal.extend(d['elapsed_s'] for d in normal.values())
   calls=[json.loads(l) for l in (player/'seat/mcp_calls.jsonl').read_text().splitlines()]
   for call in calls:
    if call['tool']!='act' or call['arguments']['seq'] not in normal:continue
    seq=call['arguments']['seq'];elapsed=call['time']-(player/f'decisions/{seq:05d}.state.json').stat().st_mtime;publication.append(elapsed);outside.append(elapsed-normal[seq]['elapsed_s'])
  relay[mode]={'games':len(records),'act_calls':sum(r['act_calls'] for r in records),'actual_first':sum(r['result']['first_player']==r['seat'] for r in records),'internal_program_latency_s':quantiles(internal),'publication_to_act_latency_s':quantiles(publication),'outside_internal_program_latency_s':quantiles(outside)}
 result={'recommended':recommendation['recommended'],'freeze':freeze,'recommendation':recommendation,'pools':pools,'full_cli':cli,'relay':relay,'final_pools_complete':True,'paired_final_validation_complete':len(freeze['arms'])==2,'protocol_acceptance':{'passed':acceptance.get('passed',False),'gap':acceptance.get('gap'),'plan_sha256':acceptance.get('plan_sha256')},
  'latency_method':'Quantiles recomputed from pooled raw decision samples, never averaged per-game quantiles.',
  'timing_scope':'Full CLI includes interpreter/process startup. Relay internal program timer excludes interpreter startup; publication-to-act includes model, shell, Python and transport. It is not pure network latency.',
  'formal_score_scope':'No new formal course receipt. Verified historical 10-point C2 receipt remains Bot1 5/6, Bot2 2/4, Astra 1/4; local proxies and score simulation do not update that receipt.'}
 ledger.atomic(RUN/'final-validation.json',result);ledger.atomic(ROOT/'docs/secret_hunter_astra_sprint/final-validation.json',result)
 print(json.dumps({'recommended':result['recommended'],'full_cli':{k:v['merged_final_pools']['latency_s'] for k,v in cli.items()},'relay':relay},indent=2))
if __name__=='__main__':main()
