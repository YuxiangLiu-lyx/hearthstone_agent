"""Archive and replay complete recorded games, without inferring single-action causality."""
import argparse
import gzip
import json

from hs_arena.deck import load_deck
from hs_arena.engine import Engine
from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.counterfactual import public_key, projection
from development.teacher_eval.compare import index
from .accounting import reserve, finish, fail
from .analyze import D, folder

SELECTED = [('astra-tempo-proxy', 985010, 1), ('bot2-face-proxy', 985018, 1),
            ('bot2-face-proxy', 985013, 2)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--name', required=True)
    parser.add_argument('--out', default='docs/secret_hunter_face_validation/cases.json')
    args = parser.parse_args()
    archive_path = D / 'recorded-games.json.gz'
    if args.build:
        assert not archive_path.exists()
        differences = [json.loads(line) for line in gzip.open(D / 'first-differences.jsonl.gz', 'rt')]
        population = json.loads((ROOT / 'development/teacher_eval/core.json').read_text())
        jobs = []
        for opponent, seed, seat in SELECTED:
            difference = next(r for r in differences if (r['opponent'], r['seed'], r['seat']) == (opponent, seed, seat))
            spec = next(o for o in population if o['name'] == opponent)
            for arm in ('Y1', 'F2'):
                row = index(readlines(folder(arm, 'core') / 'results.jsonl'))[(opponent, seed, seat)]
                jobs.append({'arm': arm, 'opponent': opponent, 'seed': seed, 'seat': seat, 'spec': spec,
                             'row': row, 'difference': difference, 'actions': []})
    else:
        jobs = json.loads(gzip.open(archive_path, 'rt').read())
    reserve(args.name, full=len(jobs), final=True, seconds=120)
    try:
        reports = []
        for job in jobs:
            seat = job['seat']
            own = load_deck(ROOT / 'development/secret_hunter_response/candidates/Y1/deck.json')
            other = load_deck(ROOT / job['spec']['deck'])
            engine = Engine(own if seat == 1 else other, other if seat == 1 else own, job['seed'], max_turns=180)
            if args.build:
                observations = {who: readlines(folder(job['arm'], 'core') / 'games' / job['row']['game'] / f'p{who}/observations.jsonl')
                                for who in (1, 2)}
            cursors = {1: 0, 2: 0}
            steps, divergence_index, last_turn = 0, None, None
            trajectory = []
            while not engine.over:
                who, _ = engine.pending()
                if args.build:
                    record = observations[who][cursors[who]]
                    step = {'player': who, 'action': record['action'], 'public_sha256': public_key(record['state']),
                            'seq': record['state']['seq']}
                    job['actions'].append(step)
                else:
                    step = job['actions'][steps]
                state = engine.view(who)
                assert who == step['player'] and public_key(state) == step['public_sha256']
                if who == seat and step['seq'] == job['difference']['state']['seq']:
                    assert public_key(state) == job['difference']['public_state_sha256']
                    assert step['action'] == job['difference'][job['arm']]['action']
                    divergence_index = steps
                if who == seat and divergence_index is not None and state['turn'] != last_turn:
                    last_turn = state['turn']
                    trajectory.append({'turn': state['turn'], 'max_mana': state['you']['max_mana'],
                                       'at': 'before_first_remaining_own_action', **projection(state)})
                assert engine.step(who, step['action']).accepted
                if who == seat and divergence_index is not None and step['action']['type'] == 'end_turn':
                    trajectory.append({'turn': last_turn, 'at': 'after_own_end_turn', **projection(engine.view(seat))})
                cursors[who] += 1
                steps += 1
            assert steps == len(job['actions']) and divergence_index is not None
            assert engine.winner == job['row']['result']['winner']
            assert engine.turn == job['row']['result']['turns']
            reports.append({k: job[k] for k in ('arm', 'opponent', 'seed', 'seat')} |
                           {'steps': steps, 'divergence_action_index': divergence_index,
                            'first_action': job['difference'][job['arm']]['description'],
                            'winner': engine.winner, 'own_win': engine.winner == seat,
                            'terminal_turn': engine.turn, 'terminal': projection(engine.view(seat)),
                            'trajectory': trajectory})
        if args.build:
            with archive_path.open('wb') as output:
                with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as archive:
                    archive.write(json.dumps(jobs).encode())
        result = {'games': reports, 'reproduced_terminal_outcomes': len(reports),
                  'selection': 'Post-hoc examples: one trade-to-face win, one trade-to-face loss, one early development-to-Hero-Power loss.',
                  'scope': 'Replay of recorded full policies and realized random outcomes. These are not new independent wins or isolated first-action counterfactuals.'}
        write(ROOT / args.out, result)
        finish(args.name, completed=len(reports), reproduced=len(reports))
        print(json.dumps({'reproduced_terminal_outcomes': len(reports),
                          'games': [{k: r[k] for k in ('arm', 'opponent', 'seed', 'seat', 'own_win', 'steps')}
                                    for r in reports]}, indent=2))
    except BaseException as exc:
        fail(args.name, repr(exc))
        raise


if __name__ == '__main__':
    main()
