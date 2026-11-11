"""Check token identities themselves, not just aggregate chance probabilities."""
import sys,json
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_program.accounting import record_cases
from development.secret_hunter_program import checks as f
from tactical_model import TOKENS
from lethal_planner import probabilistic_lethal


def main():
    e,i=f.fixture(hand=['NEW1_031'],mana=3,enemy_hp=4);actual=[]
    for cid in ('NEW1_032','NEW1_033','NEW1_034'):
        c=e.player(i).card(cid);expected=(c.atk,c.health,bool(c.charge),bool(c.taunt));assert TOKENS[cid]==expected,(cid,TOKENS[cid],expected)
        actual.append({'id':cid,'name':str(c),'stats':expected})
    probability=probabilistic_lethal(e.view(i),budget_s=.3,max_nodes=5000)
    winning=[b['companion'] for b in probability['branches'] if b['lethal_found']]
    assert winning==['NEW1_034'] and abs(probability['probability']-1/3)<1e-9
    record_cases('companion-id-and-chance-regression',4);write(ROOT/'docs/secret_hunter_program/companion-id-checks.json',{'passed':4,'actual':actual,'winning_branch':winning,'probability':probability})
    print('Four Companion identity/probability checks passed')
if __name__=='__main__':main()
