"""Differential tests: every proposed action executes in the unchanged engine."""
import json
import sys
from development.secret_hunter_final.study import HERE,ROOT
sys.path.insert(0,str(HERE/'candidates/L2/scripts'))
from development.secret_hunter_mcgs.mcgs_init import initialize
initialize()
from development.secret_hunter_mcgs.cases import fixture
from hearthstone.enums import Zone
from face_lethal import prove
from action_validator import legal

def finish(e):
    sequence=[]
    for _ in range(5):
        if e.over:break
        s=e.view(1);proof=prove(s)
        assert proof is not None, s
        a=proof['first_action'];assert legal(s,a)
        assert e.step(1,a).accepted;sequence.append(a)
    assert e.over and e.winner==1
    return sequence

def main():
    rows=[]
    e=fixture(hand=['EX1_539','EX1_539'],own=['DS1_070','EX1_080'],mana=8,enemy_hp=7,opponent_class='HUNTER')
    e.player(2).card('EX1_610',zone=Zone.SECRET)
    rows.append({'name':'historical_houndmaster_coverage','sequence':finish(e)})
    for secret in [None,'EX1_610','EX1_611','EX1_533','EX1_554','EX1_609']:
        for frozen in [False,True]:
            e=fixture(hand=['EX1_539','EX1_539'],enemy=['CS2_179'],mana=8,enemy_hp=7,hp=2,opponent_class='HUNTER')
            p,q=e.player(1),e.player(2);p.hero.frozen=frozen
            if secret:q.card(secret,zone=Zone.SECRET)
            rows.append({'name':'burn_taunt_secret','secret':secret,'frozen':frozen,'sequence':finish(e)})
    for attacked in [False,True]:
        e=fixture(mana=2,hp=2,enemy_hp=2,opponent_class='HUNTER')
        p,q=e.player(1),e.player(2);p.card('EX1_536',zone=Zone.PLAY);p.hero.num_attacks=int(attacked)
        q.card('EX1_610',zone=Zone.SECRET)
        seq=finish(e);assert seq==[{'type':'hero_power'}]
        rows.append({'name':'avoid_bow_trap','already_attacked':attacked,'sequence':seq})
    for secret in ['EX1_287','EX1_289','EX1_295']:
        e=fixture(hand=['EX1_539','EX1_539'],mana=8,enemy_hp=7,opponent_class='MAGE')
        e.player(2).card(secret,zone=Zone.SECRET)
        assert prove(e.view(1)) is None
        rows.append({'name':'unknown_mage_secret_abstain','secret':secret})
    for mana,hp,armor,beast,expected in [(5,7,0,False,False),(5,7,0,True,True),(8,7,2,False,False),(8,7,1,False,True)]:
        e=fixture(hand=['EX1_539','EX1_539'],own=['EX1_531'] if beast else [],mana=mana,enemy_hp=hp)
        e.player(2).hero.armor=armor
        assert bool(prove(e.view(1)))==expected
        rows.append({'name':'mana_armor_beast','mana':mana,'hp':hp,'armor':armor,'beast':beast,
                     'expected':expected,'sequence':finish(e) if expected else []})
    e=fixture(mana=2,enemy_hp=2);e.player(1).hero.power.activations_this_turn=1
    assert prove(e.view(1)) is None;rows.append({'name':'power_used_abstain'})
    e=fixture(mana=2,enemy_hp=2);e.player(2).hero.buff(e.player(2).hero,'EX1_295o')
    assert prove(e.view(1)) is None;rows.append({'name':'immune_abstain'})
    path=ROOT/'docs/secret_hunter_final/face-lethal-checks.json'
    path.write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'checks':len(rows),'passed':True}))

if __name__=='__main__':main()
