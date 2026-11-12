"""Fresh paired futures for the fixed Bow plan; never used to select W3."""
from development.secret_hunter_program.common import ROOT, readlines, write
from development.secret_hunter_response.accounting import reserve, finish
from development.secret_hunter_response.counterfactual import worker
import json


def main():
    row = next(x for x in readlines(ROOT/'docs/secret_hunter_response/counterfactual-balanced.jsonl')
               if x['case_id'] == 33)
    case = row['case']
    case['_frozen_plans'] = [p for p in row['plans'] if p['id'] in ('Y1', 'plan-1')]
    case['_validation_offset'] = 983000 - (964000 + 33*100)
    write(ROOT/'docs/secret_hunter_winrate/continuation-plan.json', {
        'case': 33, 'plans': ['Y1', 'plan-1'], 'fresh_future_seeds': [983000, 12],
        'purpose': 'Post-freeze conditional diagnostic only; no candidate reselection or tuning.'})
    reserve('winrate-conditional-bow', full=24, short=200, seconds=300)
    result = worker((case, 33, 0, 12))
    result['selected_on_selection_only'] = None
    result['selection_note'] = 'No selection samples: both plans were fixed before the new futures.'
    write(ROOT/'docs/secret_hunter_winrate/continuation-bow.json', result)
    errors = [x['error'] for p in result['plans'] for x in p['outcomes'] if x['error']]
    assert not errors
    wins = {p['id']: sum(x['win'] for x in p['outcomes']) for p in result['plans']}
    finish('winrate-conditional-bow', actual_full=24, actual_short=result['generation_nodes']+result['prefix_actions'], wins=wins)
    print(json.dumps(wins))


if __name__ == '__main__':
    main()
