"""Engine-verified lethal lines crossing armor, taunt, shield and weapon setup."""
from development.secret_hunter_program import checks as f
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.accounting import record_cases
from lethal_planner import search


def main():
    cases=[]
    specs=[dict(own=['EX1_534','EX1_531'],enemy=['EX1_032'],hand=['EX1_539'],mana=5,enemy_hp=5),
           dict(own=['EX1_029'],hand=['EX1_536'],mana=5,enemy_hp=4)]
    for n,spec in enumerate(specs):
        e,i=f.fixture(**spec);e.player(3-i).hero.armor=2;actions=[];hero_available=True
        while not e.over and len(actions)<12:
            s=e.view(i);s['hero_attack_available']=hero_available;r=search(s,budget_s=.5,max_nodes=7000)
            assert r['guaranteed'],(n,r)
            a=r['first_action'];assert e.step(i,a).accepted;actions.append(a)
            if a.get('attacker')==s['you']['hero']['entity_id']:hero_available=False
        assert e.winner==i
        cases.append({'case':'taunt-shield-armor' if n==0 else 'equip-bow-armor','actions':actions,'winner':i})
    record_cases('armor-taunt-shield-weapon-lethal-regressions',2);write(ROOT/'docs/secret_hunter_program/defence-checks.json',{'passed':2,'cases':cases});print('Two compound lethal checks passed')
if __name__=='__main__':main()
