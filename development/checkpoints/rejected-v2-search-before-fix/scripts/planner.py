"""Bounded, conservative current-turn search over an explicitly supported public model.

No live engine, opponent hand, deck identities, seed, or RNG access. Unknown effects cause
search abstention. Plans are re-evaluated from the next real observation, never blindly replayed.
Existing Windfury units get only one remaining attack (a safe underestimate).
"""
import copy
import time
from actions import expand, legal
from evaluator import CATALOG, minion_value

DIRECT={"CS2_024":3,"CS2_029":6,"EX1_279":10,"DS1_185":2,"CS2_008":1,"EX1_238":3,"EX1_241":5}
BUFF={"CS2_092":(4,4),"CS2_087":(3,0),"EX1_019":(1,1),"CS2_188":(2,0),"EX1_046":(2,0)}
AREA={"CS2_032":4,"CS2_025":1,"CS2_028":2,"CS2_093":2}
BATTLE={"CS2_189":1,"CS2_141":1,"CS2_150":2,"CS2_042":3}
CHARGE={"CS2_171","CS2_173","CS2_124","CS2_131","CS2_213","EX1_067","NEW1_011","EX1_543"}
SAFE={"CS2_182","CS2_200","CS2_179","EX1_008","NEW1_023","EX1_608","NEW1_012","CS2_033",
      "EX1_556","EX1_534","EX1_110","EX1_096","EX1_012","EX1_028","EX1_066","CS2_120",
      "CS2_172","CS2_065","EX1_319","EX1_362","EX1_382","CS2_151","CS2_196","CS2_088",
      "CS2_147","EX1_015","CS2_117","EX1_032","CS2_125","CS1_069","CS2_142","CS2_197",
      "CS2_155","EX1_563","EX1_010","EX1_029","CS2_231","CS2_168","CS1_042",
      "CS2_226","CS2_186","CS2_181","EX1_195","EX1_623","EX1_020","CS2_127",
      "skele21","EX1_534t","EX1_110t","CS2_152","CS2_101t","CS2_tk1","CS2_050",
      "NEW1_032","NEW1_034","CS2_022t","hexfrog"} | CHARGE | set(BUFF) | set(BATTLE)
DEATH_TOKENS={"EX1_556":[("skele21",2,1)],"EX1_534":[("EX1_534t",2,2)]*2,"EX1_110":[("EX1_110t",4,5)]}
# Public spells whose lingering enchantments are not fully represented by state flags.
UNSUPPORTED_HISTORY={"EX1_363","CS2_038","CS2_103","NEW1_036","CS2_084","EX1_619","EX1_549"}


def supported(state):
    y,o=state["you"],state["opponent"]
    if o.get("secrets_count") or y.get("secrets") or y["hero"].get("immune") or o["hero"].get("immune"):
        return False
    if y["hero"].get("card_id") not in {"HERO_0"+str(i) for i in range(1,10)}: return False
    for side in (y,o):
        if any(c["card_id"] in UNSUPPORTED_HISTORY for c in side.get("graveyard",[])): return False
        for m in side["board"]:
            if not m.get("silenced") and m["card_id"] not in SAFE: return False
            if m.get("deathrattle") and m["card_id"] not in set(DEATH_TOKENS)|{"EX1_029","EX1_096","EX1_012"}: return False
    # Weapons with deathrattles / attack triggers are outside the model.
    if y.get("weapon") and y["weapon"]["card_id"] not in {"CS2_106","CS2_112","CS2_091","EX1_536","CS2_082"}: return False
    return True


def prepare(state):
    s=copy.deepcopy(state)
    for side in (s["you"],s["opponent"]):
        for m in side["board"]: m["remaining_attacks"]=int(m.get("can_attack",False))
    s["you"]["hero"]["remaining_attacks"]=int(s["you"]["hero"].get("can_attack",False))
    s["synthetic_id"]=-1
    return s


def damage(m, amount, poison=False):
    if amount<=0 or m.get("immune"): return
    if m.get("divine_shield"):
        m["divine_shield"]=False
        return
    armor=m.get("armor",0)
    absorbed=min(armor,amount)
    if "armor" in m: m["armor"]-=absorbed
    m["health"]-=amount-absorbed
    if poison and "hero_class" not in m: m["health"]=0


