"""Audit immutable experiment artifacts and summarize actual completed games."""
import json,fcntl
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,sha,write,readlines
from development.secret_hunter_program.summarize import measurements,reproduction
from development.benchmarks.run import fingerprint

def main():
 p=ROOT/'docs/secret_hunter_tactics/budget.json';ledger=json.loads(p.read_text());reports={}
 for r in ledger['runs']:
  folder=ROOT/r['out'];config=json.loads((folder/'config.json').read_text());rows=readlines(folder/'results.jsonl')
  if r['mode']=='python':
   assert len(rows)==r['reserved'],r['out'];assert fingerprint(ROOT/config['candidate'])==config['candidate_sha256']
   report=measurements(folder,rows);summary=json.loads((folder/'summary.json').read_text())
   report.update(summary=summary,candidate=config['candidate'],candidate_sha256=config['candidate_sha256'],
     config_sha256=sha(ROOT/config['candidate']/'config.json'),deck_sha256=config['deck_sha256'],
     opponent_sha256=config['manifest_sha256'],hypothesis=config['hypothesis'],split=config['split'])
   reports[r['out']]=report;r.update(completed=len(rows),status='completed')
  elif r['mode']=='client':
   results=[json.loads(g.read_text()) for g in folder.glob('g_*/result.json')]
   assert len(results)==r['reserved'];r.update(completed=len(results),status='completed')
  else:
   interrupted=list((folder/'games').glob('*/interruption.json'))
   assert len(rows)+len(interrupted)==r['reserved']
   r.update(completed=len(rows),interrupted=len(interrupted),status='completed_with_external_interruption' if interrupted else 'completed')
 ledger['full_games_completed']=sum(r['completed'] for r in ledger['runs']);ledger['full_games_reserved']=sum(r['reserved'] for r in ledger['runs'])
 ledger['externally_interrupted_attempts']=sum(r.get('interrupted',0) for r in ledger['runs'])
 ledger['full_game_attempts_charged']=sum(r['reserved'] for r in ledger['runs'])
 ledger['updated_utc']=datetime.now(timezone.utc).isoformat();ledger['elapsed_wall_seconds']=(datetime.now(timezone.utc)-datetime.fromisoformat(ledger['started_utc'])).total_seconds()
 with (p.parent/'budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);live=json.loads(p.read_text());ledger['short_continuations']=live['short_continuations'];ledger['short_continuations_used']=sum(r['count'] for r in live['short_continuations']);write(p,ledger)
 write(ROOT/'docs/secret_hunter_tactics/experiments.json',reports)
 rep=reproduction('experiments/tactics-final-confirmation','experiments/tactics-zip-reproduction-confirmation','docs/secret_hunter_tactics/reproduction.json')
 print(json.dumps({'games':ledger['full_games_completed'],'short_cases':ledger['short_continuations_used'],
                   'reproduced_outcomes':rep['same_outcomes'],'reproduced_traces':rep['identical_action_traces']}))
 print(json.dumps({k:v for k,v in reports['experiments/tactics-final-confirmation'].items() if k in ('latency_s','nodes','policy_errors','fallbacks','over_2s')}))
if __name__=='__main__':main()
