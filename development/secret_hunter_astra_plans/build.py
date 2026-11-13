"""Create isolated, reproducible Y1 ablations for the Astra replay study."""
import argparse
import json
from pathlib import Path
import shutil

from development.benchmarks.run import fingerprint
from development.secret_hunter_dgm.deck_guard import check
from development.secret_hunter_mcgs.build import Y1


HERE = Path(__file__).resolve().parent
FEATURES = {
    'engine': {'summon_pressure_weight': 1.65},
    'trap': {'explosive_credit_weight': .90},
    'trap-commit': {'trap_turn_commit': True, 'plan_cache': True},
    'burst': {'enrage_risk_cost': 9.0},
}


def replace_once(path, old, new):
    source = path.read_text()
    if source.count(old) != 1:
        raise ValueError(f'Unexpected source for {path}')
    path.write_text(source.replace(old, new))


def build(target, features):
    if 'trap-commit' in features and 'trap' not in features:
        raise ValueError('trap-commit requires trap')
    shutil.copytree(Y1, target, ignore=shutil.ignore_patterns('__pycache__', 'scratch', 'game'))
    scripts = target / 'scripts'
    shutil.copyfile(HERE / 'reply_features.py', scripts / 'reply_features.py')
    replace_once(scripts / 'race_plan.py', '    return score\n',
                 '    from reply_features import value_adjustment\n'
                 '    return score + value_adjustment(s, cfg, after_response)\n')
    if 'burst' in features:
        shutil.copyfile(HERE / 'burst_plan.py', scripts / 'burst_plan.py')
        # Preserve the pre-attack scenario risk in the post-response term without
        # charging each partial attack as if it began a new opposing turn.
        replace_once(scripts / 'public_response.py', '    return {\'supported\':True,\'nodes\':nodes,\'value\':best_v,',
                     '    from reply_features import enrage_exposure\n'
                     '    if enrage_exposure(state):\n'
                     "        best_v -= cfg.get('enrage_risk_cost', 0)\n"
                     "    return {'supported':True,'nodes':nodes,'value':best_v,")
        replace_once(scripts / 'program_policy.py', '    except Exception as exc:\n',
                     "                if time.monotonic() < deadline:\n"
                     "                    from burst_plan import plan as defend\n"
                     "                    defense = defend(state, best, info.get('turn_search', {}).get('sequence'), config, deadline)\n"
                     "                    if defense:\n"
                     "                        info['burst_plan'] = defense\n"
                     "                        info['nodes'] += defense['nodes']\n"
                     "                        save(defense['action'], 'conditional_burst_plan')\n"
                     "    except Exception as exc:\n")
    if 'trap-commit' in features:
        shutil.copyfile(HERE / 'turn_commit.py', scripts / 'turn_commit.py')
        # ScriptPlayer uses plan_cache to pass persistent memory. Only the
        # restricted trap continuation should use it inside this candidate.
        replace_once(scripts / 'program_policy.py', '    start=time.monotonic()\n',
                     "    start=time.monotonic()\n"
                     "    if config.get('trap_turn_commit'):\n"
                     "        config = {**config, 'plan_cache': False}\n")
        replace_once(scripts / 'program_policy.py', "            else:\n                if config.get('scoring')",
                     "            else:\n"
                     "                if config.get('trap_turn_commit') and memory is not None:\n"
                     "                    from turn_commit import take\n"
                     "                    pending = take(state, memory)\n"
                     "                    if pending is not None:\n"
                     "                        save(pending, 'verified_trap_plan')\n"
                     "                        info['elapsed_s'] = time.monotonic() - start\n"
                     "                        return best, info\n"
                     "                if config.get('scoring')")
        replace_once(scripts / 'program_policy.py', '    except Exception as exc:\n',
                     "                if config.get('trap_turn_commit') and memory is not None:\n"
                     "                    from turn_commit import remember\n"
                     "                    remember(state, best, info.get('turn_search', {}).get('sequence'),\n"
                     "                             memory, deadline)\n"
                     "    except Exception as exc:\n")
    config_path = target / 'config.json'
    cfg = json.loads(config_path.read_text())
    for feature in features:
        cfg.update(FEATURES[feature])
    config_path.write_text(json.dumps(cfg, indent=2) + '\n')
    deck = check(target)
    return {'candidate': target.name, 'features': list(features), 'fingerprint': fingerprint(target), **deck}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('features', nargs='+', choices=FEATURES)
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.features), indent=2))


if __name__ == '__main__':
    main()
