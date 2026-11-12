"""Budgeted official local client smoke test of the exact frozen ZIP contents."""
import json
import subprocess

from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import ROOT, sha, write
from development.secret_hunter_program.relay_audit import audit
from .accounting import reserve, finish, fail

D = ROOT / 'docs/secret_hunter_face_validation'


def main():
    frozen = json.loads((D / 'freeze.json').read_text())
    plan = json.loads((D / 'plan.json').read_text())
    assert sha(D / 'plan.json') == frozen['plan_sha256']
    source = plan['arms']['F2']
    assert fingerprint(ROOT / source) == frozen['source_hashes']['F2']
    output = ROOT / 'experiments/secret-hunter-face-validation-client'
    assert not output.exists()
    name = 'official-client-f2'
    count = plan['client']['games']
    command = [str(ROOT / '.venv/bin/hs-arena'), 'play', '--p1', 'client:' + source,
               '--p2', 'greedy', '--games', str(count), '--parallel', '1',
               '--seed', str(plan['client']['start']), '--out', str(output)]
    reserve(name, full=count, final=True, seconds=300)
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=280)
        (D / 'client-output.txt').write_text(completed.stdout + completed.stderr)
        assert completed.returncode == 0, completed.stderr
        reports = [audit(game, 1) for game in sorted(output.glob('g_*'))]
        assert len(reports) == count
        report = {'command': command, 'candidate_sha256': frozen['source_hashes']['F2'],
                  'games': count, 'decisions': sum(r['decisions'] for r in reports),
                  'relay_deviations': sum(r['relay_deviations'] for r in reports), 'reports': reports,
                  'scope': 'Official local no-model client against Greedy; smoke test only.'}
        write(D / 'client-audit.json', report)
        assert all(not r['relay_deviations'] and not r['worker_errors'] and not r['fallbacks'] for r in reports)
        assert all(not any(r['result']['illegal_counts'].values()) and not any(r['result']['timeouts'].values()) for r in reports)
        finish(name, completed=count, decisions=report['decisions'])
        print(json.dumps({k: v for k, v in report.items() if k not in ('command', 'reports')}))
    except BaseException as exc:
        fail(name, repr(exc))
        raise


if __name__ == '__main__':
    main()
