"""Known public Amani replay; post-freeze diagnostics, never policy selection."""
import json
from development.secret_hunter_astra_plans.probe import read_cases,CASES,seat_one_history
from development.secret_hunter_astra_plans.continue_turns import world_for
from development.secret_hunter_turn_plans.study import RUN,ROOT
from development.secret_hunter_turn_plans.routes import public_features
from state_features import with_public_history


def main():
    source=read_cases()[CASES['amani']]
    template=json.loads((ROOT/'development/teacher_eval/decks/astra-sticky.json').read_text())['cards']
    world=world_for(source,template,51022)
    history=seat_one_history(source)
    state=with_public_history({**world.view(1),'player':1,'seq':1,'game_id':'translated-amani','events':[]},history)
    specs={s['name']:s for s in json.loads((ROOT/'development/teacher_eval/core.json').read_text())}
    dest=RUN/'mined-amani-diagnostic';dest.mkdir(exist_ok=True)
    for i,name in enumerate(('astra-board-proxy','astra-tempo-proxy')):
        spec={**specs[name],'deck':'development/teacher_eval/decks/astra-sticky.json'}
        row={'case':'amani-replay-'+str(i),'kind':'amani','split':'diagnostic','source_seed':32000002,
             'source_game':source['source_game'],'seat':1,'source_outcome':0,'opponent_spec':spec,
             'state':state,'public_history':history,'public_features':public_features(state),
             'scope':'Known translated C2 public replay. Post-freeze diagnosis only. Companion may produce Taunt; its outcome is not forced. Two proxy policies share one source game.'}
        (dest/(row['case']+'.json')).write_text(json.dumps(row,indent=2)+'\n')


if __name__=='__main__':main()
