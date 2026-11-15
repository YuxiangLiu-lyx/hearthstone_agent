"""Execute only the eight predeclared protocol games for the recommended ZIP."""
import argparse
import json
import shutil
import subprocess
import sys
from zipfile import ZipFile

from development.benchmarks.run import fingerprint
from development.secret_hunter_astra_sprint.study import ROOT, RUN, ZIP_SHA, BASE_SHA
from development.secret_hunter_astra_sprint import ledger as train
from development.secret_hunter_program.common import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fallback-first', action='store_true')
    args = parser.parse_args()
    plan_path = RUN / 'final-acceptance-plan.json'
    plan = json.loads(plan_path.read_text())
    plan_sha = sha(plan_path)
    recommendation_path = ROOT / 'docs/secret_hunter_astra_sprint/recommendation.json'
    if args.fallback_first:
        db = train.connect(RUN)
        assert not train.meta(db, 'final_opened', False)
        package = RUN / 'frozen/DARCL2.zip'
        package.parent.mkdir(exist_ok=True)
        assert sha(RUN / 'DARCL2-fallback.zip') == ZIP_SHA
        if not package.exists():shutil.copy2(RUN / 'DARCL2-fallback.zip', package)
        assert sha(package) == ZIP_SHA
        extracted = RUN / 'frozen/DARCL2'
        if not extracted.exists():
            extracted.mkdir()
            with ZipFile(package) as archive:archive.extractall(extracted)
        candidate = extracted / 'secret-hunter'
        assert fingerprint(candidate) == BASE_SHA
        recommendation = {'recommended': 'DARCL2', 'final_exact_unpacked_path': str(candidate.relative_to(ROOT)),
                          'source_sha256': BASE_SHA}
        recommendation_sha = None
        validation_plan = {'source_sha256': BASE_SHA, 'zip_sha256': ZIP_SHA, 'exact_path': str(candidate),
                           'protocol_plan_sha256': plan_sha,
                           'scope': 'Original fallback bytes fixed from the start. Validate during host-resource wait without opening selection or final seeds. Reuse only if the final recommendation has these identical bytes and this exact path.'}
        previous = RUN / 'fallback-validation-plan.json'
        if previous.exists():assert json.loads(previous.read_text()) == validation_plan
        else:train.atomic(previous, validation_plan)
    else:
        recommendation = json.loads(recommendation_path.read_text())
        recommendation_sha = sha(recommendation_path)
    candidate = ROOT / recommendation['final_exact_unpacked_path']
    expected = recommendation['source_sha256']
    records = []
    games = plan['luna'] + plan['client']
    assert len(games) == plan['planned_full_auxiliary_attempts'] == 8
    for game in games:
        assert sha(plan_path) == plan_sha
        if recommendation_sha is not None:assert sha(recommendation_path) == recommendation_sha
        else:assert sha(RUN / 'frozen/DARCL2.zip') == ZIP_SHA
        assert fingerprint(candidate) == expected
        key = recommendation['recommended'] + '-' + f"{game['mode']}-{game['seed']}-s{game['seat']}"
        print(json.dumps({'acceptance_game': key, 'candidate': recommendation['recommended']}), flush=True)
        command = [sys.executable, '-m', 'development.secret_hunter_astra_sprint.relay',
                   '--candidate', str(candidate), '--mode', game['mode'],
                   '--seed', str(game['seed']), '--seat', str(game['seat']),
                   '--key-prefix', recommendation['recommended']]
        # relay resumes completed records and refuses incomplete attempts.
        # Preserve every failure; this controller never retries a failed game.
        subprocess.run(command, cwd=ROOT, check=True)
        audit = json.loads((RUN / 'relay' / (key + '.audit.json')).read_text())
        result = audit['result']
        assert audit['source_sha256'] == expected
        assert result['seed'] == game['seed'] and audit['seat'] == game['seat']
        assert result['reason'] == 'hero_death' and result['winner'] in (1, 2)
        assert all(not count for field in ('illegal_counts', 'restarts', 'timeouts') for count in result[field].values())
        assert all(not audit[field] for field in ('command_returncode', 'envelope_mismatches', 'ordinary_fallbacks', 'worker_errors'))
        assert audit['wait_first'] and audit['game_over_published'] and audit['game_over_observed']
        assert audit['act_calls'] == audit['decisions'] > 0
        if game['mode'] == 'luna':
            assert audit['model_id'] == 'gpt-6-luna' and not audit['course_stop']
            assert audit['model_chain']['script_before_every_act']
            assert audit['model_chain']['actions_without_matching_script'] == 0
            assert audit['model_chain']['model_act_calls'] == audit['act_calls']
        records.append({'key': key, 'audit_sha256': sha(RUN / 'relay' / (key + '.audit.json')), **audit})
    assert fingerprint(candidate) == expected
    summary = {'passed': True, 'candidate': recommendation['recommended'], 'source_sha256': expected,
               'plan_sha256': plan_sha, 'recommendation_sha256': recommendation_sha,
               'validated_before_selection': args.fallback_first,
               'games': len(records), 'records': records,
               'scope': 'Protocol acceptance only; these outcomes never enter strategy selection or promotion.'}
    name = 'fallback-acceptance.json' if args.fallback_first else 'final-acceptance.json'
    train.atomic(RUN / name, summary)
    train.atomic(ROOT / 'docs/secret_hunter_astra_sprint' / name, summary)
    print(json.dumps({'acceptance_complete': True, 'games': len(records)}), flush=True)


if __name__ == '__main__':
    main()
