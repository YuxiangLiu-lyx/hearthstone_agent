"""Outcome-blind capacity audit after the registered resource recovery pilot."""
import argparse
import hashlib
import json
import time
from development.secret_hunter_astra_sprint.study import RUN
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.release import raw_reliability
from development.secret_hunter_program.common import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    parser.add_argument('--health', required=True)
    parser.add_argument('--close-original-confirmation', action='store_true')
    args = parser.parse_args()
    db = ledger.connect(RUN)
    assert not ledger.meta(db, 'pid') and not ledger.meta(db, 'cf_pid')
    assert not ledger.meta(db, 'selection_opened', False) and not ledger.meta(db, 'final_opened', False)
    plan = json.loads((RUN / 'resource-recovery-plan.json').read_text())
    registered = next(p for p in plan['capacity_pilot_options'] if p['batch'] == args.batch)
    batch = db.execute('select * from batches where id=?', (args.batch,)).fetchone()
    assert batch['status'] == 'done' and batch['start'] == registered['start'] and batch['seeds'] == registered['seeds']
    assert json.loads(batch['arms']) == plan['capacity_pilot_arms']
    starts = list((RUN / 'batches' / args.batch / 'control-starts').glob('*.json'))
    assert starts and all(json.loads(p.read_text())['interleave_arms'] for p in starts)
    assert all(json.loads(p.read_text())['workers'] == plan['capacity_pilot_workers'] for p in starts)
    count, duration, finished = db.execute('select count(*),max(a.finished)-min(a.started),max(a.finished) from attempts a join tasks t on t.key=a.task where t.batch=?', (args.batch,)).fetchone()
    assert count == plan['capacity_pilot_games_each'] and duration > 0
    health_path = RUN / args.health
    health = json.loads(health_path.read_text())
    assert health['created'] >= finished, 'Repeat the fixed stress probe after the full CLI pilot'
    assert {s['workers'] for s in health['summaries']} == {1, 3, 6}
    healthy = all(s['calls'] == s['matches_original_action'] == s['matches_first_probe'] == 16
                  and not any(s[k] for k in ('invalid', 'fallbacks', 'over_2s')) for s in health['summaries'])
    reliable = all(raw_reliability(db, args.batch, arm) for arm in plan['capacity_pilot_arms'])
    manifest = ledger.meta(db, 'manifest')
    used = db.execute('select count(*) from attempts').fetchone()[0] + db.execute('select count(*) from auxiliary_games').fetchone()[0]
    measured = count / duration * 60
    rate = .85 * measured
    now = time.time()
    confirmation, selection = 1920, 2 * (80 * 12 + 8 * 28)
    capacity = []
    for groups in (170, 100):
        final = 2 * (groups * 12 + 16 * 28)
        development_finish = now + (confirmation + selection) / rate * 60
        final_finish = now + (confirmation + selection + final) / rate * 60 + 2700
        fits = (healthy and reliable and development_finish < manifest['candidate_generation_deadline']
                and final_finish < manifest['deadline'] and used + confirmation + selection <= 13000
                and used + confirmation + selection + final + 16 <= 18000)
        capacity.append({'core_groups': groups, 'final_games': final, 'development_finish': development_finish,
                         'final_finish_with_45m_margin': final_finish, 'fits': fits})
    result = {'created': now, 'fits_remaining_plan': any(c['fits'] for c in capacity),
              'pilot_batch': args.batch, 'workers': plan['capacity_pilot_workers'],
              'measured_games_per_minute': measured, 'conservative_games_per_minute': rate,
              'health_sha256': sha(health_path), 'health_passed': healthy, 'full_cli_reliable': reliable,
              'recovery_plan_sha256': sha(RUN / 'resource-recovery-plan.json'),
              'used_full_attempts': used, 'confirmation_games': confirmation, 'selection_games': selection,
              'capacity': capacity, 'outcomes_used': False,
              'capacity_epoch': 'Only the recovered pilot and fresh recovered confirmation estimate future capacity. Earlier slow resource-incident rates remain archived and disclosed.'}
    ledger.atomic(RUN / 'resource-recovery-capacity.json', result)
    ledger.atomic(RUN / (args.batch + '-capacity.json'), result)
    if args.close_original_confirmation:
        assert result['fits_remaining_plan']
        previous = [list(r) for r in db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key")]
        digest = hashlib.sha256(json.dumps(previous).encode()).hexdigest()
        with db:
            db.execute("update tasks set status='not_run_resource_epoch_reset' where batch='confirmation-arcane' and status='pending'")
            db.execute("update batches set status='closed_resource_epoch_reset' where id='confirmation-arcane'")
        current = [list(r) for r in db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key")]
        assert hashlib.sha256(json.dumps(current).encode()).hexdigest() == digest
        ledger.atomic(RUN / 'confirmation-resource-reset.json', {'created': now, 'preserved_completed': len(previous),
                      'result_digest': digest, 'original_outcomes_inspected': False,
                      'new_plan': plan['confirmation_after_recovery'], 'capacity_sha256': sha(RUN / 'resource-recovery-capacity.json')})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
