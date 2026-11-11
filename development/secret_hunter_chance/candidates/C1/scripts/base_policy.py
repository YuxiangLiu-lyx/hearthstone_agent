from state_features import is_beast
"""Observation-only tempo policy. Every returned action comes from a legal template."""
import time
from itertools import combinations
from hs_arena.agents.greedy_bot import GreedyBot
from actions import expand
from evaluator import (CATALOG, BURN, BATTLE_DAMAGE, BUFFS, AOE, REMOVAL,
                       hand_body, minion_value, damage_value, threat)

def mulligan(state):
    hand=state["you"]["hand"]
    low=[c for c in hand if c["type"]=="MINION" and c["cost"]<=2]
    kept_costs={}; keep=[]
    for c in sorted(hand,key=lambda c:(c["cost"],-c.get("attack",0))):
        cost=c["cost"]
        good=c["type"]=="MINION" and cost<=2 and kept_costs.get(cost,0)<2
        good |= c["type"]=="MINION" and cost==3 and bool(low) and kept_costs.get(3,0)<1
        good |= c["card_id"] in ("CS2_024","CS1_130","DS1_185") and bool(low) and kept_costs.get(-1,0)<1
        if good:
            keep.append(c["entity_id"])
            key=cost if c["type"]=="MINION" else -1
            kept_costs[key]=kept_costs.get(key,0)+1
    t=next(t for t in state["legal_actions"] if t["type"]=="mulligan")
    return {"type":"mulligan","replace":[x for x in t["options"] if x not in keep]}

def choose(state):
    t=next(t for t in state["legal_actions"] if t["type"]=="choose")
    def v(c): return hand_body(c) if c.get("type")=="MINION" else BURN.get(c.get("card_id"),2)
    ids=[x["entity_id"] for x in sorted(t["options"],key=v,reverse=True)]
    return {"type":"choose","options":ids[:max(1,t.get("min",1))]}

