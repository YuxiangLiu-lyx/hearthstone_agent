"""Materialize the preregistered selection recipe after development review."""
import json
import time

from development.secret_hunter_long.study import RUN, HERE
from development.secret_hunter_long.select_challenger import ERRORS
from development.secret_hunter_mcgs import train
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha


def main():
    db = train.connect(RUN)
    assert not train.meta(db, 'final_opened', False)
    destination = RUN / 'selection-plan.json'
    if destination.exists():
        print(destination.read_text())
        return
    assert not train.meta(db, 'pid') and not train.meta(db, 'cf_pid')
    assert not train.meta(db, 'selection_opened', False)
    design_path = RUN / 'selection-design.json'
    design = json.loads(design_path.read_text())
    reports = {}
    for batch in ('mulligan-combination', 'cli-load', 'two-card'):
        row = db.execute('select status from batches where id=?', (batch,)).fetchone()
        assert row and row['status'] == 'done'
        reports[batch] = json.loads((RUN / 'batches' / batch / 'report.json').read_text())
    development = reports['mulligan-combination']
    chosen = []
    details = {}
    for family in ('original_deck_line', 'arcane_line'):
        order = design['candidate_recipe'][family]
        rates = {arm: development['comparisons'][arm]['primary']['b_rate'] for arm in order
                 if all(development['arms'][arm]['all'][key] == 0 for key in ERRORS)}
        assert rates, ('No reliable candidate in line', family)
        best = max(rates.values())
        arm = next(a for a in order if a in rates and best - rates[a] <= 1e-12)
        chosen.append(arm)
        details[family] = {'chosen': arm, 'development_primary_rates': rates, 'tie_order': order}
    arms = ['B', *chosen, *design['candidate_recipe']['other_pure_card_lines']]
    assert len(arms) == len(set(arms)) == design['max_arms']
    assert all(reports['two-card']['arms'][arm]['all'][key] == 0
               for arm in design['candidate_recipe']['other_pure_card_lines'] for key in ERRORS)
    load = reports['cli-load']
    load_reliable = all(summary['all'][key] == 0 for summary in load['arms'].values() for key in ERRORS)
    count = sum(summary['all']['n'] for summary in load['arms'].values())
    assert count == 72
    elapsed = db.execute("select max(a.finished)-min(a.started) from attempts a join tasks t on t.key=a.task where t.batch='cli-load'").fetchone()[0]
    rate = count / elapsed * 60
    workers = 6 if load_reliable and rate > 29.6 else 3
    manifest = train.meta(db, 'manifest')
    used = db.execute('select count(*) from attempts').fetchone()[0]
    used += db.execute('select count(*) from auxiliary_games').fetchone()[0]
    planned = len(arms) * (design['core']['seeds'] * 12 + design['guardrail']['seeds'] * 28)
    assert used + planned <= manifest['limits']['full_games'] - manifest['reserved_final_games']
    estimate = rate if workers == 6 else min(29.6, rate)
    selection_seconds = planned / estimate * 60
    final_seconds = 3296 / estimate * 60
    assert time.time() + selection_seconds < manifest['candidate_generation_deadline']
    assert time.time() + selection_seconds + final_seconds + 1800 < manifest['deadline']
    plan = {'created': time.time(), 'arms': arms, 'core': design['core'], 'guardrail': design['guardrail'],
            'workers': workers, 'design_sha256': sha(design_path), 'line_choices': details,
            'candidate_fingerprints': {a: fingerprint(HERE / 'candidates' / a) for a in arms},
            'load': {'n': count, 'elapsed_s': elapsed, 'games_per_minute': rate, 'reliable': load_reliable},
            'budget': {'used_full_including_auxiliary': used, 'selection_full': planned,
                       'capacity_after_selection': manifest['limits']['full_games'] - used - planned,
                       'selection_seconds_estimate': selection_seconds, 'final_seconds_estimate': final_seconds},
            'selection_rule': design['selection_rule'], 'no_retuning_after_selection': True}
    train.atomic(destination, plan)
    print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    main()
