"""Nonterminal course-engine turn replays for the requested face-first preference."""
import copy
import json
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT, write
from development.secret_hunter_response.accounting import reserve, finish
from program_policy import decide
from action_validator import legal
from face_preference import pressure_window, ordinary_small_minion


def turn(engine, seat, cfg):
    trace = []
    for _ in range(15):
        s = engine.view(seat)
        s.update(player=seat, seq=len(trace), game_id='public-preference-fixture')
        action, info = decide(s, cfg)
        assert legal(s, action) and not info.get('error')
        assert engine.step(seat, action).accepted
        assert not engine.over, 'Only nonterminal branches are authorized in this follow-up.'
        trace.append({'action': action, 'reason': info['reason']})
        if action['type'] == 'end_turn':
            return {'trace': trace, 'own_hp': engine.view(seat)['you']['hero']['health'],
                    'enemy_hp': engine.view(seat)['opponent']['hero']['health']}
    raise AssertionError('Nonterminal fixture failed to end the turn')


def main():
    run_name = 'face-preference-fixtures-'+c.CANDIDATE.name+'-v3'
    reserve(run_name, short=400, seconds=180)
    cfg = json.loads((c.CANDIDATE/'config.json').read_text())
    base = {**cfg, 'face_preference': False}
    specs = [
        ('small_imp', dict(own=['EX1_531'], enemy=['EX1_598'], mana=0)),
        ('two_small_imps', dict(own=['EX1_531'], enemy=['EX1_598', 'EX1_598'], mana=0)),
        ('explosive_control', dict(own=['EX1_531'], enemy=['EX1_598', 'EX1_598'], hand=['EX1_610'], mana=2)),
        ('key_juggler', dict(own=['CS2_182'], enemy=['NEW1_019'], mana=0)),
        ('key_hyena', dict(own=['CS2_182'], enemy=['EX1_531', 'EX1_598'], mana=0)),
        ('bow_removal', dict(enemy=['NEW1_019'], hand=['EX1_536'], mana=3)),
        ('danger', dict(own=['CS2_182'], enemy=['CS2_182'], mana=0, hp=5)),
        ('danger_with_secret', dict(own=['CS2_182'], enemy=['CS2_182'], hand=['EX1_533'], mana=2, hp=5)),
        ('taunt', dict(own=['CS2_182'], enemy=['CS2_121'], mana=0)),
        ('hyena_sacrifice', dict(own=['EX1_531', 'EX1_538t', 'EX1_538t'], enemy=['CS2_182'], mana=0)),
        ('houndmaster_order', dict(own=['EX1_531'], enemy=['CS2_182'], hand=['DS1_070'], mana=4)),
        ('juggler_hounds', dict(enemy=['CS2_172', 'CS2_172', 'EX1_598'], hand=['NEW1_019', 'EX1_538'], mana=5)),
    ]
    rows = []
    for name, spec in specs:
        engine, seat = c.fixture(**spec)
        state = engine.view(seat)
        old = turn(copy.deepcopy(engine), seat, base)
        new = turn(copy.deepcopy(engine), seat, cfg)
        rows.append({'name': name, 'initial_state': state,
                     'pressure_window': pressure_window(state, cfg),
                     'ordinary_enemy': [m['card_id'] for m in state['opponent']['board'] if ordinary_small_minion(m)],
                     'Y1': old, 'candidate': new})
    by_name = {r['name']: r for r in rows}
    if c.CANDIDATE.name == 'F2':
        for protected in ('key_juggler', 'bow_removal', 'danger', 'danger_with_secret', 'taunt', 'hyena_sacrifice', 'houndmaster_order'):
            assert by_name[protected]['Y1']['trace'] == by_name[protected]['candidate']['trace'], protected
    # Lethal is checked without executing the terminal action or spending a full-game attempt.
    engine, seat = c.fixture(own=['EX1_543'], enemy_hp=8, mana=0)
    state = engine.view(seat)
    action, info = decide(state, cfg)
    assert legal(state, action) and info['lethal']['guaranteed']
    assert action['type'] == 'attack' and action['target'] == state['opponent']['hero']['entity_id']
    assert not engine.over
    report = {'nonterminal_cases': rows, 'guaranteed_lethal_preserved_without_execution': True,
              'candidate': c.CANDIDATE.name, 'full_games': 0, 'claim': 'Legal mechanism and preference checks only; no win-rate estimate.'}
    write(ROOT/c.ARGS.out, report)
    steps = sum(len(r[k]['trace']) for r in rows for k in ('Y1', 'candidate'))
    finish(run_name, actual_short=steps+1, full_games=0)
    for r in rows:
        print(json.dumps({'case': r['name'], 'pressure': r['pressure_window'],
                          'Y1': r['Y1'], c.CANDIDATE.name: r['candidate']}))


if __name__ == '__main__':
    main()
