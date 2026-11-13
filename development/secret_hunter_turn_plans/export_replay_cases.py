"""Export the recovered public Golem turn for new paired conditional samples."""
import json
from development.secret_hunter_astra_plans.probe import read_cases,CASES,seat_one_history
from development.secret_hunter_astra_plans.continue_turns import world_for
from development.secret_hunter_turn_plans.study import RUN,ROOT
from development.secret_hunter_turn_plans.routes import public_features
from state_features import with_public_history


def main():
    source=read_cases()[CASES['deathrattle']]
    template=json.loads((ROOT/'development/teacher_eval/decks/astra-sticky.json').read_text())['cards']
    world=world_for(source,template,51010)
    history=seat_one_history(source)
    state=with_public_history({**world.view(1),'player':1,'seq':1,'game_id':'translated-golem','events':[]},history)
    pool=json.loads((ROOT/'development/teacher_eval/core.json').read_text());specs={s['name']:s for s in pool}
    dest=RUN/'mined-replay';dest.mkdir(exist_ok=True)
    for i,name in enumerate(('astra-board-proxy','astra-tempo-proxy')):
        spec={**specs[name],'deck':'development/teacher_eval/decks/astra-sticky.json'}
        r={'case':'trap-replay-'+str(i),'kind':'trap','split':'train','source_seed':32000003,
           'source_game':source['source_game'],'seat':1,'source_outcome':0,'opponent_spec':spec,
           'state':state,'public_history':history,'public_features':public_features(state),
           'scope':'Previously known public C2 Golem case translated to the original deck. Both frozen proxy policies use a compatible existing sticky-deck hypothesis template. New conditional futures, not held-out source games.'}
        (dest/(r['case']+'.json')).write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
