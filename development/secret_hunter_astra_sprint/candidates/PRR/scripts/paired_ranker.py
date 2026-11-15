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

COEFFICIENTS = [-1.3316736579909787, 1.2885618328507238, -0.7805813770003012, 0.5293909187335782, 0.026474670237677935, 0.12780419145710328, 0.24856351672076493, -0.0813907975778356, -0.3338076590038179, -0.20384010378497613, -0.0972254637693905, 0.015585850045674077, 0.47498086730267364, 0.1772874202559695, 0.4069539878891773, -0.3661688065127218, 0.4428938266629453, -0.8171648253667029, 0.0801774787413138, 0.13157551828954608, -0.9450273602481001, 0.8503670116998817, -0.3377639974985757, 1.331799747802977]

def correction(state,reply):
    if not eligible(state):return 0.
    return max(-4.,min(4.,sum(a*b for a,b in zip(vector(state,reply),COEFFICIENTS))))