def rank_actions(state, config=None, deadline=None):
    cfg=config or {}; you,opp=state["you"],state["opponent"]
    own={m["entity_id"]:m for m in you["board"]}; enemy={m["entity_id"]:m for m in opp["board"]}
    hand={m["entity_id"]:m for m in you["hand"]}
    oh,eh=you["hero"]["entity_id"],opp["hero"]["entity_id"]
    ehp=opp["hero"]["health"]+opp["hero"].get("armor",0)
    hp=you["hero"]["health"]+you["hero"].get("armor",0)
    danger=threat(opp)+3>=hp
    sd=sum(m.get("spell_damage",0) for m in own.values())
    face=cfg.get("face_weight",.6)+.45*(ehp<=15)+.65*(ehp<=8)
    if danger: face *= .55
    greedy=GreedyBot("fallback",None); ctx=greedy._ctx(state); generic={}
    for t in state["legal_actions"]:
        if deadline is not None and time.monotonic()>=deadline:break
        generator = greedy._play_candidates(state,t,ctx) if t["type"]=="play_card" else []
        for score,a in generator: generic[(a.get("card"),a.get("target"),a.get("choose"))]=score
    bodies=[c for c in hand.values() if c["type"]=="MINION" and c.get("playable")]
    packing={}
    for c in bodies:
        if deadline is not None and time.monotonic()>=deadline:break
        best=0; others=[d for d in bodies if d is not c]
        for n in range(min(2,max(0,6-len(own)))+1):
            for group in combinations(others,n):
                if deadline is not None and time.monotonic()>=deadline:break
                if c["cost"]+sum(d["cost"] for d in group)<=you["mana"]:
                    best=max(best,sum(hand_body(d) for d in group))
        packing[c["entity_id"]]=best*.55
    scored=[]
    for a in expand(state):
        if deadline is not None and time.monotonic()>=deadline:break
        kind=a["type"]; target=a.get("target"); s=-100.
        if kind=="end_turn": s=0
        elif kind=="attack":
            at=own.get(a["attacker"],you["hero"])
            if target==eh:
                s=face*at["attack"]
                if at["attack"]>=ehp and not opp["hero"].get("immune"): s=100000
            elif target in enemy:
                m=enemy[target]
                kills=(at["attack"]>=m["health"] or at.get("poisonous")) and not m.get("divine_shield")
                taken=0 if at.get("divine_shield") or at.get("immune") else m["attack"]
                dies=taken>0 and (taken>=at["health"] or m.get("poisonous") and a["attacker"]!=oh)
                gain=damage_value(m,at["attack"])
                if kills: gain=max(gain,minion_value(m)-2*bool(m.get("deathrattle")))
                loss=minion_value(at) if dies else .4*min(taken,at["health"])
                if a["attacker"]==oh:
                    loss=taken*(1.5 if danger else .35)
                    if taken>=hp: loss=100000
                s=gain-loss+(1.3 if kills and not dies else 0)
                if danger and kills: s+=m["attack"]*.8
                if at.get("divine_shield") and m["attack"]: s-=1.2
        elif kind=="play_card":
            c=hand[a["card"]]; cid=c["card_id"]; cost=c["cost"]
            s=generic.get((a["card"],target,a.get("choose")),-5)
            if c["type"]=="MINION":
                s=hand_body(c)+.15*cost+packing.get(a["card"],0)
                if cid=="EX1_608": s+=.7*sum(d["type"]=="SPELL" and d["cost"]>0 for d in hand.values())
                if cid=="EX1_319": s-=4 if hp<12 else .5
                if cid=="EX1_306": s-=2.5*(len(hand)>1)
                if cid=="CS2_151": s+=4.1 if len(own)<6 else 0
                if cid=="CS2_196": s+=1.9 if len(own)<6 else 0
                if cid in ("EX1_015","CS2_147"): s+=2.3*(len(hand)<8)
                if cid in ("CS2_088","EX1_583"): s+=min(30-hp,6 if cid=="CS2_088" else 4)*(.9 if danger else .3)
                if target is not None:
                    if cid in BUFFS:
                        da,dh=BUFFS[cid]; m=own.get(target)
                        s+=(da*(1.3 if m and m.get("can_attack") else .8)+.6*dh) if m else -30
                    elif cid in BATTLE_DAMAGE:
                        d=BATTLE_DAMAGE[cid]
                        s+=damage_value(enemy[target],d) if target in enemy else (face*d if target==eh else -30)
                        if target==eh and d>=ehp: s=100000
                    elif cid=="EX1_362": s+=3 if target in own and not own[target].get("divine_shield") else -15
                    elif cid=="EX1_382": s+=max(0,enemy.get(target,{}).get("attack",1)-1)*1.4 if target in enemy else -30
                    elif "Restore" in c.get("text",""):
                        m=own.get(target,you["hero"] if target==oh else {})
                        s+=min(3,m.get("max_health",0)-m.get("health",0)) if m else -30
                    elif target in enemy and not any(x in c.get("text","").lower() for x in ("damage","destroy","silence","take control","change an enemy")): s-=30
                pos=a.get("position",0); adjacent=you["board"][max(0,pos-1):pos+1]
                if cid in ("EX1_093","EX1_058","EX1_162","EX1_565"):
                    s+=sum((2.5 if cid=="EX1_093" else 1.1)+1.2*m.get("can_attack",False) for m in adjacent)
                else: s+=sum(.6 for m in adjacent if m["card_id"] in ("EX1_162","EX1_565"))
            elif c["type"]=="WEAPON":
                old=you.get("weapon") or {}
                s=1.8*c.get("attack",0)+.7*c.get("durability",0)-old.get("attack",0)*old.get("durability",0)
            elif cid in BURN:
                d=BURN[cid]+sd
                if cid=="EX1_539" and any(is_beast(m) for m in own.values()): d+=2
                if target==eh:
                    s=d*face-3.2 if ehp<=12 else -2
                    if d>=ehp and not opp["hero"].get("immune"): s=100000
                elif target in enemy:
                    m=enemy[target]; s=damage_value(m,d)-.45*cost-1.1
                    if danger and (d>=m["health"] or cid=="CS2_024"): s+=m["attack"]*.8
                    if cid=="EX1_302" and d>=m["health"] and not m.get("divine_shield"): s+=2.5
                else: s=-30
            elif cid in REMOVAL:
                m=enemy.get(target); s=minion_value(m)-.6*cost-2 if m else -30
                if cid=="CS1_113" and m: s+=minion_value(m)
                if danger and m: s+=m["attack"]*.8
            elif cid in AOE:
                d,hits_own=AOE[cid]; d+=sd
                s=sum(damage_value(m,d) for m in enemy.values())-1.5-.35*cost
                if hits_own: s-=sum(damage_value(m,d) for m in own.values())
                if danger: s+=sum(m["attack"]*.7 for m in enemy.values() if d>=m["health"] and not m.get("divine_shield"))
            elif cid in BUFFS:
                da,dh=BUFFS[cid]; m=own.get(target)
                s=(da*(1.6 if m and m.get("can_attack") else .8)+.7*dh-.4*cost-1) if m else -30
            elif cid=="EX1_277":
                s=sum(min(1.2,m["health"])*.8 for m in enemy.values())+1.2*sum(m["health"]==1 for m in enemy.values())-1.5
                if not enemy and ehp<=3+sd: s=100000
            elif cid=="GAME_005":
                s=1 if any(d["type"]=="MINION" and d["cost"]==you["mana"]+1 for d in hand.values()) and len(own)<7 else -1
            elif cid=="CS2_023": s=(3.4 if len(hand)<=4 else 1.)-(.8*len(enemy) if danger else 0)
            elif cid=="NEW1_031": s=8.5
            elif cid=="EX1_538": s=min(len(enemy),7-len(own))*3-1
            elif cid=="CS2_046": s=sum(3*(1.5 if m.get("can_attack") else .1) for m in own.values())-2
            elif cid=="EX1_248": s=9 if len(own)<6 else 3
            elif cid=="CS2_026": s=sum(m["attack"] for m in enemy.values())*(.7 if danger else .12)-2
        elif kind=="hero_power":
            hc=you["hero"]["hero_class"]; s=.25
            if hc=="MAGE":
                s=damage_value(enemy[target],1)-.5 if target in enemy else (face*.7 if target==eh else -5)
                if target==eh and ehp<=1 and not opp["hero"].get("immune"): s=100000
            elif hc=="HUNTER": s=1.4+(ehp<15)*1.5 if ehp>2 else 100000
            elif hc=="WARLOCK": s=2.0 if len(hand)<5 and hp>max(8,threat(opp)+5) and you["deck_remaining"] else -20
            elif hc=="PRIEST":
                m=own.get(target,you["hero"] if target==oh else {})
                s=min(2,m.get("max_health",0)-m.get("health",0))*(1.1 if danger else .7)-.1 if m else -20
            elif hc=="ROGUE": s=1 if not you.get("weapon") else -1
            if any(c["cost"]>you["mana"]-you["hero_power"]["cost"] for c in bodies) and s<1000: s-=2
        scored.append((s,a))
    return sorted(scored,key=lambda pair:pair[0],reverse=True)

def decide(state, config=None):
    if state["phase"]=="mulligan": return mulligan(state)
    if state["phase"]=="choice": return choose(state)
    if state["phase"]=="game_over": return None
    return rank_actions(state,config)[0][1]
