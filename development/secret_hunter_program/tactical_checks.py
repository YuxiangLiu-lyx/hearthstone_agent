"""Regression cases for survival, trigger uncertainty and validated plan reuse."""
import json,sys,time
from development.secret_hunter_program import checks as f
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.accounting import record_cases
from program_policy import decide
from action_validator import legal
from tactical_model import prepare,transition
from plan_cache import save,take


def main():
    cfg=json.loads((ROOT/'development/secret_hunter_program/candidates/T1/config.json').read_text());evidence=[]
    # Spending two mana on the power loses the available removal-plus-trade defense.
    e,i=f.fixture(own=['EX1_534'],enemy=['CS2_200'],hand=['EX1_539'],mana=3,hp=6)
    p,o=e.player(i),e.player(3-i);steps=[]
    while not e.over and e.pending()[0]==i and len(steps)<12:
        s=e.view(i);s.update(player=i,game_id='survival-fixture');a,info=decide(s,cfg);assert legal(s,a);assert e.step(i,a).accepted;steps.append(a)
    assert not o.field,[(m.id,m.health) for m in o.field]
    assert p.hero.health==6
    evidence.append({'case':'known-board-lethal-defense','actions':steps,'enemy_board_empty':True,'own_hp':p.hero.health,'claim':'Current visible board threat removed; no hidden-hand survival guarantee.'})
    # Explosive Trap stays untriggered while the opponent exchanges first.
    e,i=f.fixture(own=['EX1_080'],enemy=['EX1_008'],hand=['EX1_610']);p,o=e.player(i),e.player(3-i)
    f.play(e,i,'EX1_610');e.step(i,{'type':'end_turn'});m=o.field[0]
    assert e.step(3-i,{'type':'attack','attacker':m.entity_id,'target':p.field[0].entity_id}).accepted
    assert len(p.secrets)==1
    evidence.append({'case':'explosive-can-be-avoided-by-trading','secret_still_active':True})
    # A divine shield absorbs the trap and the attacker remains alive.
    e,i=f.fixture(enemy=['EX1_008'],hand=['EX1_610']);p,o=e.player(i),e.player(3-i)
    f.play(e,i,'EX1_610');e.step(i,{'type':'end_turn'});m=o.field[0]
    assert e.step(3-i,{'type':'attack','attacker':m.entity_id,'target':p.hero.entity_id}).accepted
    assert m in o.field and m.health==1 and not m.divine_shield
    evidence.append({'case':'explosive-shield-survival','enemy_health':m.health,'own_hp':p.hero.health})
    # Public deterministic attack plan reused only after observing its exact result.
    e,i=f.fixture(own=['EX1_531','EX1_029'],mana=0);s=e.view(i);s.update(game_id='cache',player=i)
    ids=[m['entity_id'] for m in s['you']['board']];hero=s['opponent']['hero']['entity_id'];seq=[{'type':'attack','attacker':x,'target':hero} for x in ids]
    memory={};save(s,cfg,seq,memory,time.monotonic()+.1);assert e.step(i,seq[0]).accepted
    fresh=e.view(i);fresh.update(game_id='cache',player=i);assert take(fresh,cfg,memory)==seq[1]
    memory={};save(s,cfg,seq,memory,time.monotonic()+.1);fresh['you']['board'][0]['health']-=1;assert take(fresh,cfg,memory) is None
    evidence.append({'case':'cache-exact-result-and-invalidated-health','reused':True,'changed_state_rejected':True})
    # Several simultaneous random triggers are deliberately outside deterministic projection.
    e,i=f.fixture(own=['NEW1_019','NEW1_019','EX1_531'],enemy=['CS2_200']*4,hand=['EX1_538'])
    s=e.view(i);card=next(c for c in s['you']['hand'] if c['card_id']=='EX1_538');a={'type':'play_card','card':card['entity_id']}
    assert transition(prepare(s),a) is None
    assert e.step(i,a).accepted
    evidence.append({'case':'two-jugglers-hounds','projector_rejected_random_branch':True,'engine_action_accepted':True,'board_size':len(e.player(i).field)})
    shortcfg=cfg|{'search_soft_s':0};a,info=decide(s,shortcfg);assert legal(s,a)
    evidence.append({'case':'zero-search-budget','action':a,'elapsed_s':info['elapsed_s']})
    record_cases('additional-tactical-regressions',f.FIXTURES+1);write(ROOT/'docs/secret_hunter_program/tactical-checks.json',{'passed':len(evidence),'fixtures':f.FIXTURES,'evidence':evidence});print(json.dumps({'passed':len(evidence),'fixtures':f.FIXTURES}))
if __name__=='__main__':main()
