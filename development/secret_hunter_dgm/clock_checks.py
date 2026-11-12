"""Check Krush hand-clock conditions, including slots, taunts and frozen hero."""
import sys,json,copy
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_dgm.accounting import reserve,finish
reserve('krush-clock-checks',short=30)
sys.path.insert(0,str(ROOT/'development/secret_hunter_dgm/candidates/B1/scripts'))
from race_plan import hand_damage,burst
rows=[]
def check(name,actual,expected):
 rows.append({'name':name,'actual':actual,'expected':expected});assert actual==expected,(name,actual,expected)
check('Krush affordable',hand_damage((('EX1_543',9,True),),9,False,1),8)
check('Krush too expensive',hand_damage((('EX1_543',9,True),),8,False,1),2)
check('Krush full board',hand_damage((('EX1_543',9,True),),10,False,0),2)
check('Krush blocked Taunt',hand_damage((('EX1_543',9,True),),10,False,1,False),2)
check('No undrawn Krush',hand_damage((),10,False,1),2)
check('Affordable discounted charge and kill',hand_damage((('EX1_543',6,True),('EX1_539',3,False)),9,False,1),13)
check('Only one slot cannot summon twice',hand_damage((('EX1_531',2,True),('EX1_543',6,True),('EX1_539',3,False)),9,False,1),13)
check('Spell bypasses Taunt',hand_damage((('EX1_543',6,True),('EX1_539',3,False)),9,False,1,False),5)
write(ROOT/'docs/secret_hunter_dgm/clock-checks.json',rows);finish('krush-clock-checks',actual_short=len(rows));print('passed',len(rows))
