"""Create the mechanism candidate without modifying either frozen baseline."""
import json
from pathlib import Path
P=Path('development/secret_hunter_next/candidates/M1')
p=P/'scripts/tactical_model.py';s=p.read_text()
s=s.replace('"EX1_554t": (1, 1, False, False),','"EX1_598": (1, 1, False, False), "EX1_554t": (1, 1, False, False),')
s=s.replace('SAFE |= {"EX1_080"','SAFE |= {"EX1_393", "EX1_597", "CS2_203", "EX1_080"')
s=s.replace('def refresh(state):','def enrage(m):\n    return 3 if m["card_id"] == "EX1_393" and not m.get("silenced") and m["health"] < m.get("max_health", m["health"]) else 0\n\n\ndef refresh(state):')
s=s.replace('m["base_attack"] + aura(side["board"], i)','m["base_attack"] + aura(side["board"], i) + enrage(m)')
s=s.replace('m["attack"] - aura(result[key]["board"], i)','m["attack"] - aura(result[key]["board"], i) - enrage(m)')
s += '''\n\ndef end_effects(state, side_key):
    """Project Imp Master end triggers, rejecting random summon interactions."""
    s = copy.deepcopy(state)
    side = s[side_key]
    masters = [m for m in side['board'] if m['card_id'] == 'EX1_597' and not m.get('silenced')]
    if masters and any(m['card_id'] == 'NEW1_019' and not m.get('silenced') for m in side['board']):
        return None
    for master in masters:
        if master not in side['board']:
            continue
        damage(master, 1)
        # Engine resolves the Hit death sweep before Summon, freeing a slot.
        if not cleanup(s):
            return None
        summon(s, side, 'EX1_598')
    refresh(s)
    return s
'''
p.write_text(s)
p=P/'scripts/public_response.py';s=p.read_text().replace("s=copy.deepcopy(state);y,o=s['you'],s['opponent']","s=m.end_effects(state, 'you')\n    if s is None:return None\n    y,o=s['you'],s['opponent']",1);p.write_text(s)
p=P/'scripts/program_policy.py';s=p.read_text().replace("deadline=start+min(1.5,config.get('search_soft_s',1.5))","deadline=min(start+min(1.5,config.get('search_soft_s',1.5)),config.get('_deadline',float('inf')))")
s=s.replace("lethal=search(state,", "lethal=search({**state,'planning_mode':'proof'},")
p.write_text(s)
p=P/'scripts/turn_search.py';s=p.read_text().replace("'depth':0}","'depth':0,'excluded':0,'deduplicated':0,'beam_pruned':0,'stop_reason':None}")
s=s.replace("report['bounded_out']=True;break","report['bounded_out']=True;report['stop_reason']='time' if time.monotonic()>=deadline else 'nodes';break")
s=s.replace('if successor is None:continue',"if successor is None:report['excluded']+=1;continue")
s=s.replace('if key in seen:continue',"if key in seen:report['deduplicated']+=1;continue")
s=s.replace("frontier=[(s,line) for _,s,line in following[:width]]","report['beam_pruned']+=max(0,len(following)-width)\n        frontier=[(s,line) for _,s,line in following[:width]]")
p.write_text(s)
c=json.loads((P/'config.json').read_text());c.update(version='next-M1',parent='D1');(P/'config.json').write_text(json.dumps(c,indent=2)+'\n')
