"""Reconcile executed counts and candidate archives without changing raw results."""
import json
from pathlib import Path
from development.secret_hunter.bootstrap import ROOT,sha,write
from development.secret_hunter.audit import readlines
from development.benchmarks.run import fingerprint


def main():
    ledger_path=ROOT/'docs/secret_hunter/budget.json';ledger=json.loads(ledger_path.read_text())
    totals={'python':0,'skill':0,'cases':0};running={k:0 for k in totals}
    for run in ledger['runs']:
        out=ROOT/run['out'];rows=readlines(out/'results.jsonl')
        if not rows and out.exists():
            rows=[json.loads(p.read_text()) for p in out.glob('g_*/result.json')]
        run['completed']=len(rows);totals[run['mode']]+=len(rows)
        run['status']='complete' if len(rows)==run['reserved'] else 'incomplete'
        if (out/'summary.json').exists() and json.loads((out/'summary.json').read_text()).get('stopped_for_external_failure'):
            run['status']='external_failure';run['cancelled_before_start']=run['reserved']-len(rows)
        elif run['status']=='incomplete':running[run['mode']]+=run['reserved']-len(rows)
        run['game_wall_s_sum']=sum(r.get('wall_s',r.get('duration_s',0)) for r in rows)
    ledger['short_case_runs']=[
        {'name':'initial fixture adapter failure','engine_microfixtures':13},
        {'name':'corrected 13-test mechanism/timing suite','engine_microfixtures':29},
        {'name':'C2 13-test regression','engine_microfixtures':29},
        {'name':'C3 15-test suite','engine_microfixtures':121},
        {'name':'C4 15-test suite','engine_microfixtures':122},
        {'name':'upper bound old/new comparison','engine_microfixtures':1,'policy_branch_calls':2},
        {'name':'actual-game replay perturbations','short_branches':50,'replay_actions_not_matches':558},
        {'name':'adversarial JSON validation gap','policy_branch_calls':1},
        {'name':'C5 16-test suite','engine_microfixtures':123},
        {'name':'Final extracted C5 16-test suite','engine_microfixtures':123},
    ]
    # Conservatively reserve/count each constructed fixture and each perturbed branch,
    # plus the two old/new planner checks. Replayed prefix actions are listed separately.
    totals['cases']=sum(x.get('engine_microfixtures',0)+x.get('short_branches',0)+x.get('policy_branch_calls',0) for x in ledger['short_case_runs'])
    ledger['completed_totals']=totals;ledger['outstanding_reserved']=running
    ledger['remaining_after_reservations']={k:ledger['limits'][k]-totals[k]-running[k] for k in totals}
    ledger['model_requests']='Exact API request count is not exposed by official CLI JSON; actual commands/MCP calls and reported tokens are separately audited.'
    write(ledger_path,ledger)
    candidates=[]
    for p in sorted((ROOT/'development/secret_hunter/candidates').glob('*/secret-hunter-agent')):
        cfg=json.loads((p/'config.json').read_text())
        candidates.append({'id':cfg['version'],'parent':cfg.get('parent'),'path':str(p.relative_to(ROOT)),
                           'candidate_sha256':fingerprint(p),'deck_sha256':sha(p/'deck.json'),'config_sha256':sha(p/'config.json')})
    for p in sorted((ROOT/'development/secret_hunter').glob('frozen*/secret-hunter-agent')):
        cfg=json.loads((p/'config.json').read_text())
        candidates.append({'id':cfg['version'],'parent':cfg['parent'],'path':str(p.relative_to(ROOT)),
                           'candidate_sha256':fingerprint(p),'deck_sha256':sha(p/'deck.json'),'config_sha256':sha(p/'config.json')})
    write(ROOT/'docs/secret_hunter/candidate_archive.json',candidates)
    print(json.dumps({'completed':totals,'reserved_remaining':running,'budget_remaining':ledger['remaining_after_reservations']}))


if __name__=='__main__':main()
