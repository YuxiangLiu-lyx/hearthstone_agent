"""Replay actual allowed games to check public tactical proofs and same-family perturbations.

The replay harness knows the original seed/decks only to reconstruct the engine.
The decision function receives e.view plus public hero-attack history, never those
private reconstruction inputs. Continuations here are deterministic tactical lines,
not simulated full-game win-rate estimates.
"""
import copy
import json
from pathlib import Path
import sys

from development.secret_hunter.bootstrap import ROOT,write
from development.secret_hunter.audit import readlines
sys.path.insert(0,str(ROOT/'development/secret_hunter/frozen/secret-hunter-agent/scripts'))
from hs_arena.deck import load_deck
from hs_arena.engine import Engine
from lethal_planner import search


def main():
    folder=ROOT/'experiments/secret-c1-development'
    opponents={s['name']:s for s in json.loads((ROOT/'docs/secret_hunter/opponent_manifest.json').read_text())['opponents']}
    cases=[];used=0;replay_actions=0
    for row in readlines(folder/'results.jsonl'):
        game=folder/'games'/row['game'];seat=row['seat']
        observations={p:readlines(game/f'p{p}'/'observations.jsonl') for p in (1,2)}
        known=next((z for z in observations[seat] if z['info'].get('lethal',{}).get('guaranteed')),None)
        if not known:continue
        own=load_deck(ROOT/'secret-hunter-agent/deck.json');other=load_deck(ROOT/opponents[row['opponent']]['deck'])
        e=Engine(own if seat==1 else other,other if seat==1 else own,row['seed']);indices={1:0,2:0}
        while not e.over:
            who,_=e.pending();z=observations[who][indices[who]]
            if who==seat and z['state']['seq']==known['state']['seq']:break
            assert e.step(who,z['action']).accepted
            indices[who]+=1;replay_actions+=1
        for hp_delta,mana_delta in [(0,0),(-1,0),(-2,0),(1,0),(0,-1)]:
            branch=copy.deepcopy(e);me,enemy=branch.player(seat),branch.player(3-seat)
            enemy.hero.damage=enemy.hero.max_health-max(1,enemy.hero.health+hp_delta)
            if mana_delta:me.used_mana+=1
            steps=0;proof=None
            while not branch.over and steps<15:
                s=branch.view(seat)
                # Complete public turn history provided the original hero-attack availability.
                if steps==0:s['hero_attack_available']=known['state'].get('hero_attack_available',False)
                r=search(s,budget_s=.4,max_nodes=6000)
                if proof is None:proof=r
                if not r['guaranteed']:break
                accepted=branch.step(seat,r['first_action']).accepted
                assert accepted,'Projection returned an engine-illegal root action'
                steps+=1
            win=branch.over and branch.winner==seat
            # A truncated replan does not refute the first proof; retain the unresolved case.
            cases.append({'family':row['game'],'source_seq':known['state']['seq'],'enemy_hp_delta':hp_delta,
                          'mana_delta':mana_delta,'known_positive':hp_delta<=0 and mana_delta==0,
                          'proof_found':proof['guaranteed'],'engine_win':win,'steps':steps,
                          'unresolved':proof['guaranteed'] and not win,'status':proof})
        used+=1
        if used==10:break
    positive=[c for c in cases if c['known_positive']]
    report={'families':used,'short_branches':len(cases),'replay_actions':replay_actions,
            'known_positive_cases':len(positive),'known_positive_recall':sum(c['proof_found'] for c in positive)/len(positive),
            'proofs':sum(c['proof_found'] for c in cases),'engine_verified_wins':sum(c['engine_win'] for c in cases),
            'unresolved':sum(c['unresolved'] for c in cases),'cases':cases,
            'scope':'Development-only game families. No final holdout or hidden information used to choose actions.'}
    write(ROOT/'docs/secret_hunter/replay-tactics.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))


if __name__=='__main__':main()
