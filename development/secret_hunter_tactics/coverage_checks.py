"""Distinguish exact transition coverage from the release's two search entrypoints."""
import json,sys,time
from development.secret_hunter_tactics import checks as c
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_tactics.accounting import record_cases
from program_policy import decide
from lethal_planner import search
cfg=json.loads((c.CANDIDATE/'config.json').read_text());cases=[];count=0
for family,kwargs in [('keeper',dict(own=['EX1_080','EX1_080'],hand=['EX1_610'],mana=4,enemy_hp=6)),
 ('houndmaster',dict(own=['EX1_554t','EX1_543'],enemy=['CS2_179'],hand=['DS1_070'],mana=4,enemy_hp=8))]:
    e,i=c.fixture(**kwargs)
    if family=='houndmaster':e.player(3-i).field[0].damage=2
    s=e.view(i);base=search(s,budget_s=.4,max_nodes=8000);extended=search({**s,'planning_mode':'proof'},budget_s=.5,max_nodes=8000);count+=2
    assert not base['guaranteed'],base
    assert extended['guaranteed'],extended
    line=[];reasons=[]
    while not e.over and len(line)<10:
        s=e.view(i);a,info=decide(s,cfg);line.append(a);reasons.append(info['reason']);count+=1
        assert a['type']!='end_turn',(family,line,info)
        assert e.step(i,a).accepted
    assert e.over and e.winner==i,(family,line)
    cases.append({'family':family,'dedicated_base_search_lethal':False,'offline_extended_proof_lethal':True,
      'release_policy_engine_win':True,'actions':line,'reasons':reasons})
report={'cases':cases,'short_cases':count,
 'limitation':'The release dedicated lethal entrypoint still prepares base coverage. Houndmaster/Secretkeeper buff lines can be found by ordinary response-mode turn search with a terminal score, but are not part of the independent proof-first coverage. No post-holdout policy patch was made.'}
record_cases('search-entrypoint coverage boundary',count);write(ROOT/'docs/secret_hunter_tactics/coverage-boundary.json',report);print(json.dumps(report))