def cleanup(s):
    for side,other in ((s["you"],s["opponent"]),(s["opponent"],s["you"])):
        dead=[m for m in side["board"] if m["health"]<=0]
        for m in dead:
            pos=side["board"].index(m); side["board"].remove(m)
            if m.get("deathrattle"):
                cid=m["card_id"]
                if cid=="EX1_029": damage(other["hero"],2)
                # Drawing is not simulated. Stop a line with an unknown draw instead of fabricating it.
                if cid in ("EX1_096","EX1_012"): return False
                for card_id,atk,hp in DEATH_TOKENS.get(cid,[]):
                    if len(side["board"])>=7: break
                    token={"entity_id":s["synthetic_id"],"card_id":card_id,"attack":atk,"health":hp,
                           "max_health":hp,"remaining_attacks":0,"can_attack":False}
                    s["synthetic_id"]-=1; side["board"].insert(pos,token);pos+=1
            if side is s["you"] and m["card_id"]=="EX1_608" and not m.get("silenced"):
                # Reject discount removal: costs clamped at zero cannot always be inverted from observation.
                return False
    return True


def spell_target(m):
    return not m.get("stealth") and (m.get("silenced") or m.get("card_id")!="NEW1_023")


def options(s):
    y,o=s["you"],s["opponent"]; eh=o["hero"]["entity_id"]
    visible=[m for m in o["board"] if not m.get("stealth")]
    taunts=[m["entity_id"] for m in visible if m.get("taunt")]
    attack_targets=taunts or [eh]+[m["entity_id"] for m in visible]
    for m in y["board"]+[y["hero"]]:
        if m.get("remaining_attacks",0) and m["attack"]>0 and not m.get("frozen"):
            for t in attack_targets: yield {"type":"attack","attacker":m["entity_id"],"target":t}
    power=y.get("hero_power") or {}
    if power.get("usable") and power["cost"]<=y["mana"]:
        if y["hero"]["hero_class"]=="MAGE":
            for t in [eh]+[m["entity_id"] for m in o["board"] if spell_target(m)]: yield {"type":"hero_power","target":t}
        elif y["hero"]["hero_class"]=="HUNTER": yield {"type":"hero_power"}
    for c in y["hand"]:
        cid=c["card_id"]
        if c["cost"]>y["mana"]: continue
        a={"type":"play_card","card":c["entity_id"]}
        if c["type"]=="MINION" and len(y["board"])>=7: continue
        if cid in DIRECT:
            for t in [eh]+[m["entity_id"] for m in o["board"] if spell_target(m)]: yield {**a,"target":t}
        elif cid in BATTLE:
            for t in [eh]+[m["entity_id"] for m in visible]: yield {**a,"target":t,"position":len(y["board"])}
        elif cid in BUFF:
            for m in y["board"]:
                if c["type"]=="MINION" or spell_target({**m,"stealth":False}):
                    yield {**a,"target":m["entity_id"],**({"position":len(y["board"])} if c["type"]=="MINION" else {})}
        elif cid in CHARGE|{"EX1_608","NEW1_012","CS2_142"}:
            yield {**a,"position":len(y["board"])}
        elif cid in AREA or cid=="GAME_005": yield a
        elif cid in ("CS2_022","EX1_246"):
            for m in o["board"]:
                if spell_target(m): yield {**a,"target":m["entity_id"]}


