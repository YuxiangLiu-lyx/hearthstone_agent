"""Repeat fixed public CLI inputs with full search metadata, without games."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from development.secret_hunter_astra_sprint.study import RUN, HERE
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_astra_sprint.tactical import digest
from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import sha, quantiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--workers', type=int, nargs='+', default=[1, 3, 6])
    args = parser.parse_args()
    output = RUN / f'resource-probe-{args.label}.json'
    assert not output.exists()
    source = HERE / 'candidates/DARCL2'
    source_hash = fingerprint(source)
    stress_path = RUN / 'runtime-stress-cases.json'
    cases = json.loads(stress_path.read_text())['cases']
    originals = []
    for case in cases:
        rows = [json.loads(line) for line in Path(case['log_path']).read_text().splitlines()]
        matching = [r for r in rows if digest(r['state']) == case['digest']]
        assert len(matching) == 1
        originals.append(matching[0])
    sys.path.insert(0, str(source / 'scripts'))
    from action_validator import legal

    def probe(i):
        state = cases[i]['state']
        with tempfile.TemporaryDirectory(prefix='astra-resource-') as temporary:
            folder = Path(temporary) / 'skill'
            shutil.copytree(source, folder, ignore=shutil.ignore_patterns('__pycache__', 'game', 'scratch'))
            (folder / 'game').mkdir()
            (folder / 'game/state.json').write_text(json.dumps(state))
            start = time.monotonic()
            process = subprocess.run([sys.executable, 'scripts/decide.py'], cwd=folder,
                                     capture_output=True, text=True, timeout=3, check=True)
            elapsed = time.monotonic() - start
            envelope = json.loads(process.stdout)
            record = json.loads((folder / 'scratch/decisions.jsonl').read_text().splitlines()[-1])
            assert envelope == {'seq': state['seq'], 'action': record['action']}
            return {'case_index': i, 'state_digest': cases[i]['digest'], 'elapsed_s': elapsed,
                    'valid': legal(state, record['action']), 'record': record,
                    'matches_original_action': record['action'] == originals[i]['action'],
                    'original_action': originals[i]['action'], 'original_info': originals[i]['info']}

    records = []
    summaries = []
    reference = None
    for workers in args.workers:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(probe, range(len(cases))))
        if reference is None:
            reference = [r['record']['action'] for r in rows]
        summary = {'workers': workers, 'calls': len(rows), 'latency_s': quantiles([r['elapsed_s'] for r in rows]),
                   'matches_first_probe': sum(r['record']['action'] == reference[i] for i, r in enumerate(rows)),
                   'matches_original_action': sum(r['matches_original_action'] for r in rows),
                   'invalid': sum(not r['valid'] for r in rows),
                   'fallbacks': sum(bool(r['record']['info'].get('fallback')) for r in rows),
                   'over_2s': sum(r['elapsed_s'] > 2 for r in rows)}
        summaries.append(summary)
        records.extend({'workers': workers, **r} for r in rows)
        print(json.dumps(summary), flush=True)
        ledger.atomic(output, {'created': time.time(), 'source_sha256': source_hash,
                              'stress_sha256': sha(stress_path), 'summaries': summaries, 'records': records,
                              'scope': 'Previously fixed public states only, no new games or outcome-based choices. Cold contexts; baseline plan_cache is disabled. Full search metadata retained to distinguish timing cutoffs from policy changes.'})
    assert fingerprint(source) == source_hash


if __name__ == '__main__':
    main()
