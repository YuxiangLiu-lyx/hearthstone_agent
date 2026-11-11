"""Within-game continuation cache guarded by complete supported-state fingerprints."""
import hashlib,json,time
import tactical_model as model
from action_validator import legal


def fingerprint(s):
    # Include projected flags omitted by the older lethal dedup key, plus secret order.
    fields={'turn':s.get('turn'),'model':model.signature(s)}
    fields['extras']={k:{'board':[(m['entity_id'],m.get('taunt'),m.get('poisonous'),m.get('silenced'),m.get('immune'),m.get('deathrattle'),m.get('spell_damage',0)) for m in s[k]['board']],
        'secrets':[c['card_id'] for c in s[k].get('secrets',[])],'secrets_count':s[k].get('secrets_count'),
        'weapon':s[k].get('weapon')} for k in ('you','opponent')}
    return hashlib.sha256(json.dumps(fields,sort_keys=True,default=str).encode()).hexdigest()


def take(state,config,memory):
    identity=(state.get('game_id'),state.get('turn'))
    if tuple(memory.get('identity',[]))!=identity or memory.get('config')!=config:
        memory.clear();return None
    steps=memory.get('steps',[])
    if not steps or not model.supported(state):memory.clear();return None
    step=steps[0]
    if fingerprint(model.prepare(state))!=step['expected'] or not legal(state,step['action']):memory.clear();return None
    memory['steps']=steps[1:]
    return step['action']


def save(state,config,sequence,memory,deadline):
    memory.clear()
    if len(sequence)<2:return
    current=model.prepare(state);steps=[]
    for n,a in enumerate(sequence):
        if time.monotonic()>=deadline:break
        if n:steps.append({'expected':fingerprint(current),'action':a})
        current=model.transition(current,a)
        if current is None:break
    memory.update(identity=[state.get('game_id'),state.get('turn')],config=config,steps=steps)
