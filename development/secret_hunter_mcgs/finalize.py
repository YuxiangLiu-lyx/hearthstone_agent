"""Apply preregistered promotion gates only to complete frozen final results."""
import json
from development.secret_hunter_mcgs.train import atomic,meta,setmeta
from development.secret_hunter_mcgs.build import ROOT

def finalize(db,run):
    paths=[run/'batches'/b/'report.json' for b in ('final-core','final-guard')]
    if not all(p.exists() for p in paths):return
    core,guard=[json.loads(p.read_text()) for p in paths];name=meta(db,'challenger')
    primary=core['comparisons'][name]['primary'];old=guard['comparisons'][name]['all']
    families=core['comparisons'][name]['by_group'];limits=meta(db,'manifest')['promotion']
    runtime_path=run/'final-cli.json'
    if not runtime_path.exists():
        import subprocess,sys
        subprocess.run([sys.executable,'-m','development.secret_hunter_mcgs.runtime',
                        '--candidate',meta(db,'candidates')[name]['path'],'--out',str(runtime_path)],check=True,cwd=ROOT)
    runtime=json.loads(runtime_path.read_text())
    failures=[]
    if primary['gain']<limits['primary_gain_min']:failures.append('primary_gain_below_1pp')
    if primary['gain_seed_cluster_95'][0]<=0:failures.append('primary_interval_includes_zero')
    if any(families[g]['gain'] < -limits['family_regression_limit'] for g in ('astra','bot2')):failures.append('family_regression')
    if old['gain'] < -limits['guard_regression_limit']:failures.append('old_pool_regression')
    if runtime['invalid'] or runtime['over_2s'] or runtime['ordinary_fallbacks']:failures.append('cli_reliability')
    for report in (core,guard):
        for arm in ('Y1',name):
            a=report['arms'][arm]['all']
            if any(a[k] for k in ('harness_errors','illegal','timeouts','forfeits','policy_errors','over_2s','public_input_violations')):failures.append('match_reliability:'+arm)
    result={'challenger':name,'promoted':not failures,'failed_gates':failures,'primary':primary,'old_pool':old,
            'recommendation':name if not failures else 'Y1','scope':'Complete frozen local proxy comparison; not official course results.'}
    atomic(run/'final-result.json',result);setmeta(db,'promotion',result)
    text='# Frozen final comparison\n\n'+json.dumps(result,indent=2)+'\n'
    (run/'FINAL_REPORT.md').write_text(text)
