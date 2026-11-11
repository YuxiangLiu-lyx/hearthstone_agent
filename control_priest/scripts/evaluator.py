"""Explainable local values; coefficients are hypotheses assessed by paired games."""
from hs_arena.cards import load
CATALOG = load()
BURN = {"CS2_024":3,"CS2_029":6,"EX1_279":10,"DS1_185":2,"EX1_238":3,
        "EX1_241":5,"CS2_008":1,"EX1_308":4,"CS2_061":2,"CS2_094":3,
        "CS1_130":3,"CS2_057":4,"EX1_302":1,"CS2_037":1,"EX1_539":3}
BATTLE_DAMAGE = {"CS2_189":1,"CS2_141":1,"CS2_150":2,"CS2_042":3}
BUFFS = {"CS2_188":(2,0),"EX1_046":(2,0),"EX1_019":(1,1),"CS2_092":(4,4),
         "CS2_087":(3,0),"EX1_195":(0,2),"EX1_623":(0,3),"EX1_194":(2,2),"CS2_004":(0,2),"DS1_070":(2,2)}
AOE = {"CS2_032":(4,False),"CS2_025":(1,False),"CS2_028":(2,False),"CS2_093":(2,False),
       "CS1_112":(2,False),"CS2_062":(3,True)}
REMOVAL = {"CS2_022", "EX1_246", "CS2_076", "EX1_622", "CS2_234", "EX1_309", "CS1_113"}
THREATS = {"NEW1_019":3,"EX1_162":2,"EX1_565":4,"EX1_608":2,"NEW1_012":1.5,
           "EX1_595":3,"EX1_095":3,"EX1_559":5,"CS2_222":4,"EX1_575":3,"EX1_604":3}
DEATH_VALUE = {"EX1_556":2.6,"EX1_534":6,"EX1_110":6,"EX1_383":6,"EX1_096":1.8,"EX1_012":1.8}

def minion_value(m):
    v = 1.25*m.get("attack",0) + .65*m.get("health",0)
    v += 1.8*bool(m.get("divine_shield")) + 1.1*bool(m.get("taunt")) + .5*bool(m.get("stealth"))
    v += .5*m.get("attack",0)*bool(m.get("windfury")) + 2*bool(m.get("poisonous"))
    if not m.get("silenced"):
        v += THREATS.get(m.get("card_id"), 0)
        if m.get("deathrattle"): v += DEATH_VALUE.get(m.get("card_id"),1)
    return v

def hand_body(c):
    m = dict(c)
    mechanics = CATALOG.get(c["card_id"],{}).get("mechanics",[])
    for key in ("taunt","divine_shield","windfury","stealth","deathrattle","poisonous"):
        m[key] = key.upper() in mechanics
    return minion_value(m)

def damage_value(m, damage):
    if m.get("immune"): return 0
    if m.get("divine_shield"): return 1.8 if damage > 0 else 0
    if damage >= m["health"]:
        return minion_value(m) - (DEATH_VALUE.get(m.get("card_id"),1) if m.get("deathrattle") else 0)
    return min(damage,m["health"])*.45

def threat(side):
    return sum(m["attack"]*(2 if m.get("windfury") else 1) for m in side["board"] if not m.get("frozen")) + (side.get("weapon") or {}).get("attack",0)

def board_evaluation(state):
    you,opp=state["you"],state["opponent"]
    hp=lambda s:s["hero"]["health"]+s["hero"].get("armor",0)
    return (sum(map(minion_value,you["board"]))-sum(map(minion_value,opp["board"]))
            +.3*(hp(you)-hp(opp)) + 1.4*(len(you["hand"])-opp["hand_size"])
            -2*max(0,threat(opp)-hp(you)+4))
