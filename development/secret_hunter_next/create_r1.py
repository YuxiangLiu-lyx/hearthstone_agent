"""A public-information scenario candidate, kept separate from mechanism-only M1."""
import json,shutil
from pathlib import Path
base=Path('development/secret_hunter_next/candidates');dest=base/'R1';shutil.copytree(base/'M1',dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
p=dest/'scripts/state_features.py';s=p.read_text().replace("'shown_cards':list(dict.fromkeys(e['card_id'] for e in shown)),","'shown_cards':list(dict.fromkeys(e['card_id'] for e in shown)),\n           'shown_counts':{cid:len({e.get('entity_id',n) for n,e in enumerate(shown) if e.get('card_id')==cid}) for cid in {e['card_id'] for e in shown}},")
p.write_text(s)
p=dest/'scripts/tactical_model.py';s=p.read_text().replace('"planning_mode": state.get("planning_mode", "base")}', '"planning_mode": state.get("planning_mode", "base"), "public_opponent_evidence": copy.deepcopy(state.get("public_opponent_evidence", {}))}')
p.write_text(s)
p=dest/'scripts/public_response.py';s=p.read_text().replace("x['remaining_attacks']=0 if x.get('frozen') else", "x['remaining_attacks']=0 if x.get('frozen') or x.get('hypothetical_fresh') else")
s=s.replace('def worst_reply(state,cfg,deadline,max_nodes=64):','def visible_reply(state,cfg,deadline,max_nodes=64):')
s += '''\n\ndef worst_reply(state, cfg, deadline, max_nodes=64):
    base = visible_reply(state, cfg, deadline, max_nodes)
    if not base['supported'] or not cfg.get('hidden_scenarios'):
        return base
    o = state['opponent']
    if o['hero']['hero_class'] != 'WARLOCK' or o.get('hand_size', 0) == 0:
        return base
    mana = min(10, o.get('max_mana', o.get('mana', 0)) + 1)
    evidence = state.get('public_opponent_evidence', {})
    shown = evidence.get('shown_counts', {})
    hand = o.get('hand_size', 0) + 1
    deck = max(10, o.get('deck_size', 20) + hand)
    scenarios = []
    # Subjective class priors, explicitly bounded by the two-copy rule and public plays.
    for cid, cost, kind in [('EX1_308', 1, 'burn'), ('CS2_188', 1, 'buff'), ('EX1_093', 4, 'taunts')]:
        remaining = max(0, 2 - shown.get(cid, 0))
        if mana < cost or not remaining:
            continue
        weight = min(.18, remaining * hand / deck * (.7 if cid in shown else .35))
        s = copy.deepcopy(state)
        y, enemy = s['you'], s['opponent']
        if kind == 'burn':
            m.damage(y['hero'], 4)
        elif kind == 'buff':
            targets = [x for x in enemy['board'] if not x.get('frozen')]
            if not targets or len(enemy['board']) >= 7:
                continue
            target = max(targets, key=lambda x: x['attack'])
            target['base_attack'] += 2
            m.refresh(s)
        else:
            if not enemy['board'] or len(enemy['board']) >= 7:
                continue
            for target in sorted(enemy['board'], key=lambda x: x['health'], reverse=True)[:2]:
                target['base_attack'] += 1
                target['health'] += 1
                target['max_health'] += 1
                target['taunt'] = True
            m.summon(s, enemy, 'EX1_093')
            enemy['board'][-1]['hypothetical_fresh'] = True
            m.refresh(s)
        reply = visible_reply(s, cfg, deadline, max(12, max_nodes // 2))
        if not reply['supported'] or time.monotonic() >= deadline:
            continue
        # A hidden-card scenario can express risk, never a proven visible lethal.
        delta = max(-80., min(0., reply['value'] - base['value']))
        scenarios.append({'card': cid, 'weight': weight, 'value_delta': delta,
                          'lethal_under_hypothesis': reply['visible_lethal_found']})
        base['nodes'] += reply['nodes']
    base['value'] += sum(x['weight'] * x['value_delta'] for x in scenarios)
    base['scenarios'] = scenarios
    base['scope'] = 'Visible attacks plus finite subjective Warlock hand scenarios; no hidden card is asserted present.'
    return base
'''
p.write_text(s)
p=dest/'scripts/race_plan.py';s=p.read_text().replace('    return score\n',"    if cfg.get('generator_value'):\n        score -= cfg['generator_value'] * sum(min(3, x['health']) for x in o['board'] if x['card_id']=='EX1_597' and not x.get('silenced'))\n    return score\n")
p.write_text(s)
c=json.loads((dest/'config.json').read_text());c.update(version='next-R1',parent='M1',hidden_scenarios=True,generator_value=.8,reply_budget_s=.24);(dest/'config.json').write_text(json.dumps(c,indent=2)+'\n')
