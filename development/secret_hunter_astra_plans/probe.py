"""Run a complete public replay turn through the supervised skill CLI."""

import argparse
import io
import json
from pathlib import Path
from zipfile import ZipFile

from development.secret_hunter_mcgs.cli_match import CLIPlayer
from development.secret_hunter_mcgs.replays import build, translate
from development.secret_hunter_program.common import ROOT, write
from state_features import with_public_history


CASES = {
    'amani': ('02', 22),
    'deathrattle': ('03', 20),
    'juggler': ('04', 9),
}


def read_cases():
    with ZipFile(ROOT / 'docs/secret_hunter_mcgs/submission2-public.zip') as archive:
        with archive.open('decisions.jsonl') as source:
            return {
                (row['source_game'].rsplit('_', 1)[-1], row['state']['seq']): row
                for line in source
                if '_astra_' in (row := json.loads(line))['source_game']
            }


def action_cards(state, action):
    entities = {
        card['entity_id']: card['card_id']
        for side in ('you', 'opponent')
        for card in [state[side]['hero'], *state[side]['board'], *state[side].get('hand', ())]
    }
    return {key: entities[action[key]] for key in ('card', 'attacker', 'target') if key in action}


def seat_one_history(source):
    # Reconstruction places the observed seat in slot 1. Entity IDs stay the same.
    return [
        {**event, 'player': 3 - event['player']}
        if source['state']['player'] == 2 and event.get('player') in (1, 2) else event
        for event in source['history']
    ]


def run_turn(candidate, source, seed):
    initial = with_public_history(source['state'], source['history'])
    world = build(initial, seed)
    translate(world)
    player = CLIPlayer(candidate)
    player.history.extend(seat_one_history(source))
    player.log = io.StringIO()
    start_turn = world.turn
    cursor = 0
    actions = []
    try:
        while not world.over and world.turn == start_turn and world.pending()[0] == 1:
            state = {
                **world.view(1),
                'game_id': 'synthetic-replay',
                'seq': initial['seq'] + len(actions),
                'player': 1,
                'events': [view for event in world.events[cursor:] if (view := event.view(1)) is not None],
            }
            cursor = len(world.events)
            decision = player.decide(state)
            if decision.kind != 'action':
                raise RuntimeError(decision.message)
            result = world.step(1, decision.action)
            if not result.accepted:
                raise ValueError(f'Engine rejected {decision.action}: {result}')
            actions.append({
                'action': decision.action,
                'cards': action_cards(state, decision.action),
                'events': [view for event in world.events[cursor:] if (view := event.view(1)) is not None],
            })
            if len(actions) >= 32:
                raise RuntimeError('Synthetic replay turn did not finish')
        records = [json.loads(line) for line in player.log.getvalue().splitlines()]
    finally:
        player.stop()
    for action, record in zip(actions, records, strict=True):
        info = record['info']
        if info.get('error') or info.get('fallback'):
            raise RuntimeError(info)
        action.update(reason=info['reason'], elapsed_s=record['elapsed_s'],
                      error=info.get('error'), fallback=info.get('fallback', False),
                      burst_plan=info.get('burst_plan'))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--case', nargs='+', choices=CASES, default=list(CASES))
    parser.add_argument('--samples', type=int, default=1)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error('samples must be positive')
    cases = read_cases()
    results = []
    for name in args.case:
        for seed in range(500, 500 + args.samples):
            line = run_turn(args.candidate, cases[CASES[name]], seed)
            results.append({'case': name, 'seed': seed, 'actions': line})
            print(name, seed, [(a['action']['type'], a['cards'], a['reason']) for a in line], flush=True)
    write(args.out, {
        'candidate': str(args.candidate),
        'scope': 'Translated public C2 development turns. Hidden cards and RNG are synthetic.',
        'results': results,
    })


if __name__ == '__main__':
    main()
