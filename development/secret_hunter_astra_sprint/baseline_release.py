"""Close development without a challenger only after its registered rejection."""
import json
import time
from development.secret_hunter_astra_sprint.study import RUN, register, ZIP_SHA
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import sha


def main():
    db = ledger.connect(RUN)
    assert not ledger.meta(db, 'pid') and not ledger.meta(db, 'cf_pid')
    assert not ledger.meta(db, 'selection_opened', False)
    assert not ledger.meta(db, 'final_opened', False)
    decisions = {}
    for name in ('H1-full-decision', 'H2-full-decision', 'H4-full-decision', 'H3-confirmation-decision'):
        path = RUN / 'hypotheses' / (name + '.json')
        record = json.loads(path.read_text())
        rejected = ('Do not advance from first full-game test; retain immutable diagnostic control'
                    if name == 'H1-full-decision' else 'do_not_advance')
        assert record['decision'] == rejected, (name, record['decision'])
        decisions[name] = sha(path)
    assert sha(RUN / 'DARCL2-fallback.zip') == ZIP_SHA
    assert db.execute("select status from batches where id='confirmation-arcane'").fetchone()[0] == 'done'
    candidates = register(db)
    manifest = ledger.meta(db, 'manifest')
    used = db.execute('select count(*) from attempts').fetchone()[0] + db.execute('select count(*) from auxiliary_games').fetchone()[0]
    # Use the predeclared maximum final size; outcomes have never been opened.
    final_games = manifest['final_target']['per_arm_core'] + manifest['final_target']['per_arm_guard']
    rates = [json.loads((RUN / 'throughput.json').read_text())['pilot-c6']['games_per_minute']]
    for batch in ('round3-arcane', 'round4-hand-resource', 'confirmation-arcane'):
        n, elapsed = db.execute('select count(*),max(a.finished)-min(a.started) from attempts a join tasks t on t.key=a.task where t.batch=?', (batch,)).fetchone()
        rates.append(n / elapsed * 60)
    rate = .85 * min(rates)
    assert used + final_games + 8 <= manifest['limits']['full_games']
    assert time.time() + final_games / rate * 60 + 2700 < manifest['deadline']
    reason = 'Every challenger was rejected by its registered natural-frequency full-game check. Retain the original DARCL2 bytes and validate only that fixed baseline. No selection seed or final outcome informed this decision.'
    capacity = {'created': time.time(), 'before_final_opening': True, 'groups': manifest['final_target']['seeds_core'],
                'guard_groups': manifest['final_target']['seeds_guard'], 'workers': 6,
                'used_full_attempts': used, 'final_games': final_games, 'selection_games': 0,
                'conservative_games_per_minute': rate, 'protocol_pack_margin_s': 2700}
    plan = {'created': time.time(), 'arms': ['DARCL2'], 'workers': 6, 'selection_skipped': True,
            'reason': reason, 'decision_sha256': decisions, 'capacity': capacity}
    selection = {'created': time.time(), 'challenger': 'DARCL2', 'ranking': [],
                 'fingerprints': {'DARCL2': candidates['DARCL2']['sha256']},
                 'selection_skipped': True, 'reason': reason, 'no_retuning': True}
    for name, value in [('development-decision.json', {'candidates': [], 'reason': reason, 'decision_sha256': decisions}),
                        ('selection-plan.json', plan), ('selection-decision.json', selection),
                        ('final-capacity.json', capacity)]:
        assert not (RUN / name).exists()
        ledger.atomic(RUN / name, value)
    ledger.setmeta(db, 'selection_opened', True)  # Lock further development; no selection games were run.
    ledger.setmeta(db, 'selected_challenger', 'DARCL2')
    ledger.setmeta(db, 'selection_closed_without_challenger', True)
    print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    main()
