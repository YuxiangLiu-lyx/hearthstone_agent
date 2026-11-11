"""Read-only integrity/reliability checks across the new evidence and complete experiments."""
import json
from pathlib import Path
import hs_arena

from development.benchmarks.run import fingerprint
from development.secret_hunter_program.common import ROOT, sha, write, readlines
from development.teacher_eval.compare import index


def main():
    raw=ROOT/'experiments/teacher-submission-1'
    archive=json.loads((raw/'manifest.json').read_text())
    assert all(sha(raw/'raw'/name)==digest for name,digest in archive['files'].items())
    marker=json.loads((ROOT/'SECRET_HUNTER_CHAMPION.json').read_text())
    assert fingerprint(ROOT/marker['source'])==marker['source_sha256']
    assert sha(ROOT/marker['zip'])==marker['zip_sha256']
    assert (ROOT/marker['report']).is_file()
    workspace=json.loads((ROOT/'secret-hunter.code-workspace').read_text())
    assert all((ROOT/f['path']).is_dir() for f in workspace['folders'])
    runtime=json.loads((ROOT/'docs/secret_hunter_program/runtime.json').read_text())
    engine_root=Path(hs_arena.__file__).parent
    assert all(sha(engine_root/name)==digest for name,digest in runtime['installed_files'].items())
    historical=json.loads((ROOT/'docs/secret_hunter_program/opponent_manifest.json').read_text())
    enumerator='development/checkpoints/v3-paladin-relay-champion/scripts/actions.py'
    expected_enumerator={o['dependencies'][enumerator] for o in historical['opponents'] if enumerator in o['dependencies']}
    assert expected_enumerator=={sha(ROOT/enumerator)}
    runs=[];opponent_defects=0
    populations={sha(ROOT/path):json.loads((ROOT/path).read_text()) for path in
                 ('development/teacher_eval/core.json','development/teacher_eval/guardrail.json')}
    for folder in sorted((ROOT/'experiments').glob('teacher-*')):
        if not (folder/'config.json').exists():continue
        cfg=json.loads((folder/'config.json').read_text())
        if 'planned_games' not in cfg:continue
        rows=readlines(folder/'results.jsonl')
        actual=index(rows)
        expected={(o['name'],seed,seat) for o in cfg['population']
                  for seed in range(cfg['start'],cfg['start']+cfg['seeds']) for seat in (1,2)}
        assert actual.keys()==expected,(folder,'incomplete schedule')
        assert {p.name for p in (folder/'games').iterdir() if p.is_dir()}=={r['game'] for r in rows}
        assert len(rows)==cfg['planned_games']
        assert fingerprint(ROOT/cfg['candidate'])==cfg['candidate_sha256']
        # Run manifests embed the complete population instead of a mutable path.
        assert populations[cfg['population_sha256']]==cfg['population']
        assert all(sha(ROOT/name)==digest for name,digest in cfg['code_sha256'].items())
        for spec in cfg['population']:
            version=cfg['opponent_versions'][spec['name']]
            assert sha(ROOT/spec['deck'])==version['deck']
            if spec.get('policy'):assert fingerprint(ROOT/spec['policy'])==version['policy']
        for row in rows:
            result=row['result']
            assert result['reason']=='hero_death', (folder,result)  # All completed matches in this round.
            assert not row['policy_errors'] and not row['fallbacks'] and not row['over_2s'] and row['public_only']
            assert not row['opponent_errors']
            assert not any(result['illegal_counts'].values()) and not any(result['timeouts'].values())
            assert json.loads((folder/'games'/row['game']/'result.json').read_text())==result
        runs.append({'folder':str(folder.relative_to(ROOT)),'games':len(rows),'wins':sum(r['score'] for r in rows),
                     'candidate_sha256':cfg['candidate_sha256']})
    for manifest_path in (ROOT/'dist').glob('secret-hunter-teacher-*.manifest.json'):
        manifest=json.loads(manifest_path.read_text())
        assert sha(ROOT/manifest['zip'])==manifest['zip_sha256']
        assert fingerprint(ROOT/manifest['source'])==fingerprint(ROOT/manifest['extracted'])==manifest['source_sha256']
    report={'complete_python_games':sum(r['games'] for r in runs),'runs':runs,
            'raw_files_sha256_verified':archive['files'],'canonical_champion':marker['candidate'],
            'canonical_source_sha256':marker['source_sha256'],'canonical_zip_sha256':marker['zip_sha256'],
            'workspace_folders_verified':len(workspace['folders']),'both_sides_execution_defects':opponent_defects,
            'historically_frozen_engine_files_verified':len(runtime['installed_files']),
            'scope':'Every scheduled result, frozen source, opponent version and canonical release checked; client games audited separately.'}
    write(ROOT/'docs/teacher_eval/integrity.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='runs'},indent=2))


if __name__=='__main__':
    main()
