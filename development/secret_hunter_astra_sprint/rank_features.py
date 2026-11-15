"""H2 public endpoint features; no opponent identity, source seed or hidden cards."""
from state_features import effective_health,is_beast
from evaluator import minion_value
from race_plan import burst

NAMES=('own_material','enemy_material','own_attack','enemy_attack','own_health','enemy_health',
       'own_hand','enemy_hand','known_followup','known_burn','own_weapon','enemy_shields',
       'enemy_juggler','enemy_aura','enemy_loot','own_juggler','own_hyena','secret_clear',
       'secret_freeze','secret_snake','reply_own_attack','reply_enemy_attack','reply_health','race_distance')

def eligible(s):
    return s['opponent']['hero']['hero_class']=='WARLOCK' and 2<=s['you']['max_mana']<=5

def vector(s,reply):
    y,o=s['you'],s['opponent'];ry,ro=reply['you'],reply['opponent']
    alive=lambda side,cid:sum(m['card_id']==cid and not m.get('silenced') for m in side['board'])
    attack=lambda side:sum(m['attack'] for m in side['board'] if not m.get('frozen'))
    # Knapsack over our known minions only: next-turn deployable material, not a draw prediction.
    mana=max(0,min(10,y['max_mana']+1)-y.get('overload_next_turn',0));dp=[0.]*(mana+1)
    for c in y['hand']:
        cost=c.get('cost',99)
        if c.get('type')!='MINION' or not 0<=cost<=mana:continue
        material=c.get('attack',0)+.6*c.get('health',0)
        for n in range(mana,cost-1,-1):dp[n]=max(dp[n],dp[n-cost]+material)
    secrets={c['card_id'] for c in y.get('secrets',[])};weapon=y.get('weapon') or {}
    burn=burst(s,any(is_beast(m) for m in y['board']))
    return [sum(minion_value(m) for m in y['board'])/10,sum(minion_value(m) for m in o['board'])/10,
        attack(y)/10,attack(o)/10,effective_health(y['hero'])/30,effective_health(o['hero'])/30,
        len(y['hand'])/5,o.get('hand_size',0)/5,max(dp)/10,burn/10,
        weapon.get('attack',0)*weapon.get('durability',0)/6,
        sum(bool(m.get('divine_shield')) for m in o['board'])/3,
        alive(o,'NEW1_019'),alive(o,'EX1_162'),alive(o,'EX1_096'),alive(y,'NEW1_019'),alive(y,'EX1_531'),
        (sum(m['attack'] for m in o['board'] if m['health']<=2 and not m.get('divine_shield'))/10 if 'EX1_610' in secrets else 0),
        float('EX1_611' in secrets),float('EX1_554' in secrets and bool(y['board'])),
        attack(ry)/10,attack(ro)/10,effective_health(ry['hero'])/30,
        max(-2,min(2,(effective_health(o['hero'])-burn-attack(y))/10))]
