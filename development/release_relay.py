"""Promote only the relay instruction revision after three clean exact-relay skill games."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from development.benchmarks.run import fingerprint

def main():
    source=Path('development/candidates/v5-relay')
    base=Path('development/checkpoints/v2-paladin-champion')
    experiment=Path('development/experiments/integration-relay-v2')
    results=[json.loads(p.read_text()) for p in sorted(experiment.glob('*/result.json'))]
    assert len(results)==3,'Wait for all three actual results'
    assert all(r['reason']=='hero_death' for r in results)
    assert all(not any(r['illegal_counts'].values()) and not any(r['timeouts'].values()) for r in results)
    subprocess.run([sys.executable,'-m','development.benchmarks.model_audit',str(experiment),'--skill',str(source),
                    '--out','development/reports/model-audit-relay-v2.json'],check=True)
    fidelity=json.loads(Path('development/reports/model-audit-relay-v2.json').read_text())
    assert fidelity['decisions']==fidelity['exact_policy_matches']==fidelity['script_invoked_and_relayed']
    for p in base.rglob('*'):
        if p.is_file() and p.suffix in ('.py','.json'):
            assert p.read_bytes()==(source/p.relative_to(base)).read_bytes(),p
    checkpoint=Path('development/checkpoints/v3-paladin-relay-champion')
    shutil.copytree(source,checkpoint,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(source,'submission/hearthstone-agent',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    record=json.loads(Path('development/checkpoints/CHAMPION.json').read_text())
    record.update(champion=checkpoint.name,path=str(checkpoint),sha256=fingerprint(checkpoint),
                  previous='v2-paladin-champion',policy_checkpoint=str(base),
                  release_integration=str(experiment),release_integration_games=3,
                  release_action_fidelity=fidelity['decisions'],
                  provenance='Same validated Paladin policy/deck/config; only Skill transport wording changed. Three real Luna games completed without forfeits and with exact per-seq script relay.')
    Path('development/checkpoints/CHAMPION.json').write_text(json.dumps(record,indent=2))
    print('Promoted',checkpoint.name)

if __name__=='__main__':main()
