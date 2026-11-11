"""Promote only after paired, latency, exact-ZIP and official relay gates pass."""
import json,shutil
from datetime import datetime,timezone
from development.secret_hunter_program.common import ROOT,sha,write
from development.benchmarks.run import fingerprint
O=ROOT/'docs/secret_hunter_tactics';D=ROOT/'development/secret_hunter_tactics'
read=lambda p:json.loads((ROOT/p).read_text())
paired=read('docs/secret_hunter_tactics/final-paired.json')['primary']
metrics=read('docs/secret_hunter_tactics/experiments.json');runtime=read('docs/secret_hunter_tactics/runtime-checks-final.json')
relay=read('docs/secret_hunter_tactics/relay-audit.json');client=read('docs/secret_hunter_tactics/client-audit.json')
rep=read('docs/secret_hunter_tactics/reproduction.json');manifest=read('dist/secret-hunter-tactics.manifest.json')
freeze=read('docs/secret_hunter_tactics/freeze.json');verified=read('docs/secret_hunter_tactics/verification.json')
budget=read('docs/secret_hunter_tactics/budget.json')
checks=[read('docs/secret_hunter_tactics/checks-final.json'),read('docs/secret_hunter_tactics/tactical-checks.json')]
gates={'paired_gain':paired['gain']>=.01 and paired['gain_seed_cluster_95'][0]>0,
 'python_reliability':all(not m['policy_errors'] and not m['fallbacks'] and not m['over_2s'] and all(m['summary']['all'][k]==0 for k in ('illegal','timeouts','forfeits','opponent_errors')) for m in metrics.values()),
 'runtime':runtime['over_2s']==0 and runtime['illegal']==0,
 'mechanisms':all(x['errors']==0 and x['failures']==0 for x in checks),
 'reproduction':rep['games']==rep['same_outcomes']==rep['identical_action_traces']==56,
 'client':client['games']==2 and client['relay_deviations']==0,
 'official_relay':relay['games']>=1 and relay['attempts']<=2 and relay['relay_deviations']==0 and all(not r['worker_errors'] and not r['fallbacks'] and not r['result']['reason'].startswith('forfeit') for r in relay['reports']) and all(not p['accepted_deviations'] and not p['request_deviations'] and not p['worker_errors'] and not p['fallbacks'] for p in relay['interrupted_attempts']),
 'freeze_integrity':verified['baseline_tree_unchanged'] and fingerprint(ROOT/manifest['extracted'])==manifest['candidate_sha256'],
 'budget':budget['full_game_attempts_charged']<=6000 and budget['short_continuations_used']<=20000 and budget['elapsed_wall_seconds']<=14400}
if not all(gates.values()):
    write(O/'promotion.json',{'promoted':False,'gates':gates,'retained':'F2'});print('F2 RETAINED',gates);raise SystemExit(1)
assert not (O/'archive.json').exists(),'Already promoted; inspect the existing archive instead of repeating mutation.'
assert sha(ROOT/'dist/secret-hunter-program.zip')==freeze['protected']['dist/secret-hunter-program.zip']
# Preserve the complete previous source tree, original ZIP, original manifest and marker.
archive=D/'previous-champion/secret-hunter-program';archive.parent.mkdir(parents=True,exist_ok=False)
shutil.copy2(O/'verification.json',O/'verification-before-promotion.json')
shutil.copy2(ROOT/'dist/secret-hunter-program.zip',ROOT/'dist/secret-hunter-program-f2.zip')
shutil.copy2(ROOT/'dist/secret-hunter-program.manifest.json',ROOT/'dist/secret-hunter-program-f2.manifest.json')
shutil.move(str(ROOT/'secret-hunter-program'),str(archive))
assert fingerprint(archive)==freeze['baseline_sha256']
shutil.copytree(ROOT/manifest['extracted'],ROOT/'secret-hunter-program',ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
shutil.copy2(ROOT/manifest['zip'],ROOT/'dist/secret-hunter-program.zip')
canonical={**manifest,'zip':'dist/secret-hunter-program.zip','source':'secret-hunter-program','status':'Promoted local program champion H7 after frozen paired and exact-host checks.'}
write(ROOT/'dist/secret-hunter-program.manifest.json',canonical)
marker={'status':'local_program_champion','candidate':'H7','source':'secret-hunter-program','zip':'dist/secret-hunter-program.zip',
 'zip_sha256':manifest['zip_sha256'],'source_sha256':manifest['candidate_sha256'],'base_commit':'6a7fc2475a17190268594ef2f5940b5b3a62f8f0',
 'baseline':'development/secret_hunter_tactics/candidates/B0','paired':paired,'reliability_passed':True,
 'official_host_scope':f"One completed exact H7 ZIP Luna-medium host game; {relay['decisions']}/{relay['decisions']} actions match current-sequence script output. A second attempt was externally interrupted, with 26/26 accepted actions and 27/27 requests matching the script; it has no complete-game result. Runtime policy has no model calls; the course relay host does.",
 'updated_utc':datetime.now(timezone.utc).isoformat(),'official_submission':False,'report':'docs/secret_hunter_tactics/REPORT.md'}
write(ROOT/'SECRET_HUNTER_CHAMPION.json',marker)
archive_map={'secret-hunter-program/':str(archive.relative_to(ROOT))+'/',
 'dist/secret-hunter-program.zip':'dist/secret-hunter-program-f2.zip',
 'dist/secret-hunter-program.manifest.json':'dist/secret-hunter-program-f2.manifest.json',
 'SECRET_HUNTER_CHAMPION.json':'docs/secret_hunter_tactics/previous-champion.json'}
write(O/'archive.json',{'previous_candidate':'F2','previous_source_sha256':fingerprint(archive),
 'previous_zip_sha256':sha(ROOT/'dist/secret-hunter-program-f2.zip'),'protected_path_mapping':archive_map})
assert fingerprint(ROOT/'secret-hunter-program')==manifest['candidate_sha256']
write(O/'promotion.json',{'promoted':True,'gates':gates,'candidate':'H7','previous':'F2','archive':archive_map,
 'canonical_source_sha256':fingerprint(ROOT/'secret-hunter-program'),'canonical_zip_sha256':sha(ROOT/'dist/secret-hunter-program.zip')})
print(json.dumps({'promoted':'H7','gates':gates}))
