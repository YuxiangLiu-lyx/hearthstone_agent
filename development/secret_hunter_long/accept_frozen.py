"""Execute only the eight predeclared protocol games for the recommended ZIP."""
import json
import subprocess
import sys

from development.benchmarks.run import fingerprint
from development.secret_hunter_long.study import ROOT, RUN
from development.secret_hunter_mcgs import train
from development.secret_hunter_program.common import sha


def main():
    plan_path = RUN / 'final-acceptance-plan.json'
    plan = json.loads(plan_path.read_text())
    plan_sha = sha(plan_path)
    recommendation_path = ROOT / 'docs/secret_hunter_long/recommendation.json'
    recommendation = json.loads(recommendation_path.read_text())
    recommendation_sha = sha(recommendation_path)
    candidate = ROOT / recommendation['final_exact_unpacked_path']
    expected = recommendation['source_sha256']
    records = []
    games = plan['luna'] + plan['client']
    assert len(games) == plan['planned_full_auxiliary_attempts'] == 8
    for game in games:
        assert sha(plan_path) == plan_sha and sha(recommendation_path) == recommendation_sha
        assert fingerprint(candidate) == expected
        key = f"{game['mode']}-{game['seed']}-s{game['seat']}"
        print(json.dumps({'acceptance_game': key, 'candidate': recommendation['recommended']}), flush=True)
        command = [sys.executable, '-m', 'development.secret_hunter_long.relay',
                   '--candidate', str(candidate), '--mode', game['mode'],
                   '--seed', str(game['seed']), '--seat', str(game['seat'])]
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
               'games': len(records), 'records': records,
               'scope': 'Protocol acceptance only; these outcomes never enter strategy selection or promotion.'}
    train.atomic(RUN / 'final-acceptance.json', summary)
    train.atomic(ROOT / 'docs/secret_hunter_long/final-acceptance.json', summary)
    print(json.dumps({'acceptance_complete': True, 'games': len(records)}), flush=True)


if __name__ == '__main__':
    main()