def transition(state, a):
    s=copy.deepcopy(state); y,o=s["you"],s["opponent"]
    entities={m["entity_id"]:m for side in (y,o) for m in side["board"]+[side["hero"]]}
    target=entities.get(a.get("target"))
    sd=sum(m.get("spell_damage",0) for m in y["board"])
    if a["type"]=="attack":
        at=entities[a["attacker"]]; attack=at["attack"]; retaliation=target["attack"]
        ashield=at.get("divine_shield"); tshield=target.get("divine_shield")
        damage(target,attack,at.get("poisonous",False))
        damage(at,retaliation,target.get("poisonous",False))
        at["remaining_attacks"]-=1;at["can_attack"]=at["remaining_attacks"]>0
        if at.get("card_id")=="CS2_033" and not at.get("silenced") and attack and not tshield: target["frozen"]=True
        if target.get("card_id")=="CS2_033" and not target.get("silenced") and retaliation and not ashield: at["frozen"]=True
    elif a["type"]=="hero_power":
        y["mana"]-=y["hero_power"]["cost"];y["hero_power"]["usable"]=False
        damage(target if target else o["hero"],1 if target else 2)
    else:
        c=next(c for c in y["hand"] if c["entity_id"]==a["card"])
        y["hand"].remove(c);y["mana"]-=c["cost"];cid=c["card_id"]
        if c["type"]=="MINION":
            mechanics=CATALOG.get(cid,{}).get("mechanics",[])
            m={**c,"max_health":c["health"],"remaining_attacks":int(cid in CHARGE),"can_attack":cid in CHARGE,
               "spell_damage":CATALOG.get(cid,{}).get("spell_damage",0)}
            if cid=="CS2_142":m["spell_damage"]=1
            for k in ("taunt","divine_shield","windfury","charge","poisonous","deathrattle"):
                m[k]=k.upper() in mechanics
            y["board"].insert(a.get("position",len(y["board"])),m)
            if cid=="EX1_608":
                for d in y["hand"]:
                    if d["type"]=="SPELL":d["cost"]=max(0,d["cost"]-1)
        if cid in DIRECT: damage(target,DIRECT[cid]+sd)
        if cid=="CS2_024":target["frozen"]=True
        if cid in BATTLE: damage(target,BATTLE[cid])
        if cid in BUFF:
            da,dh=BUFF[cid];target["attack"]+=da;target["health"]+=dh;target["max_health"]+=dh
        if cid in AREA:
            for m in o["board"]:
                damage(m,AREA[cid]+sd)
                if cid=="CS2_028":m["frozen"]=True
            if cid=="CS2_093":damage(o["hero"],2+sd)
        if cid=="GAME_005":y["mana"]+=1
        if cid in ("CS2_022","EX1_246"):
            eid=target["entity_id"];target.clear();target.update(entity_id=eid,card_id="CS2_022t" if cid=="CS2_022" else "hexfrog",
                attack=1 if cid=="CS2_022" else 0,health=1,max_health=1,taunt=cid=="EX1_246",remaining_attacks=0)
        if c["type"]=="SPELL":
            for m in y["board"]:
                if m["card_id"]=="NEW1_012" and not m.get("silenced"):m["attack"]+=1
    if not cleanup(s):return None
    return s


def lethal_plan(state, budget_s=.035, max_nodes=700):
    if state.get("phase")!="main" or not supported(state):return None
    y,o=state["you"],state["opponent"]
    # A cheap overestimate only prunes impossible lines; never declares a win.
    upper=sum(m["attack"] for m in y["board"] if m.get("can_attack"))+y["hero"].get("attack",0)+2
    upper+=sum(DIRECT.get(c["card_id"],0)+c.get("attack",0)+8*(c["card_id"] in BUFF) for c in y["hand"])
    upper+=len(y["hand"])*sum(m.get("spell_damage",0)+int(m["card_id"]=="NEW1_012") for m in y["board"])
    if upper<o["hero"]["health"]+o["hero"].get("armor",0):return None
    deadline=time.monotonic()+min(.5,max(0,budget_s)); count=0; seen=set()
    def dfs(s,path):
        nonlocal count
        count+=1
        if s["you"]["hero"]["health"]<=0:return None
        if s["opponent"]["hero"]["health"]<=0:return path
        if count>max_nodes or len(path)>=10 or time.monotonic()>deadline:return None
        key=(s["you"]["mana"],s["opponent"]["hero"]["health"],s["opponent"]["hero"].get("armor",0),
             s["you"]["hero"]["health"],s["you"]["hero"].get("remaining_attacks",0),
             (s["you"].get("hero_power") or {}).get("usable"),
             tuple((c["entity_id"],c["cost"]) for c in s["you"]["hand"]),
             tuple((m["entity_id"],m["attack"],m["health"],m.get("divine_shield"),m.get("frozen"),m.get("remaining_attacks",0),m.get("card_id"))
                   for side in (s["you"],s["opponent"]) for m in side["board"]))
        if key in seen:return None
        seen.add(key)
        actions=list(options(s))
        if not path:actions=[a for a in actions if legal(state,a)]
        eh=s["opponent"]["hero"]["entity_id"]
        actions.sort(key=lambda a:(a.get("target")!=eh,a["type"]!="attack"))
        for a in actions:
            nxt=transition(s,a)
            if nxt is not None:
                result=dfs(nxt,path+[a])
                if result:return result
            if count>max_nodes or time.monotonic()>deadline:break
        return None
    return dfs(prepare(state),[])
