"""Three hypotheses motivated by pilot coverage and original-deck code audit."""
import json,shutil
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_dgm.deck_guard import check
W=ROOT/'development/secret_hunter_dgm/candidates';D=ROOT/'docs/secret_hunter_dgm'
def child(name,parent,hypothesis):
 dest=W/name;shutil.copytree(W/parent,dest,ignore=shutil.ignore_patterns('__pycache__','scratch','game'))
 archive=json.loads((D/'candidates.json').read_text());archive[name]={'parent_ids':[parent],'hypothesis':hypothesis,'status':'provisional','tool_version':'stratified-original-root-v1'};write(D/'candidates.json',archive)
 return dest

def main():
 b=child('B1','K1','Count affordable in-hand Krush charge in the next-turn clock only with board space and no visible Taunt; do not wait for an undrawn card.')
 p=b/'scripts/race_plan.py';s=p.read_text();start=s.index('@lru_cache');end=s.index('\ndef value',start)
 s=s[:start]+'''@lru_cache(maxsize=1024)
def hand_damage(cards,mana,beast,slots,charge_open=True,power_cost=2):
    # Track actual board slots and mana; Krush damage belongs to a new minion,
    # so a frozen friendly hero does not prevent its charge attack.
    states={(0,beast,0):0}
    for cid,cost,kind in cards:
        updated=dict(states)
        for (spent,active,used),damage in states.items():
            if spent+cost>mana:continue
            gain=0;next_active=active;next_used=used
            if cid=='EX1_539':gain=5 if active else 3
            elif cid=='DS1_185':gain=2
            elif kind and used<slots:
                next_active=True;next_used+=1
                if cid=='EX1_543' and charge_open:gain=8
            else:continue
            key=(spent+cost,next_active,next_used)
            updated[key]=max(updated.get(key,-1),damage+gain)
        states=updated
    return max(d+(2 if mana-spent>=power_cost else 0) for (spent,_,_),d in states.items())


def burst(state,assume_beast=False):
    y,o=state['you'],state['opponent']
    mana=max(0,min(10,y['max_mana']+1)-y.get('overload_next_turn',0))
    cards=tuple(sorted(((c['card_id'],c['cost'],bool(c.get('type')=='MINION' and is_beast(c))) for c in y['hand']),key=lambda c:not c[2]))
    charge_open=not any(m.get('taunt') and not m.get('stealth') for m in o['board'])
    return hand_damage(cards,mana,assume_beast,7-len(y['board']),charge_open,y['hero_power'].get('cost',2))

''' +s[end:]
 s=s.replace("attack_clock=(board_attack+weapon.get('attack',0)) if not enemy_taunts else 0","attack_clock=(board_attack+(weapon.get('attack',0) if not y['hero'].get('frozen') else 0)) if not enemy_taunts else 0")
 p.write_text(s)
 c=child('C1','C0','Enumerate standalone Animal Companion roots; inherited C2 only activates with Juggler despite implemented Companion transitions.')
 p=c/'scripts/chance_search.py';s=p.read_text().replace("    if not knives and not any(c['card_id']=='NEW1_019'", "    companion_ready=any(c['card_id']=='NEW1_031' for c in available) and len(y['board'])<7\n    if not companion_ready and not knives and not any(c['card_id']=='NEW1_019'");p.write_text(s)
 o=child('O1','K1','Against pressure classes on the play, return three-drops without a one-plus-two opening curve; keep supported Coin curves, avoid speculative combos.')
 p=o/'scripts/tactics_rank.py';s=p.read_text().replace("        if low and (c['card_id']!='EX1_538' or hounds_ok):", "        curve_ready=(bool(ones) and (coin or bool(two))) if pressure else low\n        if curve_ready and (c['card_id']!='EX1_538' or hounds_ok):");p.write_text(s)
 for name in ('B1','C1','O1'):check(W/name)
if __name__=='__main__':main()
