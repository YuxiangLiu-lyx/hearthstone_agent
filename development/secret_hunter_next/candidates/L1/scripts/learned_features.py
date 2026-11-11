"""Small public endpoint features for offline preference learning."""
NAMES=['health_reserve','enemy_health','own_material','enemy_material','own_engines','enemy_generators','hand','secrets','beasts','enemy_taunts']
def features(s):
 y,o=s['you'],s['opponent']
 def material(side):return sum(x['attack']+.6*x['health']+int(x.get('divine_shield',False)) for x in side['board'])
 return [(y['hero']['health']-sum(x['attack'] for x in o['board']))/15,o['hero']['health']/30,material(y)/15,material(o)/15,sum(x['card_id'] in ('NEW1_019','EX1_531') and not x.get('silenced') for x in y['board']),sum(x['card_id'] in ('NEW1_019','EX1_597','EX1_162') and not x.get('silenced') for x in o['board']),len(y['hand'])/5,len(y.get('secrets',[]))/2,sum(x['card_id'] in ('EX1_531','EX1_538t','EX1_554t','EX1_534','EX1_534t','NEW1_032','NEW1_033','NEW1_034','EX1_162') for x in y['board'])/4,sum(bool(x.get('taunt')) for x in o['board'])/3]
