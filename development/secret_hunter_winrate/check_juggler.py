"""Validate newly admitted deterministic deployments against the course engine."""
import json
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT, write
from development.secret_hunter_response.accounting import reserve, finish
import tactical_model as model


def projection(s):
    return {k: {'hp': s[k]['hero']['health'], 'mana': s[k]['mana'],
                'board': [(x['card_id'], x['attack'], x['health'], x['max_health'],
                           bool(x.get('taunt')), bool(x.get('divine_shield')))
                          for x in s[k]['board']]}
            for k in ('you', 'opponent')}


def main():
    reserve('winrate-juggler-mechanisms', short=100, seconds=120)
    rows = []
    for own in ([], ['EX1_080'], ['EX1_531'], ['EX1_162'], ['EX1_029']):
        for mana in (2, 3, 4):
            engine, seat = c.fixture(own=own, enemy=['EX1_008', 'CS2_172'],
                                     hand=['NEW1_019', 'EX1_029'], mana=mana)
            s = engine.view(seat)
            action = {'type': 'play_card', 'card': s['you']['hand'][0]['entity_id'],
                      'position': len(own)}
            initial = model.prepare({**s, 'planning_mode': 'response'})
            assert action in list(model.options(initial))
            predicted = model.transition(initial, action)
            assert predicted is not None
            assert engine.step(seat, action).accepted
            actual = engine.view(seat)
            equal = projection(predicted) == projection(actual)
            assert equal
            if mana > 2:
                followup = {'type': 'play_card', 'card': actual['you']['hand'][0]['entity_id'],
                            'position': len(actual['you']['board'])}
                assert model.transition(predicted, followup) is None
            rows.append({'own': own, 'mana': mana, 'equal': equal,
                         'next_random_summon_rejected': mana > 2})
    engine, seat = c.fixture(own=['NEW1_019'], hand=['NEW1_019'], mana=2)
    s = engine.view(seat)
    action = {'type': 'play_card', 'card': s['you']['hand'][0]['entity_id'], 'position': 1}
    assert model.transition(model.prepare({**s, 'planning_mode': 'response'}), action) is None
    write(ROOT/c.ARGS.out, {'deterministic_cases': rows, 'second_juggler_rejected': True})
    finish('winrate-juggler-mechanisms', actual_short=26)
    print(json.dumps({'engine_matches': len(rows), 'random_branches_rejected': 11}))


if __name__ == '__main__':
    main()
