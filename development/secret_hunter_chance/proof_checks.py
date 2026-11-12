"""Probability mass, proof separation, public determinism and deadline regressions."""
import copy,time,json
from pathlib import Path
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_chance.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
import tactical_model as m
from chance_model import outcomes
from lethal_planner import search
from program_policy import decide
from action_validator import legal


def main():
    reserve(Path(c.ARGS.out).stem,short=80)
    rows=[]
    e,i=c.fixture(own=['NEW1_019','NEW1_019'],enemy=['EX1_029'],hand=['EX1_080'],enemy_hp=10,mana=1)
    s=m.prepare(e.view(i));a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'position':2}
    d=outcomes(s,a,time.monotonic()+1,cap=12)
    assert d['exact'] and len(d['outcomes'])==3
    killed=sum(p for p,x in d['outcomes'] if not x['opponent']['board'])
    assert abs(killed-.75)<1e-9
    rows.append({'case':'two knives exclude mortally wounded target','probability_minion_killed':killed,'exact_paths':3})
    e,i=c.fixture(own=['NEW1_019'],enemy=['CS2_172'],hand=['EX1_080'],enemy_hp=1,mana=1)
    e.player(i).field[0].turns_in_play=0
    s=e.view(i);initial=m.prepare(s);a={'type':'play_card','card':s['you']['hand'][0]['entity_id'],'position':1}
    d=outcomes(initial,a,time.monotonic()+1)
    lethal_mass=sum(p for p,x in d['outcomes'] if x['opponent']['hero']['health']<=0)
    assert lethal_mass==.5 and not search({**s,'planning_mode':'proof'},budget_s=.1)['guaranteed']
    rows.append({'case':'chance lethal is not proof','chance':lethal_mass,'guaranteed':False})
    # Input is unchanged; metadata cannot seed private lookahead or cross-game memory.
    before=copy.deepcopy(initial);again=outcomes(initial|{'game_id':'different','seq':999},a,time.monotonic()+1)
    assert initial==before and [(p,m.signature(x)) for p,x in d['outcomes']]==[(p,m.signature(x)) for p,x in again['outcomes']]
    assert not outcomes(initial,a,time.monotonic()-1)['supported']
    cfg=json.loads((c.CANDIDATE/'config.json').read_text())
    action,info=decide(s,cfg|{'_deadline':time.monotonic()-1})
    assert legal(s,action) and not info.get('error')
    rows.extend([{'case':'public metadata invariance and immutable input','pass':True},
                 {'case':'expired deadline retains legal fallback','pass':True}])
    write(ROOT/c.ARGS.out,{'cases':rows,'n':len(rows),'pass':len(rows)})
    finish(Path(c.ARGS.out).stem,actual_short=8)
    print(json.dumps(rows))
if __name__=='__main__':main()
