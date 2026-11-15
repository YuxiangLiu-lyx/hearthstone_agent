"""Deliver verified original bytes when the registered recovery window expires."""
import datetime
import hashlib
import json
import subprocess
import sys
import time
from development.secret_hunter_astra_sprint.study import ROOT, RUN, HERE, ZIP_SHA, BASE_SHA, ANCHOR, check
from development.secret_hunter_astra_sprint import ledger
from development.secret_hunter_program.common import sha
from development.benchmarks.run import fingerprint


def main():
    db = ledger.connect(RUN)
    manifest = ledger.meta(db, 'manifest')
    check(manifest)
    plan = json.loads((RUN / 'resource-recovery-plan.json').read_text())
    cutoff = datetime.datetime.fromisoformat(plan['watch_until_utc']).timestamp()
    assert cutoff <= time.time() < manifest['deadline']
    assert not ledger.meta(db, 'pid') and not ledger.meta(db, 'cf_pid')
    assert not ledger.meta(db, 'selection_opened', False) and not ledger.meta(db, 'final_opened', False)
    assert not (ROOT / 'docs/secret_hunter_astra_sprint/recommendation.json').exists()
    health_paths = list(RUN.glob('resource-probe-health-*.json'))
    latest = max(health_paths, key=lambda p: json.loads(p.read_text())['created'])
    health = json.loads(latest.read_text())
    healthy = any(s['calls'] == 16 and s['matches_original_action'] == 16
                  and not any(s[k] for k in ('invalid', 'fallbacks', 'over_2s')) for s in health['summaries'])
    if healthy:
        capacity = json.loads((RUN / 'resource-recovery-capacity.json').read_text())
        assert not capacity['fits_remaining_plan'], 'Resources recovered: continue the authorized comparison'
    acceptance = json.loads((RUN / 'fallback-acceptance.json').read_text())
    assert acceptance['passed'] and acceptance['source_sha256'] == BASE_SHA and acceptance['games'] == 8
    exact = RUN / 'frozen/DARCL2/secret-hunter'
    output = ROOT / 'dist/secret-hunter-long-20261114.zip'
    assert fingerprint(exact) == BASE_SHA
    assert sha(output) == sha(RUN / 'frozen/DARCL2.zip') == ZIP_SHA
    runtime = json.loads((ROOT / 'docs/secret_hunter_astra_sprint/runtime-DARCL2-loaded.json').read_text())
    assert runtime['invalid'] == runtime['over_2s'] == runtime['ordinary_fallbacks'] == 0
    assert runtime['actual_host_stale_seq_rejected']
    completed = [list(r) for r in db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key")]
    digest = hashlib.sha256(json.dumps(completed).encode()).hexdigest()
    reason = 'Host-resource recovery did not provide a verified feasible path within the registered window. DA2 independent confirmation remains incomplete; no selection or final comparison outcomes were opened. Use the user-authorized exact original DARCL2 fallback. This is insufficient promotion evidence, not a measured negative DA2 result.'
    decision = {'created': time.time(), 'candidate': 'DA2', 'decision': 'not_completed_resource_capacity',
                'reason': reason, 'completed_baseline_confirmation_games': len(completed),
                'completed_result_digest': digest, 'outcomes_used_for_resource_decision': False,
                'latest_health_sha256': sha(latest), 'recovery_plan_sha256': sha(RUN / 'resource-recovery-plan.json')}
    ledger.atomic(RUN / 'hypotheses/H3-confirmation-decision.json', decision)
    with db:
        db.execute("update tasks set status='not_run_resource_capacity' where batch='confirmation-arcane' and status='pending'")
        db.execute("update batches set status='closed_resource_capacity' where id='confirmation-arcane'")
    assert hashlib.sha256(json.dumps([list(r) for r in db.execute("select key,result from tasks where batch='confirmation-arcane' and status='done' order by key")]).encode()).hexdigest() == digest
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    freeze = {'created': time.time(), 'artifact_role': 'Original fallback delivery; no frozen final comparison exists',
              'source_anchor_commit': ANCHOR, 'research_commit': commit, 'zip_sha256': ZIP_SHA,
              'source_sha256': BASE_SHA, 'exact_path': str(exact.relative_to(ROOT)),
              'engine_versions': manifest['versions'], 'engine_source_files': manifest['engine'],
              'opponents': manifest['opponents'], 'manifest_sha256': sha(RUN / 'manifest.json'),
              'final_seeds_opened': False, 'paired_final_validation_complete': False,
              'analysis_sources': {str((HERE / n).relative_to(ROOT)): sha(HERE / n)
                                   for n in ('finalize_fallback.py', 'fallback_evidence.py', 'verify_delivery.py')}}
    ledger.atomic(RUN / 'delivery-freeze.json', freeze)
    rec = {'created': time.time(), 'recommended': 'DARCL2', 'challenger': 'DA2', 'promoted': False,
           'reason': reason, 'paired_final_validation_complete': False, 'selection_skipped': True,
           'gates': {'independent_confirmation_complete': False, 'independent_selection_complete': False,
                     'final_paired_samples_complete': False, 'exact_fallback_sha_verified': True,
                     'fallback_protocol_passed': True, 'fallback_phase_and_2s_checks_passed': True,
                     'loaded_concurrency6_action_stability': all(r['actions_identical'] for r in runtime['concurrency_action_stability'])},
           'primary': None, 'family_gains': None, 'astra_proxy_gains': None, 'guard_gain': None,
           'zip': str(output), 'zip_sha256': ZIP_SHA, 'bytes': output.stat().st_size,
           'source_sha256': BASE_SHA, 'source_commit': ANCHOR, 'research_source_commit': commit,
           'final_exact_unpacked_path': str(exact.relative_to(ROOT)),
           'deck': json.loads((RUN / 'fallback-deck-audit.json').read_text()),
           'scope': 'Original unchanged fallback only. No new formal score and no demonstrated Astra improvement. User makes the Slack submission.'}
    ledger.atomic(ROOT / 'docs/secret_hunter_astra_sprint/recommendation.json', rec)
    ledger.setmeta(db, 'recommendation', 'DARCL2')
    ledger.setmeta(db, 'development_closed', True)
    # All eight already completed exact-path records are checked and reused;
    # relay refuses incomplete records and verifies their candidate identity.
    subprocess.run([sys.executable, '-m', 'development.secret_hunter_astra_sprint.accept_frozen'], cwd=ROOT, check=True)
    evidence = json.loads((RUN / 'fallback-validation.json').read_text())
    evidence.update(artifact_role='Final original fallback delivery; no final paired study',
                    recommendation=rec, delivery_freeze=freeze,
                    paired_final_validation_complete=False)
    ledger.atomic(RUN / 'final-validation.json', evidence)
    ledger.atomic(ROOT / 'docs/secret_hunter_astra_sprint/final-validation.json', evidence)
    print(json.dumps({k: v for k, v in rec.items() if k != 'deck'}, indent=2))


if __name__ == '__main__':
    main()
