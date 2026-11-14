"""Read-only final identity, budget, separation and completeness audit."""
import json
from pathlib import Path
import time
from zipfile import ZipFile

from development.benchmarks.run import fingerprint
from development.secret_hunter_long.study import RUN, ROOT, HERE, check, deck_check, ZIP_SHA
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import sha


def main():
    db = train.connect(RUN)
    manifest = train.meta(db, 'manifest')
    check(manifest)
    assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
    assert not train.meta(db, 'pid') and not train.meta(db, 'cf_pid')
    assert not db.execute("select count(*) from batches where status!='done'").fetchone()[0]
    assert not db.execute("select count(*) from tasks where status!='done'").fetchone()[0]
    attempts = {table: dict(db.execute(f'select status,count(*) from {table} group by status').fetchall())
                for table in ('attempts', 'cf_attempts', 'auxiliary_games')}
    assert all(not states.get('running') for states in attempts.values())
    full = sum(attempts['attempts'].values()) + sum(attempts['auxiliary_games'].values())
    cf = sum(attempts['cf_attempts'].values())
    assert full <= manifest['limits']['full_games'] and cf <= manifest['limits']['continuations']
    opening = db.execute("select min(a.started) from attempts a join tasks t on t.key=a.task where t.phase in ('final_core','final_guard')").fetchone()[0]
    assert opening
    before = db.execute('select count(*) from attempts where started<?', (opening,)).fetchone()[0]
    before += db.execute('select count(*) from auxiliary_games where started<?', (opening,)).fetchone()[0]
    assert before <= manifest['limits']['full_games'] - manifest['reserved_final_games']
    # Darwin monotonic timings exclude host suspension. Preserve elapsed UTC
    # alongside active game duration to detect another sleep during final runs.
    final_gaps = []
    for started, finished, raw in db.execute(
            "select a.started,a.finished,t.result from attempts a join tasks t on t.key=a.task "
            "where t.phase in ('final_core','final_guard') and a.status='done'"):
        result = json.loads(raw)
        final_gaps.append(finished - started - result['wall_s'])
    assert final_gaps and max(final_gaps) <= 10, 'Final run crossed a possible host suspension; inspect timing before delivery'
    assert time.time() < manifest['deadline'], 'Original wall-clock budget expired'
    phases = {}
    for phase in ('development', 'cli_development', 'selection', 'final_core', 'final_guard'):
        phases[phase] = {r[0] for r in db.execute('select distinct seed from tasks where phase=?', (phase,))}
    finals = phases['final_core'] | phases['final_guard']
    assert not finals & (phases['development'] | phases['cli_development'] | phases['selection'])
    assert not phases['final_core'] & phases['final_guard']
    for item in json.loads((HERE / 'lineage.json').read_text()):
        source = HERE / 'candidates' / item['name']
        assert fingerprint(source) == item['sha256']
        assert deck_check(source) == item['deck']
    recommendation = json.loads((ROOT / 'docs/secret_hunter_long/recommendation.json').read_text())
    package = Path(recommendation['zip'])
    assert sha(package) == recommendation['zip_sha256']
    if recommendation['recommended'] == 'B':
        assert sha(package) == ZIP_SHA
    with ZipFile(package) as archive:
        members = archive.infolist()
        assert {m.filename.split('/')[0] for m in members} == {'secret-hunter'}
        assert 'secret-hunter/SKILL.md' in archive.namelist()
        assert all('..' not in Path(m.filename).parts and not m.filename.startswith('/') for m in members)
        assert all(Path(m.filename).suffix in ('.py', '.json', '.md') for m in members if not m.is_dir())
        unpacked_bytes = sum(m.file_size for m in members)
        assert unpacked_bytes <= 10_000_000 and package.stat().st_size <= 10_000_000
    freeze = json.loads((RUN / 'final-freeze.json').read_text())
    frozen_records = json.loads((RUN / 'release-candidates.json').read_text())
    for record in frozen_records:
        assert fingerprint(ROOT / record['extracted']) == freeze['fingerprints'][record['name']]
        assert sha(ROOT / record['path']) == record['zip_sha256']
    exact_paths = {r['name']: (ROOT / r['extracted']).resolve() for r in frozen_records}
    verified_final_requests = 0
    for attempt, candidate, raw in db.execute(
            "select a.id,t.candidate,t.result from attempts a join tasks t on t.key=a.task "
            "where t.phase in ('final_core','final_guard')"):
        request = json.loads((RUN / 'attempts' / f'{attempt:06d}.request.json').read_text())
        assert request['full_cli'] is True
        assert Path(request['task'][0]).resolve() == exact_paths[candidate]
        assert json.loads(raw)['execution'] == 'full_cli'
        verified_final_requests += 1
    result = {'created': time.time(), 'passed': True, 'attempts_by_status': attempts,
              'full_attempts_including_auxiliary': full, 'counterfactual_attempts': cf,
              'full_attempts_before_final': before,
              'reserved_capacity_at_final_opening': manifest['limits']['full_games'] - before,
              'final_attempt_utc_minus_active_max_s': max(final_gaps),
              'final_host_suspend_gap_over_10s': sum(x > 10 for x in final_gaps),
              'final_attempts_from_exact_frozen_paths': verified_final_requests,
              'elapsed_hours_from_manifest': (time.time() - manifest['created']) / 3600,
              'final_source_seed_groups': {k: len(v) for k, v in phases.items() if k.startswith('final')},
              'recommended': recommendation['recommended'], 'zip_sha256': sha(package),
              'zip_bytes': package.stat().st_size, 'uncompressed_bytes': unpacked_bytes,
              'engine_opponents_candidates_unchanged': True, 'sqlite_integrity': 'ok'}
    train.atomic(ROOT / 'docs/secret_hunter_long/delivery-audit.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
