"""Pre-outcome capacity fallback after an observed host-resource change."""
import hashlib
import json
import time
from development.secret_hunter_astra_sprint.study import RUN, register, ZIP_SHA
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.release import raw_reliability
from development.secret_hunter_program.common import sha


def main():
    db = ledger.connect(RUN)
    assert not ledger.meta(db, 'pid') and not ledger.meta(db, 'cf_pid')
    assert not ledger.meta(db, 'selection_opened', False) and not ledger.meta(db, 'final_opened', False)
    assert db.execute("select count(*) from attempts where status='running'").fetchone()[0] == 0
    assert sha(RUN / 'DARCL2-fallback.zip') == ZIP_SHA
    probe_path = RUN / 'resource-probe-loaded-detail.json'
    probe = json.loads(probe_path.read_text())
    measured = []
    for workers in (3, 6):
        batch = f'resource-pilot-c{workers}'
        assert db.execute('select status from batches where id=?', (batch,)).fetchone()[0] == 'done'
        performance = json.loads((RUN / (batch + '-performance.json')).read_text())
        stress = next(r for r in probe['summaries'] if r['workers'] == workers)
        assert raw_reliability(db, batch, 'DARCL2')
        assert all(not performance[k] for k in ('over_2s', 'fallbacks', 'policy_errors', 'opponent_errors'))
        assert all(not stress[k] for k in ('over_2s', 'fallbacks', 'invalid'))
        assert stress['matches_first_probe'] == stress['calls']
        measured.append(performance)
    selected = max(measured, key=lambda r: r['games_per_minute'])
    rate = .85 * selected['games_per_minute']
    manifest = ledger.meta(db, 'manifest')
    used = db.execute('select count(*) from attempts').fetchone()[0] + db.execute('select count(*) from auxiliary_games').fetchone()[0]
    remaining_confirmation = db.execute("select count(*) from tasks where batch='confirmation-arcane' and status!='done'").fetchone()[0]
    assert remaining_confirmation > 0
    # Even this optimistic path reuses all earlier confirmation work. A fresh
    # resource-consistent confirmation would require still more time.
    challenge_minimum = remaining_confirmation + 2 * (80 * 12 + 8 * 28) + 2 * (100 * 12 + 16 * 28)
    now = time.time()
    optimistic_finish = now + challenge_minimum / rate * 60 + 2700
    assert optimistic_finish > manifest['deadline'], 'A challenger path still fits; do not invoke capacity fallback'

    def fits(groups):
        games = groups * 12 + 16 * 28
        return used + games + 8 <= manifest['limits']['full_games'] and now + games / rate * 60 + 2700 < manifest['deadline']

    groups = 170 if fits(170) else 100
    assert fits(groups), 'Even the minimum baseline final pool does not fit; retain exact fallback and record incomplete validation explicitly'
    old_rows = list(db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key"))
    completed_digest = hashlib.sha256(json.dumps([list(r) for r in old_rows]).encode()).hexdigest()
    capacity = {'created': now, 'cause': 'Observed host-resource change before selection or final opening',
                'workers': selected['workers'], 'conservative_games_per_minute': rate,
                'measured': measured, 'resource_probe_sha256': sha(probe_path),
                'used_full_attempts': used, 'remaining_confirmation': remaining_confirmation,
                'optimistic_challenger_minimum_remaining_games': challenge_minimum,
                'optimistic_challenger_finish_utc': optimistic_finish, 'deadline_utc': manifest['deadline'],
                'groups': groups, 'guard_groups': 16, 'final_games': groups * 12 + 448,
                'selection_games': 0, 'protocol_pack_margin_s': 2700,
                'completed_confirmation_games': len(old_rows), 'completed_confirmation_digest': completed_digest,
                'outcomes_used_for_capacity_decision': False}
    reason = 'Measured current-load CLI capacity cannot finish even the optimistic remaining confirmation, selection, and minimum two-arm final comparison before the original deadline. DA2 confirmation is incomplete, not a negative strategy result. Retain exact original DARCL2 and complete a fixed single-arm core/guard reliability and protocol acceptance.'
    decision = {'created': now, 'candidate': 'DA2', 'decision': 'not_completed_resource_capacity',
                'reason': reason, 'capacity': capacity, 'no_outcome_inspection': True}
    assert not (RUN / 'hypotheses/H3-confirmation-decision.json').exists()
    ledger.atomic(RUN / 'hypotheses/H3-confirmation-decision.json', decision)
    ledger.atomic(RUN / 'resource-capacity.json', capacity)
    if groups != manifest['final_target']['seeds_core']:
        ledger.atomic(RUN / 'manifest-before-capacity.json', manifest)
        manifest['seed_blocks']['final_core'][1] = manifest['seed_blocks']['final_core'][0] + groups - 1
        manifest['final_target'].update(seeds_core=groups, per_arm_core=groups * 12)
        ledger.atomic(RUN / 'manifest.json', manifest)
        ledger.setmeta(db, 'manifest', manifest)
    candidates = register(db)
    plan = {'created': now, 'arms': ['DARCL2'], 'workers': selected['workers'], 'selection_skipped': True,
            'reason': reason, 'capacity': capacity}
    selection = {'created': now, 'challenger': 'DARCL2', 'ranking': [],
                 'fingerprints': {'DARCL2': candidates['DARCL2']['sha256']},
                 'selection_skipped': True, 'reason': reason, 'no_retuning': True}
    for name, value in [('development-decision.json', {'candidates': [], 'reason': reason, 'capacity': capacity}),
                        ('selection-plan.json', plan), ('selection-decision.json', selection),
                        ('final-capacity.json', capacity)]:
        assert not (RUN / name).exists()
        ledger.atomic(RUN / name, value)
    with db:
        db.execute("update tasks set status='not_run_resource_capacity' where batch='confirmation-arcane' and status='pending'")
        db.execute("update batches set status='closed_resource_capacity' where id='confirmation-arcane'")
    new_rows = list(db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key"))
    assert hashlib.sha256(json.dumps([list(r) for r in new_rows]).encode()).hexdigest() == completed_digest
    ledger.setmeta(db, 'selection_opened', True)  # Close development without using selection seeds.
    ledger.setmeta(db, 'selected_challenger', 'DARCL2')
    ledger.setmeta(db, 'selection_closed_without_challenger', True)
    print(json.dumps({'reason': reason, 'capacity': capacity}, indent=2))


if __name__ == '__main__':
    main()
