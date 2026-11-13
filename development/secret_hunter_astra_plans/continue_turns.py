"""Measure the effect of one modified turn under paired hidden-card hypotheses."""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import random
import sys

from hs_arena.cards import load

from development.benchmarks.run import load_policy
from development.opponents.population import decide as population_decide
from development.secret_hunter_astra_plans.probe import CASES, read_cases, seat_one_history
from development.secret_hunter_mcgs.build import Y1
from development.secret_hunter_mcgs.replays import build, clone, translate
from development.secret_hunter_program.common import ROOT, write
from action_validator import expand
from state_features import with_public_history


def world_for(source, template, seed):
    state = with_public_history(source['state'], source['history'])
    enemy = state['opponent']
    observed = Counter(c['card_id'] for c in enemy['board'] + enemy['graveyard'] if c['card_id'] in load())
    template_counts = Counter(template)
    remaining = template_counts - observed
    hand_size = enemy['hand_size']
    deck_size = enemy['deck_remaining']
    if observed - template_counts or sum(remaining.values()) < hand_size + deck_size:
        raise ValueError('Proxy template cannot supply the visible and hidden cards')
    cards = list(remaining.elements())
    random.Random(seed).shuffle(cards)
    # Some replay cards have left hand/deck without a collectible graveyard
    # entry. Sample those unknown slots from the same remaining template.
    world = build(state, seed, opponent_hand=cards[:hand_size],
                  opponent_deck=cards[hand_size:hand_size + deck_size])
    translate(world)
    return world


def finish(world, source, baseline, config, opponent, prefix=()):
    from program_policy import decide

    start = world.turn
    history = seat_one_history(source)
    cursor = 0
    turn_line = []
    memory = {}
    for seq in range(450):
        if world.over:
            return {'win': int(world.winner == 1), 'steps': seq, 'turn_line': turn_line}
        seat, _ = world.pending()
        state = world.view(seat)
        if seat == 1:
            history.extend(view for event in world.events[cursor:] if (view := event.view(1)) is not None)
            cursor = len(world.events)
            state = with_public_history({**state, 'player': 1}, history)
            opening = world.turn == start
            if opening and len(turn_line) < len(prefix):
                action = prefix[len(turn_line)]
            else:
                action, info = decide(state, config if opening else baseline, memory=memory if opening else None)
                if info.get('error') or info.get('fallback'):
                    raise RuntimeError(info)
            if opening:
                turn_line.append(action)
        else:
            action = opponent(state)
        result = world.step(seat, action)
        if not result.accepted:
            raise ValueError(f'Engine rejected {action}: {result}')
    raise RuntimeError('Continuation did not reach a terminal state')


def simulate(task):
    case, proxy, seed, source, template, baseline, candidate, tail_ablation = task
    if proxy == 'tempo':
        def opponent(state):
            return population_decide(state, 'tempo', expand)
    else:
        folder = ROOT / 'development/candidates/v7-zoo-strength'
        policy, _ = load_policy(folder)
        settings = json.loads((folder / 'config.json').read_text())

        def opponent(state):
            return policy.decide(state, settings)

    world = world_for(source, template, seed)
    result = {
        'case': case, 'proxy': proxy, 'seed': seed,
        'baseline': finish(clone(world, seed), source, baseline, baseline, opponent),
        'candidate': finish(clone(world, seed), source, baseline, candidate, opponent),
    }
    if tail_ablation:
        # Add one action to the executed candidate line, then hold continuation fixed.
        line = result['candidate']['turn_line']
        if [a['type'] for a in line] != ['play_card', 'hero_power', 'end_turn']:
            raise ValueError('Tail ablation requires the three-action deathrattle line')
        keeper = next(c for c in source['state']['you']['hand'] if c['card_id'] == 'EX1_080')
        prefix = [*line[:-1], {'type': 'play_card', 'card': keeper['entity_id'], 'position': 0}, line[-1]]
        result['keeper'] = finish(clone(world, seed), source, baseline, candidate, opponent, prefix)
    return result


def use_candidate(candidate):
    # The replay tools may initialize modules with same-named Y1 helpers.
    # These five are the only end-turn policy modules needed by this ablation.
    sys.path.insert(0, str(candidate.resolve() / 'scripts'))
    for name in ('race_plan', 'program_policy', 'turn_search', 'chance_search', 'public_response'):
        sys.modules.pop(name, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--start', type=int, required=True)
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--deathrattle-tail', action='store_true',
                        help='Test the same deathrattle line with Secretkeeper played before ending')
    args = parser.parse_args()
    if args.samples < 1 or args.workers < 1:
        parser.error('samples and workers must be positive')
    # Modules have same-named imports. Only an ablation of Y1's end-turn
    # features can safely use its own code with feature flags switched off.
    baseline = json.loads((Y1 / 'config.json').read_text())
    candidate = json.loads((args.candidate / 'config.json').read_text())
    changed = {key for key in candidate if candidate[key] != baseline.get(key)}
    allowed = {'summon_pressure_weight', 'explosive_credit_weight'}
    if candidate.get('trap_turn_commit'):
        allowed.update(('trap_turn_commit', 'plan_cache'))
    if set(baseline) - set(candidate) or changed - allowed:
        parser.error('candidate must be a Y1 end-turn scoring ablation')
    template = json.loads((ROOT / 'development/teacher_eval/decks/astra-sticky.json').read_text())['cards']
    cases = read_cases()
    selected = ('deathrattle',) if args.deathrattle_tail else ('juggler', 'deathrattle')
    tasks = [
        (case, proxy, seed, cases[CASES[case]], template, baseline, candidate, args.deathrattle_tail)
        for case in selected
        for proxy in ('zoo', 'tempo')
        for seed in range(args.start, args.start + args.samples)
    ]
    with ProcessPoolExecutor(max_workers=args.workers, initializer=use_candidate, initargs=(args.candidate,)) as pool:
        rows = list(pool.map(simulate, tasks))
    groups = []
    for case in selected:
        for proxy in ('zoo', 'tempo'):
            pairs = [r for r in rows if (r['case'], r['proxy']) == (case, proxy)]
            scores = [(r['baseline']['win'], r['candidate']['win']) for r in pairs]
            groups.append({
                'case': case, 'proxy': proxy, 'pairs': len(scores),
                'y1_wins': sum(a for a, _ in scores), 'candidate_wins': sum(b for _, b in scores),
                'gained': sum(b > a for a, b in scores), 'lost': sum(a > b for a, b in scores),
                'changed_turns': sum(r['baseline']['turn_line'] != r['candidate']['turn_line'] for r in pairs),
            })
            if args.deathrattle_tail:
                scores = [(r['candidate']['win'], r['keeper']['win']) for r in pairs]
                groups[-1].update(keeper_wins=sum(b for _, b in scores),
                                  keeper_gained=sum(b > a for a, b in scores),
                                  keeper_lost=sum(a > b for a, b in scores))
    write(args.out, {
        'scope': 'Synthetic translated public C2 development states, with Y1 after the tested turn.',
        'groups': groups, 'rows': rows,
    })
    print(json.dumps(groups, indent=2))


if __name__ == '__main__':
    main()
